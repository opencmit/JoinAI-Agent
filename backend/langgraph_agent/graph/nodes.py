"""
图的各个节点、以及节点之间的路由函数
"""

import os
from copy import deepcopy
from typing import Dict, Any, Optional, List, Literal
import traceback
import json
import datetime
import time
import sys
import platform
import re
import asyncio
import logging
import requests
import json_repair

from langchain_openai import ChatOpenAI
from langchain.tools.base import BaseTool
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langgraph.errors import GraphInterrupt
from contextlib import ExitStack
from copilotkit.langgraph import copilotkit_emit_state
from langgraph.types import Command
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

from langgraph_agent.utils.convert_md import convert_to_markdown_unified

from langgraph_agent.graph.state import AgentState
from langgraph_agent.utils.tool_utils import normalize_mcp_tool_data, normalize_tool_result
from langgraph_agent.utils.tool_utils import fix_markdown_display, process_raw_html_content
from langgraph_agent.utils.json_utils import sanitize_string_for_json, deep_clean_for_json, safe_json_dumps, validate_tool_calls_json, repair_json_output
from langgraph_agent.utils.message_utils import get_last_show_message_id
from langgraph_agent.graph.llm import get_llm_client, safe_llm_invoke, get_error_msg
from langgraph_agent.constant import TEAM_MEMBERS, RESPONSE_FORMAT
from langgraph_agent.graph.a2a_agent import get_a2a_agents_from_state


from typing import Dict, Any, Optional, List, Literal

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda


from langgraph_agent.graph.state import AgentState
from langgraph_agent.utils.tool_utils import normalize_mcp_tool_data
from langgraph_agent.utils.tool_utils import get_attachment_tools
from langgraph_agent.utils.json_utils import sanitize_string_for_json, deep_clean_for_json
from langgraph_agent.graph.mcp_tool import create_mcp_converter_with_llm
from langgraph_agent.config import global_config


logger = logging.getLogger(__name__)

