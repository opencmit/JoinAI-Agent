import traceback
import uuid
from datetime import datetime
from typing import Dict, Optional, Any, Union
from copilotkit.langchain import copilotkit_emit_state

from dotenv import load_dotenv

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated
from langgraph_agent.graph.state import AgentState
from langgraph_agent.tools.sandbox.manager import sbx_manager
from langgraph_agent.utils.message_utils import get_last_show_message_id
from e2b.sandbox.commands.command_handle import CommandResult, CommandExitException
from e2b.sandbox_async.commands.command_handle import AsyncCommandHandle
import asyncio
from cachetools import TTLCache
import time


# 全局后台任务缓存，使用 (sandbox_id, pid) -> task_info 的结构，支持时间过期
# 缓存条目将在最后一次写入后 60 分钟过期
background_tasks_cache = TTLCache(maxsize=1000, ttl=3600)


class ShellCommandInput(BaseModel):
    command: str = Field(description="要执行的shell命令")
    folder: Optional[str] = Field(default=None, description="命令执行的目录路径，相对于workspace_path")
    background: bool = Field(default=False, description="是否在后台执行命令")
    timeout: int = Field(default=60, description="命令执行超时时间(秒)，前台任务超时时间不能超过60秒，后台任务超时时间不能小于900秒")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="命令执行状态，将由系统提供")


class BackgroundTaskQueryInput(BaseModel):
    pid: int = Field(description="后台任务的进程ID")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="命令执行状态，将由系统提供")


def _build_command_output(
    result: Union[CommandResult, AsyncCommandHandle],
    # folder: Optional[str] = None,
) -> str:
    """构建统一的类似shell的命令输出字符串"""
    output_str = ""
    # if folder:
    #     output_str += f"Directory: {folder}\n"

    # 获取通用属性
    print("获取结果中")
    stdout = result.stdout
    stderr = result.stderr
    exit_code = result.exit_code
    # error = getattr(result, 'error', None)
    error = result.error

    # 判断任务状态
    if exit_code is not None:
        # 任务已完成
        if exit_code == 0:
            output_str += f"Status: Success (Exit Code: {exit_code})"
        else:
            output_str += f"Status: Failed (Exit Code: {exit_code})"
    else:
        # 任务仍在运行（只有AsyncCommandHandle会有这种情况）
        # pid = getattr(result, 'pid', None)
        pid = result.pid
        output_str += f"Status: Running (PID: {pid})"

    # 添加输出内容
    if stdout:
        if exit_code is None:
            output_str += f"\n--- Standard Output (Current) ---\n{stdout}"
        else:
            output_str += f"\n--- Standard Output ---\n{stdout}"

    if stderr:
        if exit_code is None:
            output_str += f"\n--- Standard Error (Current) ---\n{stderr}"
        else:
            output_str += f"\n--- Standard Error ---\n{stderr}"

    if error:
        output_str += f"\n--- Error Message ---\n{error}"

    return output_str


@tool("execute_command", args_schema=ShellCommandInput, return_direct=False)
async def execute_command(command: str, folder: Optional[str] = None, background: bool = False, timeout: int = 60, state: AgentState = None, special_config_param: RunnableConfig = None) -> tuple[Dict, str]:
    """在沙箱环境中执行shell命令。如果是后台执行，会等待10秒后返回当前输出。前台任务超时时间不能超过60秒，后台任务超时时间不能小于900秒"""
    config = special_config_param or RunnableConfig()
    state["logs"] = state["logs"] or []

    # 添加命令执行日志
    log_index = len(state["logs"])
    state["logs"].append({
        "message": f"🖥️ 执行命令: '{command}'" + (" (后台)" if background else " (前台)"),
        "done": False,
        "messageId":  get_last_show_message_id(state["messages"])
    })
    await copilotkit_emit_state(config, state)

    try:
        # 添加超时校验逻辑
        adjustment_msg = None
        if not background:
            if timeout > 60:
                error_msg = f"错误: 前台任务的超时时间({timeout}秒)不能超过60秒。"
                state["logs"][log_index]["message"] += f" - ❌ {error_msg}"
                state["logs"][log_index]["done"] = True
                await copilotkit_emit_state(config, state)
                return state, error_msg
        else: # background == True
            if timeout < 900:
                original_timeout = timeout
                timeout = 900  # 自动设置为15分钟
                adjustment_msg = f"后台任务的超时时间({original_timeout}秒)少于15分钟，已自动调整为15分钟({timeout}秒)。"
                state["logs"][log_index]["message"] += f" - ⚠️ {adjustment_msg}"
                await copilotkit_emit_state(config, state)


        # 获取sandbox实例
        state, sandbox = await sbx_manager.get_sandbox_async(state)
        sandbox_id = state.get("e2b_sandbox_id", "unknown")

        # 执行命令
        try:
            if not background:
                # 前台执行，直接等待结果
                result = await sandbox.commands.run(command, background=False, cwd=folder, timeout=timeout)
                output_str = _build_command_output(result)

            else:
                # 后台执行，返回AsyncCommandHandle
                handle = await sandbox.commands.run(command, background=True, cwd=folder, timeout=timeout)
                print("后台执行命令执行中")

                # 缓存后台任务信息到 TTLCache，键为 (sandbox_id, pid)
                background_tasks_cache[(sandbox_id, handle.pid)] = {
                    "handle": handle,
                    "command": command,
                    "folder": folder,
                    "start_time": datetime.now(),
                }

                # 等待10秒，然后返回当前输出
                await asyncio.sleep(10)

                # 构建后台任务输出
                output_str = _build_command_output(handle)

                # 如果有调整信息，添加到输出字符串
                if adjustment_msg:
                    output_str += f"\n--- 注意 ---\n{adjustment_msg}"

        except CommandExitException as e:
            result = CommandResult(
                exit_code=e.exit_code,
                stdout=e.stdout,
                stderr=e.stderr,
                error=e.error
            )
            output_str = _build_command_output(result)
            # 如果是后台任务且有调整信息，添加到输出字符串 (异常情况下也需要告知)
            if background and adjustment_msg:
                 output_str += f"\n--- 注意 ---\n{adjustment_msg}"


        # 更新命令执行状态
        state["logs"][log_index]["done"] = True
        await copilotkit_emit_state(config, state)
        return state, output_str

    except Exception as e:
        state["logs"][log_index]["done"] = True
        await copilotkit_emit_state(config, state)
        error_msg = f"命令执行出错: {str(e)}"
        # 如果是后台任务且有调整信息，添加到错误信息中
        if background and adjustment_msg:
             error_msg += f"\n--- 注意 ---\n{adjustment_msg}"
        print(traceback.format_exc())
        return state, error_msg


