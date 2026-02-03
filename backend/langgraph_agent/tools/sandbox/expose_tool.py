import traceback
from copilotkit.langchain import copilotkit_emit_state

from pydantic import BaseModel, Field
from typing import Optional, Tuple
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from typing_extensions import Annotated
from langgraph_agent.graph.state import AgentState
from langgraph_agent.tools.sandbox.manager import sbx_manager
from langgraph_agent.utils.message_utils import get_last_show_message_id

class ExposePortInput(BaseModel):
    port: int = Field(description="要暴露的端口号，范围为1-65535")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")
    special_config_param: Annotated[RunnableConfig, InjectedToolArg] = Field(description="特殊配置参数，由系统提供")

class SandboxExposeTool:
    """沙箱端口暴露工具类"""
    
    def __init__(self):
        """初始化沙箱端口暴露工具"""
        pass
    
    @staticmethod
    async def _add_log(state: AgentState, message: str, config: RunnableConfig) -> int:
        """添加日志并返回日志索引"""
        state["logs"] = state.get("logs", [])
        log_index = len(state["logs"])
        state["logs"].append({
            "message": message,
            "done": False,
            "messageId":  get_last_show_message_id(state["messages"])
        })
        await copilotkit_emit_state(config, state)
        return log_index
    
    @staticmethod
    async def _complete_log(state: AgentState, log_index: int, config: RunnableConfig):
        """完成日志"""
        state["logs"][log_index]["done"] = True
        await copilotkit_emit_state(config, state)
    
    @staticmethod
    async def _get_sandbox(state: AgentState):
        """获取沙箱实例"""
        return await sbx_manager.get_sandbox_async(state)
    
    @staticmethod
    async def expose_port(port: int, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """暴露指定端口"""
        log_index = await SandboxExposeTool._add_log(state, f"🌐 暴露端口: {port}", config)
        
        try:
            state, sandbox = await SandboxExposeTool._get_sandbox(state)          
            # 模拟端口暴露功能，实际上不会真正暴露端口
            from langgraph_agent.config import global_config
            base_url = global_config.SANDBOX_DOMAIN
            from urllib.parse import urlparse, urlunparse
            # 解析基础URL
            parsed_url = urlparse(base_url)
            # 替换端口号
            exposed_url = urlunparse((
                parsed_url.scheme,
                f"{parsed_url.hostname}:{port}",
                "",
                "",
                "",
                ""
            ))
            # exposed_url = f"http://localhost:{port}"
            # exposed_url = f"{base_url}:{port}"
            
            # 将暴露的URL写入structure_tool_results
            toolcall_id = config.get("configurable", {}).get("tool_call_id")
            if toolcall_id:
                state.setdefault('structure_tool_results', {})
                # 存储格式参考web_search_tool，使用URL作为键
                state['structure_tool_results'][toolcall_id] = {
                    "expose_port_info": {
                        "exposed_url": exposed_url,
                        "description": f"沙箱端口 {port} 暴露的预览地址"
                    }
                }

            await SandboxExposeTool._complete_log(state, log_index, config)
            return state, f"端口 {port} 已成功暴露。用户现在可以通过 {exposed_url} 访问此服务。"
                
        except Exception as e:
            await SandboxExposeTool._complete_log(state, log_index, config)
            traceback.print_exc()
            # 即使出错也返回当前 state，并在 tool_msg 中包含错误信息
            return state, f"暴露端口 {port} 失败: {str(e)}"
    
    @staticmethod
    @tool("expose_port", args_schema=ExposePortInput)
    async def expose_port_tool(
        port: int,
        special_config_param: RunnableConfig,
        state: Optional[AgentState] = None,
    ) -> Tuple[AgentState, str]:
        """
        暴露沙箱环境中的端口到公共互联网，并获取其预览URL。
        这对于使沙箱中运行的服务（如Web应用程序、API或其他网络服务）能够被用户访问至关重要。
        暴露的URL可以与用户共享，使他们能够与沙箱环境交互。
        """
        config = special_config_param or RunnableConfig()
        
        if not isinstance(port, int) or not (1 <= port <= 65535):
            return state, f"无效的端口号: {port}。端口号必须是1到65535之间的整数。"
        
        return await SandboxExposeTool.expose_port(port, state, config)

expose_port_tool = SandboxExposeTool.expose_port_tool

async def test_expose_tool():
    """测试端口暴露工具"""
    print("开始测试沙箱端口暴露工具...")
    import traceback
    from langgraph_agent.state import create_initial_state
    
    # 创建一个初始状态
    state = create_initial_state()
    
    try:
        # 测试端口暴露工具
        print("\n1. 测试暴露端口8000:")
        expose_result = await SandboxExposeTool.expose_port_tool.ainvoke(
            {
                "port": 8000, 
                "state": state
            }
        )
        print(f"结果: {expose_result}")
        
        # 测试无效端口号
        print("\n2. 测试无效端口号:")
        invalid_port_result = await SandboxExposeTool.expose_port_tool.ainvoke(
            {
                "port": 70000,  # 超出范围的端口号
                "state": state
            }
        )
        print(f"结果: {invalid_port_result}")
        
        print("\n测试完成: 端口暴露工具测试完成!")
        
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
    asyncio.run(test_expose_tool())
