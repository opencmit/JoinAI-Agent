"""
MCP Prompt Builder

负责动态生成 MCP 相关的 prompt
"""

from typing import List, Dict, Any, Optional
from langgraph_agent.graph.state import AgentState
from langgraph_agent.graph.mcp_client import MCPConnectionManager
from langgraph_agent.prompts.formatters.mcp_formatter import format_mcp_tools_for_prompt_english
from langgraph_agent.utils.json_utils import sanitize_string_for_json, deep_clean_for_json


async def get_mcp_prompt(state: AgentState, user_query: str, mcp_client: Optional[MCPConnectionManager] = None):
    """
    为 MCP 节点生成 prompt
    
    Args:
        state: AgentState 对象
        user_query: 用户查询字符串
        mcp_client: MCP连接管理器，如果为None则使用默认实例
        
    Returns:
        包含 MCP 工具信息的 prompt 字符串
    """
    
    # 清理用户查询用于API调用
    cleaned_user_query = sanitize_string_for_json(user_query, context="api")

    # 获取mcp_tools_prompt - 同样需要清理
    mcp_tools_for_copilotkit: List[Dict[str, Any]] = state.get("copilotkit", {}).get("actions", [])

    # 使用新的 mcp_client 获取工具
    if mcp_client is None:
        mcp_client = MCPConnectionManager.get_instance()
    
    mcp_tools = await mcp_client.get_tools()
    
    # 从工具对象生成 prompt 信息
    mcp_tools_dict_for_prompt = []
    for tool in mcp_tools:
        mcp_tools_dict_for_prompt.append({
            'name': tool.name,
            'description': tool.description,
            'parameters': {
                'type': 'object',
                'properties': {
                    'query': {
                        'type': 'string',
                        'description': '用户查询内容，工具将自动从中提取所需的具体参数执行操作'
                    }
                },
                'required': ['query']
            }
        })

    all_mcp_tools_for_prompt = mcp_tools_for_copilotkit + mcp_tools_dict_for_prompt

    # 清理 MCP 工具 prompt
    try:
        mcp_tools_prompt = format_mcp_tools_for_prompt_english(all_mcp_tools_for_prompt)
        mcp_tools_prompt = sanitize_string_for_json(mcp_tools_prompt, context="api")
        mcp_tools_prompt = (
                "\n\n <mcp_tools_mounted_status>" + mcp_tools_prompt + "</mcp_tools_mounted_status>") if mcp_tools_prompt else ""
    except Exception as e:
        print(f"⚠️ MCP工具prompt生成失败: {str(e)}")
        mcp_tools_prompt = ""

    return mcp_tools_prompt