async def agent_node(
        state: AgentState,
        config: RunnableConfig,
        llm: Optional[ChatOpenAI],
        prompt: str,
        cur_node: str
) -> Dict:
    """Agent 节点 - 修复JSON格式错误版本，增强工具使用示例"""
    if llm is None:
        raise ValueError("LLM is not initialized for agent_node")
        
    # logger.info("Agent Node Messages:\n{}".format(state["messages"]))

    print(f"\n=== Agent Node 消息调试 (JSON格式错误修复版本) ===")
    print(f"状态中的消息数量: {len(state['messages'])}")

    # 记录LLM配置信息
    print(f"\n=== LLM 配置信息 ===")
    print(f"LLM 类型: {type(llm).__name__}")
    print(f"模型名称: {getattr(llm, 'model_name', 'unknown')}")
    print(f"Base URL: {getattr(llm, 'openai_api_base', 'unknown')}")
    print(f"超时设置: {getattr(llm, 'request_timeout', 'unknown')}")
    print(f"最大重试次数: {getattr(llm, 'max_retries', 'unknown')}")

    # 获取用户的最新查询内容并清理
    user_query = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, 'type') and msg.type == "human":
            user_query = msg.content
            break

    print(f"用户最新查询（原始）: {user_query}")
    

    # 使用deepcopy，不影响state.messages
    llm_messages = deepcopy(state["messages"])
    # print("llm_messages:{}".format(llm_messages))

    if state.get("sub_task"):
        logger.info(f"user_query改为使用子任务: {state.get('sub_task')}")
        user_query = state.get("sub_task")

    llm_messages.append(HumanMessage(content=user_query))
    
    

    # 创建系统消息 - 清理系统prompt
    # try:
    #     system_prompt = sanitize_string_for_json(prompt, context="api")
    #     system_message = SystemMessage(content=system_prompt)
    # except Exception as e:
    #     print(f"⚠️ 系统prompt创建失败: {str(e)}")
    #     # 使用简化的系统消息
    #     simple_system_prompt = "你是一个有用的AI助手。"
    #     system_message = SystemMessage(content=simple_system_prompt)
    #
    # llm_messages.insert(0, system_message)

    # 改进的循环检测逻辑
    iteration_count = state.get("iteration_count", 0)

    # 检查是否达到最大迭代次数
    max_iterations = state.get("max_iterations", 50)
    if iteration_count >= max_iterations:
        print(f"达到最大迭代次数 {max_iterations}，强制结束")
        state['completed'] = True
        # 添加结束消息
        final_message = AIMessage(content="对话已达到最大迭代次数，自动结束。如需继续，请开始新的对话。", name=cur_node)
        state["messages"].append(final_message)
        return {
            "completed": True,
            "messages": [final_message]
        }

    # 检查最近的AI消息是否重复
    recent_ai_messages = [msg for msg in state["messages"][-10:] if
                          hasattr(msg, 'type') and msg.type == "ai" and msg.content.strip()]
    if len(recent_ai_messages) >= 3:
        # 检查最近3条AI消息的内容相似度
        last_three_contents = [msg.content.strip() for msg in recent_ai_messages[-3:]]

        # 简单的重复检测：如果最后两条消息完全相同
        if len(set(last_three_contents)) == 1 and len(last_three_contents) >= 3:
            print("检测到AI消息重复，强制结束对话")
            state['completed'] = True
            # 添加结束消息
            final_message = AIMessage(content="检测到响应重复，对话结束。如需继续，请提供更具体的请求或开始新的对话。", name=cur_node)
            state["messages"].append(final_message)
            return {
                "completed": True,
                "messages": [final_message]
            }

        # 检查是否都是标准结束语
        standard_endings = [
            "我理解您的请求。请问还有什么我可以帮助您的吗？",
            "如果一切清楚，可以直接告诉我，以便我们结束这次对话。"
        ]

        if all(content in standard_endings for content in last_three_contents[-3:]):
            print("检测到连续的标准结束语，强制结束对话")
            state['completed'] = True
            # 添加结束消息
            final_message = AIMessage(content="对话自然结束。感谢您的使用！如有其他问题，请随时开始新的对话。", name=cur_node)
            state["messages"].append(final_message)
            return {
                "completed": True,
                "messages": [final_message]
            }

    try:
        # 记录LLM调用信息
        print(f"\n=== LLM 调用详情 ===")
        # 记录调用时间
        start_time = time.time()
        print(f"开始调用 LLM: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}")

        model_name = state.get("model")

        # 调用 LLM (使用安全调用函数)
        response = await safe_llm_invoke(llm, config, model_name, llm_messages, disable_emit=True)

        logger.info(f"LLM 响应内容：{response}")
        
        # 记录响应时间
        end_time = time.time()
        print(f"LLM 响应完成: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
        print(f"响应耗时: {end_time - start_time:.2f} 秒")
        

        # 验证工具调用
        if hasattr(response, "tool_calls") and response.tool_calls:
            print("---------------------")
            print(f"LLM 响应包含工具调用: {[tc['name'] for tc in response.tool_calls]}")

            # 验证和清理工具调用参数
            try:
                cleaned_tool_calls = validate_tool_calls_json(response.tool_calls)
                response.tool_calls = cleaned_tool_calls
                print("✅ 工具调用参数验证和清理完成")
            except Exception as tc_e:
                print(f"⚠️ 工具调用清理失败: {str(tc_e)}")
                # 如果工具调用清理失败，移除工具调用
                response.tool_calls = []
        else:
            print("LLM 响应不包含工具调用")
            if not response.content or not response.content.strip():
                print("警告：LLM返回空响应，使用默认回复")
                response.content = "我理解您的请求。请问还有什么我可以帮助您的吗？"
        
        # 处理响应内容
        if response.content and any(indicator in response.content.lower() for indicator in ['.md', 'markdown', '```']):
            # 如果响应包含Markdown内容，修复显示
            response.content = fix_markdown_display(response.content)

        response.name = cur_node
        state["messages"].append(response)
        state["inner_messages"].append(response)

        print(f"LLM 响应内容: {response.content[:300]}...")
        

        # 🔥 新增：多步骤工作流状态更新逻辑（类似A2A智能体）
        # 检查是否为多步骤工作流中的通用智能体执行
        workflow_plan = state.get("workflow_plan") or {}
        workflow_type = workflow_plan.get("workflow_type", "single_step")
        current_step_index = state.get("current_step_index", 0)

        if workflow_type == "multi_step":
            print(f"🔄 通用智能体在多步骤工作流中执行完成，当前步骤: {current_step_index + 1}")

            # 标记当前步骤完成
            state["current_step_completed"] = True

            # 递增步骤索引
            state["current_step_index"] = current_step_index + 1
            print(f"✅ 通用智能体步骤索引已递增: {current_step_index} → {current_step_index + 1}")

            # 保存执行结果供后续步骤使用
            if "execution_results" not in state:
                state["execution_results"] = {}

            # 使用特殊的key来标识通用智能体的结果
            general_agent_key = f"general_agent_step_{current_step_index + 1}"
            state["execution_results"][general_agent_key] = {
                "agent_name": "通用智能体",
                "result": response.content,
                "timestamp": datetime.datetime.now().isoformat(),
                "success": True,
                "step_id": current_step_index + 1
            }

            print(f"💾 通用智能体执行结果已保存，key: {general_agent_key}")
        else:
            print(f"📋 通用智能体执行单步任务或非工作流任务")

            # 🔥 关键修复：单步任务完成后也要递增步骤索引，让supervisor能检测到完成
            state["current_step_completed"] = True
            state["current_step_index"] = current_step_index + 1
            print(f"✅ 单步任务完成，步骤索引已递增: {current_step_index} → {current_step_index + 1}")

            # 保存执行结果
            if "execution_results" not in state:
                state["execution_results"] = {}

            # 使用特殊的key来标识通用智能体单步任务的结果
            single_step_key = f"general_agent_single_step"
            state["execution_results"][single_step_key] = {
                "agent_name": "通用智能体",
                "result": response.content,
                "timestamp": datetime.datetime.now().isoformat(),
                "success": True,
                "step_id": current_step_index + 1
            }

            print(f"💾 单步任务执行结果已保存，key: {single_step_key}")

    except Exception as e:
        # 增强的异常处理
        error_type = type(e).__name__
        error_msg = str(e)

        print(f"\n=== LLM 调用异常详情 (JSON格式错误专项处理) ===")
        print(f"异常类型: {error_type}")
        print(f"异常消息: {error_msg}")

        # 特殊处理JSON相关错误
        if any(keyword in error_msg.lower() for keyword in ["expecting", "delimiter", "json", "invalid character"]):
            print(get_error_msg(type="json"))

            # 尝试重新构建简化的消息
            try:
                print("\n🔧 尝试使用简化消息重新调用...")

                # 创建最简化的消息，只包含核心内容
                simple_user_query = re.sub(r'[^\w\s\u4e00-\u9fff.,!?]', ' ', user_query) if user_query else "请帮助我"
                simple_user_query = re.sub(r'\s+', ' ', simple_user_query).strip()

                simple_messages = [
                    SystemMessage(content="你是一个有用的AI助手。请帮助用户解决问题。"),
                    HumanMessage(content=simple_user_query)
                ]

                print(f"简化查询: {simple_user_query}")

                model_name = state.get("model")

                response = await safe_llm_invoke(llm, config, model_name, simple_messages)

                # 处理响应内容
                if any(indicator in response.content.lower() for indicator in ['.md', 'markdown', '```']):
                    response.content = fix_markdown_display(response.content)

                new_message = AIMessage(content=response.content, name=cur_node)
                state["messages"].append(new_message)
                state["inner_messages"].append(new_message)

                print("✅ 简化消息调用成功")
                return state

            except Exception as retry_e:
                print(f"❌ 简化消息调用也失败: {str(retry_e)}")

                # 最后的降级方案：使用预设回复
                print("🔧 使用预设回复作为最后的降级方案")
                fallback_content = f"抱歉，我在处理您的请求时遇到了技术问题。您的请求是：{simple_user_query if 'simple_user_query' in locals() else user_query}。请尝试用更简单的方式重新提问。"
                fallback_response = AIMessage(content=fallback_content, name=cur_node)
                state["messages"].append(fallback_response)
                state["inner_messages"].append(fallback_response)
                state['completed'] = True
                return state

        # 其他类型的错误处理
        if "Connection" in error_type or "connection" in error_msg.lower():
            print(get_error_msg(type="connection"))

        elif "timeout" in error_msg.lower():
            print(get_error_msg(type="timeout"))

        elif "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            print(get_error_msg(type="authentication"))

        elif "rate limit" in error_msg.lower():
            print(get_error_msg(type="rate limit"))

        else:
            print(get_error_msg(type="other"))

        # 打印完整的错误堆栈
        import traceback
        print("\n完整错误堆栈:")
        traceback.print_exc()

        # 记录环境信息
        print("\n=== 环境信息 ===")
        print(f"Python 版本: {sys.version}")
        print(f"操作系统: {platform.system()} {platform.release()}")

        # 设置错误响应
        error_content = f"抱歉，我遇到了一些技术问题（{error_type}）。请您稍后再试。如果问题持续存在，请尝试简化您的请求。"
        print(f"Error in agent_node: {error_msg}")
        state["messages"].append(AIMessage(content=error_content, name=cur_node))
        state["inner_messages"].append(AIMessage(content=error_content, name=cur_node))
        # 设置完成标志避免无限循环
        state['completed'] = True

    return {
        "last_node": cur_node,
        "messages": state['messages'],
        "inner_messages": state['inner_messages'],
        "temporary_message_content_list": state["temporary_message_content_list"],
        "completed": state['completed'],
        "current_step_completed": state["current_step_completed"],
        "current_step_index": state["current_step_index"],
        "execution_results": state["execution_results"],
        "logs":state["logs"],
        "e2b_sandbox_id": state["e2b_sandbox_id"],
        "iteration_count": state["iteration_count"],
        "max_iterations": state["max_iterations"],
        "temporary_images": state["temporary_images"],
        "structure_tool_results": state["structure_tool_results"],
        "mcp_tools": state["mcp_tools"],
        "input_data": state["input_data"],
        "model": state.get("model", global_config.BASE_LLM),
        "a2a_agents": state["a2a_agents"],
        "a2a_sessions": state["a2a_sessions"],
        "route_to_a2a": state.get("route_to_a2a", None),
        "last_a2a_result": state.get("last_a2a_result", None),
        "a2a_failure_count": state["a2a_failure_count"],
        "a2a_fallback_to_general": state["a2a_fallback_to_general"],
        "failed_a2a_agents": state["failed_a2a_agents"],
        "supervisor_retry_count": state["supervisor_retry_count"],
        "supervisor_decision": state["supervisor_decision"],
        "workflow_steps": state["workflow_steps"],
        "workflow_plan": state.get("workflow_plan", None)
    }


async def process_a2a_agents(state: AgentState) -> AgentState:

    # 保存原始数据
    original_a2a_agents = state.get("a2a_agents", [])  # 保存原始A2A智能体数据

    # 从input字段获取A2A智能体数据
    if not original_a2a_agents:
        input_data = state.get("input", {})
        if input_data and "a2a_agents" in input_data:
            original_a2a_agents = input_data["a2a_agents"]
            print(f"[initial_setup_node] 从 input 中获取 a2a_agents: {len(original_a2a_agents)} 个智能体")

    # 设置A2A智能体数据
    if original_a2a_agents:
        state["a2a_agents"] = original_a2a_agents
        print(f"[initial_setup_node] 设置 a2a_agents: {len(original_a2a_agents)} 个智能体")

        # 增强调试信息：打印每个A2A智能体的详细信息
        print("\n========== A2A 智能体详细信息 ==========")
        for idx, agent in enumerate(original_a2a_agents, 1):
            print(f"\n--- A2A智能体 {idx} ---")
            print(f"  ID: {agent.get('agent_id', agent.get('agent_Id', 'Unknown'))}")
            print(f"  名称: {agent.get('name', 'Unknown')}")
            print(f"  描述: {agent.get('desc', agent.get('description', 'No description'))}")
        print("=====================================\n")

    # 消息处理已由 create_initial_state 统一处理，无需重复添加
    print(f"[initial_setup_node] 消息已由 create_initial_state 处理，当前消息数量: {len(state.get('messages', []))}")

    return state


async def process_mcp_tools(state: AgentState) -> AgentState:

    # 保存原始数据
    original_mcp_tools = state.get("mcp_tools", [])

    # 从input字段获取数据
    if not original_mcp_tools:
        input_data = state.get("input", {})
        if input_data and "mcp_tools" in input_data:
            original_mcp_tools = input_data["mcp_tools"]
            print(f"[initial_setup_node] 从 input 中获取 mcp_tools: {len(original_mcp_tools)} 个工具")

    # 设置MCP工具数据
    if original_mcp_tools:
        normalized_mcp_tools = []
        for tool in original_mcp_tools:
            normalized_tool = normalize_mcp_tool_data(tool)
            normalized_mcp_tools.append(normalized_tool)

        state["mcp_tools"] = normalized_mcp_tools
        print(f"[initial_setup_node] 设置标准化后的 mcp_tools: {len(normalized_mcp_tools)} 个工具")

        # 增强调试信息：打印每个工具的详细信息
        print("\n========== MCP 工具详细信息 ==========")
        for idx, tool in enumerate(normalized_mcp_tools, 1):
            print(f"\n--- 工具 {idx} ---")
            print(f"  名称: {tool.get('name', 'Unknown')}")
            print(f"  ID: {tool.get('id', tool.get('tool_id', 'Unknown'))}")
            print(f"  类型: {tool.get('type', 'unknown')}")
            print(f"  描述: {tool.get('description', tool.get('desc', 'No description'))}")

            # 打印参数信息
            params = tool.get('parameters', tool.get('arguments', {}))
            if params:
                print(f"  参数结构:")
                print(f"    {json.dumps(params, indent=4, ensure_ascii=False)}")
            else:
                print(f"  参数结构: 无")

            # 如果有预定义参数值
            if 'arguments' in tool and isinstance(tool['arguments'], list):
                print(f"  预定义参数值:")
                for arg in tool['arguments']:
                    print(f"    {json.dumps(arg, ensure_ascii=False)}")
        print("=====================================\n")

    return state


async def process_knowledge(state: AgentState, config: RunnableConfig) -> AgentState:
    # todo 初始化 知识库信息

    return state



# 使用 MarkItDown 转换并写入上下文
async def process_attachment(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    附件处理节点
    - 从 state["files"] 读取本地附件路径
    - 使用 convert_to_markdown_unified 转换并写入 E2B 沙箱
    - 从沙箱读取生成的 .md 内容，汇总到 state["inner_messages"]
    """
    print("=== Attachment Processor Node (MarkItDown) 开始 ===")
    # state["files"] 存本地附件路径
    files = state.get("files", [])
    if not files:
        print("[attachment_processor] 未发现附件文件，跳过处理")
        return state
        
    if files[0].strip().split(".")[-1].lower() in ["jpg", "jpeg", "png", "gif", "bmp", "webp"]:
        context_content = "图片地址为：" + files[0]
        state["inner_messages"].append(AIMessage(content=context_content, name="attachment"))
        return state

    # 日志：开始处理
    if "logs" not in state:
        state["logs"] = []
    state["logs"].append({
        "message": f"发现{len(files)}个附件，正在转换为Markdown...",
        "done": False,
        "messageId": get_last_show_message_id(state.get("messages", []))
    })

    context_parts = ["=== 附件内容解析结果 ===\n"]

    for idx, file in enumerate(files, 1):
        try:
            if not isinstance(file, str):
                print(f"非字符串附件路径，跳过: {type(file)}")
                continue
            src_path = file
            file_name = os.path.basename(src_path)

            if not os.path.exists(src_path):
                print(f"本地附件不存在，跳过: {src_path}")
                continue

            print(f"使用本地附件路径: {src_path}")

            # 在沙箱中保存的 Markdown 文件路径
            stem = os.path.splitext(file_name)[0]
            sandbox_md_path = f"/home/md/attachment_{idx}_{stem}.md"

            # 直接从 state 读取 e2b_sandbox_id
            sandbox_id = state.get("e2b_sandbox_id")
            if not sandbox_id:
                print("沙箱未实例化，无法进行沙箱转换，跳过该附件。")
                continue

            # 先连接一次沙箱，后续写入与读取复用同一连接
            from e2b import Sandbox
            sbx = await asyncio.to_thread(Sandbox.connect, str(sandbox_id))

            # 执行统一的沙箱 Markdown 转换
            # 在异步环境中将潜在阻塞的文件解析与写入沙箱操作卸载到线程
            result = await asyncio.to_thread(
                convert_to_markdown_unified,
                file_path=src_path,
                sandbox_id=str(sandbox_id),
                sandbox_path=sandbox_md_path,
                output_path=None,
                sbx=sbx,
            )
            file_type = result.get("file_type", "unknown")
            sandbox_path = result.get("sandbox_path", sandbox_md_path)

            print(f"转换完成: 类型={file_type}, 沙箱Markdown={sandbox_path}")

            # 从沙箱读取生成的 Markdown 内容，增加短暂重试，避免写入后立即读取导致空
            md_content = ""
            try:
                last_err = None
                for attempt in range(5):
                    try:
                        content = await asyncio.to_thread(sbx.files.read, sandbox_path)
                        if isinstance(content, bytes):
                            content = content.decode("utf-8", errors="replace")
                        if isinstance(content, str) and content.strip():
                            md_content = content
                            break
                        await asyncio.sleep(0.4 * (2 ** attempt))
                    except Exception as e:
                        last_err = e
                        await asyncio.sleep(0.4 * (2 ** attempt))
                if not md_content:
                    raise RuntimeError(f"沙箱读取内容为空或失败，path={sandbox_path}, err={last_err}")
            except Exception as read_err:
                md_content = f"读取沙箱Markdown失败: {str(read_err)}"

            # 汇总上下文（对内容进行长度控制）
            header = f"**附件 {file_name}** (类型: {file_type}):\n"
            context_parts.append(header)
            max_chars = int(os.getenv("ATTACHMENT_CONTEXT_MAX_CHARS", "120000"))
            # max_chars = 120000
            current_len = sum(len(p) for p in context_parts)
            remaining = max_chars - current_len
            context_parts.append(md_content[:remaining] if remaining > 0 else "")
            context_parts.append("\n")

        except Exception as e:
            print(f"❌ 处理附件失败: {str(e)}")
            # 对于字符串路径，提取文件名
            file_name = os.path.basename(file) if isinstance(file, str) else f"attachment_{idx}"
            context_parts.append(f"**附件 {file_name}** 处理失败: {str(e)}\n")

    # 组合上下文内容
    context_parts.append("=== 基于以上附件内容，请回答用户问题 ===\n")
    context_content = "\n".join(context_parts)

    # 写入到上下文消息
    state["inner_messages"].append(AIMessage(content=context_content, name="attachment"))

    # 完成日志
    state["logs"].append({
        "message": "附件解析完成，已生成Markdown并写入上下文",
        "done": True,
        "messageId": get_last_show_message_id(state.get("messages", []))
    })

    print("=== Attachment Processor Node (MarkItDown) 完成 ===")
    return state


def route_after_agent_node(last_message):
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print(f"[通用智能体路由] 检测到工具调用: {[tool_call['name'] for tool_call in last_message.tool_calls]}")
        return "tool_executor"
    else:
        return "supervisor"