@tool("get_background_task_output", args_schema=BackgroundTaskQueryInput, return_direct=False)
async def get_background_task_output(pid: int, state: AgentState = None, special_config_param: RunnableConfig = None) -> tuple[Dict, str]:
    """获取后台任务的当前输出和状态。"""
    config = special_config_param or RunnableConfig()
    state["logs"] = state["logs"] or []

    # 从state获取sandbox_id
    sandbox_id = state.get("e2b_sandbox_id", "unknown")

    # 添加查询日志
    log_index = len(state["logs"])
    state["logs"].append({
        "message": f"🔍 查询后台任务: PID {pid}",
        "done": False,
        "messageId":  get_last_show_message_id(state["messages"])
    })
    await copilotkit_emit_state(config, state)

    try:
        # 检查任务是否存在，使用 (sandbox_id, pid) 作为键
        task_key = (sandbox_id, pid)
        if task_key not in background_tasks_cache:
            output_str = f"错误: 未找到PID为 {pid} 的后台任务"
            state["logs"][log_index]["done"] = True
            await copilotkit_emit_state(config, state)
            return state, output_str

        # 从 TTLCache 获取任务信息
        task_info = background_tasks_cache[task_key]
        handle: AsyncCommandHandle = task_info["handle"]

        # 总是使用当前的handle构建输出，忽略任务完成状态
        output_str = _build_command_output(handle)

        state["logs"][log_index]["done"] = True
        await copilotkit_emit_state(config, state)
        return state, output_str

    except Exception as e:
        state["logs"][log_index]["done"] = True
        await copilotkit_emit_state(config, state)
        error_msg = f"查询后台任务出错: {str(e)}"
        print(traceback.format_exc())
        return state, error_msg


async def test_shell_tool():
    """测试shell命令执行工具"""
    print("开始测试沙箱shell命令执行工具...")
    import traceback
    from langgraph_agent.graph.state import create_initial_state

    # 创建一个初始状态
    state = AgentState(
        copilotkit={
            "actions": []
        },
        messages=[],
        logs=[],  # 初始化 logs 为一个空列表
        e2b_sandbox_id="test_sandbox_123"  # 提供一个测试sandbox ID
    )
    state = create_initial_state(state)

    try:
        # 测试执行简单命令
        print("\n1. 测试执行简单命令 - ls:")
        ls_result = await execute_command.ainvoke(
            {
                "command": "ls -la",
                "state": state
            }
        )
        print(f"结果: {ls_result}")

        # 测试后台执行长时间命令
        print("\n2. 测试后台执行长时间命令:")
        bg_result = await execute_command.ainvoke(
            {
                "command": "echo 'hello world' && sleep 10",
                "background": True,
                "state": state
            }
        )
        print(f"后台任务结果: {bg_result}")

        # 从结果中提取PID
        result_str = bg_result[1]
        pid = None
        for line in result_str.split('\n'):
            if line.startswith('Status: Running (PID:'):
                pid_str = line.split('PID: ')[1].rstrip(')')
                pid = int(pid_str)
                break

        if pid:
            # 测试查询后台任务
            print(f"\n3. 测试查询后台任务 PID {pid}:")
            await asyncio.sleep(2)  # 等待2秒
            query_result = await get_background_task_output.ainvoke(
                {
                    "pid": pid,
                    "state": bg_result[0]
                }
            )
            print(f"查询结果: {query_result}")

        print("\n测试完成: shell命令执行工具测试成功!")

    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        traceback.print_exc()

    # 打印最终状态
    print("\n最终状态:")
    if hasattr(state, 'logs') and state.logs:
        for i, log in enumerate(state.logs):
            print(f"Log {i+1}: {log['message']} - 完成状态: {log['done']}")
    else:
        print("没有日志记录")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_shell_tool())
