"""
通用工具函数模块
"""

import asyncio

from typing import List, Dict, Any
from langchain_core.messages import AIMessage
from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.runnables import RunnableConfig


def add_error_message_if_not_exists(
    state: Dict[str, Any], 
    error_content: str, 
    message_key: str = "messages"
) -> bool:
    """
    检查并添加错误消息，避免重复添加相同的错误消息
    
    Args:
        state: 状态字典
        error_content: 错误消息内容
        message_key: 消息列表在状态中的键名
        
    Returns:
        bool: 是否添加了新消息
    """
    messages = state.get(message_key, [])
    
    # 检查是否已经存在相同的错误消息
    existing_error = False
    for msg in messages:
        if hasattr(msg, 'content') and error_content in msg.content:
            existing_error = True
            break
    
    if not existing_error:
        error_message = AIMessage(content=error_content)
        messages.append(error_message)
        state[message_key] = messages
        return True
    
    return False


def format_a2a_error_message(
    agent_name: str, 
    route_decision: str, 
    available_agents: List[str],
    error_type: str = "执行失败"
) -> str:
    """
    格式化A2A智能体错误消息
    
    Args:
        agent_name: 智能体名称
        route_decision: 路由决策
        available_agents: 可用智能体列表
        error_type: 错误类型
        
    Returns:
        str: 格式化的错误消息
    """
    available_str = "、".join(available_agents) if available_agents else "无"
    
    if error_type == "路由失败":
        return f"""❌ **A2A智能体路由失败**

**问题**: 推荐的智能体 `{route_decision}` 不存在或不可用。

**可用的A2A智能体**: {available_str}

**原因**: 可能是智能体ID不匹配或服务不可用。

正在重新进行路由决策..."""
    
    elif error_type == "执行失败":
        return f"""❌ **A2A智能体执行失败**

**问题**: 无法找到或连接到智能体 `{route_decision}`

**可用智能体**: {available_str}

**建议**: 请稍后重试或使用通用智能体服务。

正在重新进行智能体选择..."""
    
    else:
        return f"""❌ **A2A智能体{error_type}**

**问题**: 智能体 `{agent_name}` 执行过程中出现问题

**可用智能体**: {available_str}

**建议**: 请稍后重试或使用通用智能体服务。"""


async def send_temp_message_to_frontend(message: str, message_id: str, role: str, config: RunnableConfig):
    """
    Send a temporary message to the frontend.

    Args:
        message (str): The content of the message to be sent.
        message_id (str): The unique ID of the message.
        role (str): The role of the sender (e.g., user, assistant).
        config (RunnableConfig): The runtime configuration object for message dispatch.
    """
    await adispatch_custom_event(
        "copilotkit_manually_emit_message",
        {
            "message": message,
            "message_id": message_id,
            "role": role
        },
        config=config,
    )

    await asyncio.sleep(0.02)

async def send_temp_tool_call_to_frontend(tool_name: str, arguments: Dict[str, Any], tool_call_id: str, config: RunnableConfig):
    """
    Send a temporary tool call information to the frontend.

    Args:
        tool_name (str): The name of the tool.
        arguments (Dict[str, Any]): The arguments of the tool call.
        tool_call_id (str): The unique ID of the tool call.
        config (RunnableConfig): The runtime configuration object for message dispatch.
    """
    await adispatch_custom_event(
        "copilotkit_manually_emit_tool_call",
        {
            "name": tool_name,
            "args": arguments,
            "id": tool_call_id
        },
        config=config,
    )
    await asyncio.sleep(0.02)
