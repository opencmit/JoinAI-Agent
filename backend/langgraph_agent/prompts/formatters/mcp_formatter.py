"""
MCP 工具格式化模块

提供将 MCP 工具转换为 prompt 文本的格式化函数
"""

from typing import List, Dict, Any, Union


def format_mcp_tools_for_prompt_english(mcp_tools: Union[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]) -> str:
    """
    Converts MCP tools into a formatted text string suitable for an Agent prompt in English.

    Args:
        mcp_tools: Can be either:
            - A list of dictionaries containing MCP tool definitions
            - A dictionary where keys are tool names and values are tool definitions

    Returns:
        A formatted string describing the available MCP tools in English.
    """

    # 处理不同的输入格式
    if isinstance(mcp_tools, dict):
        # 如果输入是字典格式，转换为列表
        tools_list = []
        for tool_key, tool_data in mcp_tools.items():
            tool_copy = tool_data.copy()
            # 如果工具数据中没有name字段，使用键名作为name
            if 'name' not in tool_copy:
                tool_copy['name'] = tool_key
            tools_list.append(tool_copy)
    else:
        tools_list = mcp_tools

    if not tools_list:
        return "Currently, no custom MCP tools are mounted."

    prompt_text = "## Available MCP Tools\n\n"
    prompt_text += "Below is a list of custom MCP tools currently available. Please select the appropriate tool based on the task requirements.\n\n"

    for tool in tools_list:
        name = tool.get('name', 'Unknown Tool Name')
        # 支持多种描述字段名
        description = (tool.get('description') or
                       tool.get('desc') or
                       'No description provided').strip()

        tool_type = tool.get('type', 'normal')
        tool_id = tool.get('tool_id') or tool.get('id', '')

        prompt_text += f"### Tool: {name}\n"
        prompt_text += f"Description: {description}\n"

        if tool_id:
            prompt_text += f"Tool ID: {tool_id}\n"

        if tool_type:
            prompt_text += f"Type: {tool_type}\n"

        # 处理参数信息 - 支持多种格式
        parameters = tool.get('parameters', {})
        properties = parameters.get('properties', {}) if parameters else tool.get('properties', {})
        required_params = parameters.get('required', []) if parameters else tool.get('required', [])

        if properties:
            prompt_text += "Parameters:\n"
            for param_name, param_details in properties.items():
                param_type = param_details.get('type', 'Any type')
                param_description = param_details.get('description', 'No description')
                required_status = " (Required)" if param_name in required_params else " (Optional)"
                prompt_text += f"  - {param_name} ({param_type}){required_status}: {param_description}\n"
        else:
            # 如果是知识库类型，自动添加默认参数说明
            if tool_type == 'knowledge':
                prompt_text += "Parameters: This knowledge base tool automatically uses dbList (knowledge base IDs) and content (user question)\n"
            else:
                prompt_text += "Parameters: None (This tool requires no parameters)\n"

        # 显示预配置的参数（如果有）
        arguments = tool.get('arguments', [])
        if arguments and any(arg for arg in arguments if arg):
            prompt_text += "Pre-configured Arguments:\n"
            for arg in arguments:
                if arg:
                    arg_name = arg.get('name', 'Unknown')
                    arg_value = arg.get('value', 'Not set')
                    prompt_text += f"  - {arg_name}: {arg_value}\n"

        prompt_text += "\n"

    return prompt_text

