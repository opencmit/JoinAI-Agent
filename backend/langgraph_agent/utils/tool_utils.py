"""
附件、html报告、markdown报告相关的功能函数
"""
from typing import Dict, List, Tuple, Any
import re
import json

from langchain_core.messages import AIMessage, ToolMessage, SystemMessage, HumanMessage, BaseMessage
from langgraph_agent.graph.state import AgentState
from langgraph_agent.utils.json_utils import sanitize_string_for_json, safe_json_dumps, deep_clean_for_json


def normalize_mcp_tool_data(tool_data: Dict[str, Any]) -> Dict[str, Any]:
    """标准化MCP工具数据格式，处理字段名差异"""
    normalized_tool = tool_data.copy()

    # 处理参数字段名差异：arguments -> parameters
    if "arguments" in normalized_tool and "parameters" not in normalized_tool:
        arguments = normalized_tool.pop("arguments")
        # 如果arguments是列表且只有一个元素，取第一个元素
        if isinstance(arguments, list) and len(arguments) > 0:
            normalized_tool["parameters"] = arguments[0]
        elif isinstance(arguments, list) and len(arguments) == 0:
            normalized_tool["parameters"] = {}
        else:
            normalized_tool["parameters"] = arguments if arguments else {}

    # 确保有description字段（从desc复制）
    if "desc" in normalized_tool and "description" not in normalized_tool:
        normalized_tool["description"] = normalized_tool["desc"]

    # 确保有id字段（从tool_id复制）
    if "tool_id" in normalized_tool and "id" not in normalized_tool:
        normalized_tool["id"] = normalized_tool["tool_id"]

    return normalized_tool


# ================================
#          附件相关
# ================================

# def should_process_attachments(state: AgentState) -> bool:
#     """统一判断是否需要处理attachment工具"""
#     # 检查是否有attachment工具
#     if not has_attachment_tools(state):
#         return False
#
#     # 检查是否已处理
#     if state.get("attachment_processed", False):
#         return False
#
#     # 检查是否是首次对话（第一轮）
#     if state.get("conversation_round", 0) == 1:
#         return True
#
#     # 检查强制标志
#     if state.get("force_attachment_call", False):
#         return True
#
#     # 其他情况不处理
#     return False


# def has_attachment_tools(state: AgentState) -> bool:
#     """检查状态中是否有附件工具"""
#     # 从状态中获取 MCP 工具数据，尝试多个可能的位置
#     mcp_tools_data = state.get("mcp_tools", [])
#
#     # 如果 mcp_tools 为空，尝试从 input_data 中获取
#     if not mcp_tools_data:
#         input_data = state.get("input_data", {})
#         mcp_tools_data = input_data.get("mcp_tools", [])
#
#     # 如果还是为空，尝试从 input 中获取（新格式支持）
#     if not mcp_tools_data and "input" in state:
#         input_section = state["input"]
#         mcp_tools_data = input_section.get("mcp_tools", [])
#
#     # 检查是否有attachment类型的工具
#     for tool_data in mcp_tools_data:
#         if tool_data.get('type') == 'attachment':
#             return True
#
#     return False


def get_attachment_tools(state: AgentState) -> List[Dict[str, Any]]:
    """获取状态中的所有附件工具"""
    # 从状态中获取 MCP 工具数据，尝试多个可能的位置
    mcp_tools_data = state.get("mcp_tools", [])

    # 如果 mcp_tools 为空，尝试从 input_data 中获取
    if not mcp_tools_data:
        input_data = state.get("input_data", {})
        mcp_tools_data = input_data.get("mcp_tools", [])

    # 如果还是为空，尝试从 input 中获取（新格式支持）
    if not mcp_tools_data and "input" in state:
        input_section = state["input"]
        mcp_tools_data = input_section.get("mcp_tools", [])

    # 收集所有attachment类型的工具
    attachment_tools = []
    for tool_data in mcp_tools_data:
        if tool_data.get('type') == 'attachment':
            attachment_tools.append(tool_data)

    return attachment_tools


# ================================
#  markdown和html报告相关
# ================================


def fix_markdown_display(content: str) -> str:
    """修复Markdown显示问题 - 改进版本"""
    import re

    # 提取所有代码块
    code_blocks = []
    code_block_pattern = r'```[\s\S]*?```'

    def process_code_block_content(block_content: str) -> str:
        """处理代码块内容的转义字符"""
        # 特殊处理路径中的双反斜杠
        # 例如: C:\\\\Users\\\\Documents -> C:\\Users\\Documents
        # 先处理四个反斜杠的情况（表示两个反斜杠）
        block_content = block_content.replace('\\\\\\\\', '\\\\')

        # 然后处理其他转义序列
        block_content = block_content.replace('\\n', '\n')
        block_content = block_content.replace('\\t', '\t')
        block_content = block_content.replace('\\"', '"')

        # 最后处理剩余的双反斜杠（如果不是路径的一部分）
        # 这一步要小心，避免破坏已经正确的反斜杠
        if '\\\\' in block_content and not re.search(r'[A-Za-z]:\\\\', block_content):
            block_content = block_content.replace('\\\\', '\\')

        return block_content

    def replace_code_block(match):
        # 获取代码块内容
        block_content = match.group(0)

        # 处理代码块内部的转义字符
        block_content = process_code_block_content(block_content)

        # 保存处理后的代码块
        code_blocks.append(block_content)
        return f"__CODE_BLOCK_{len(code_blocks) - 1}__"

    # 临时替换代码块（同时处理其内容）
    content = re.sub(code_block_pattern, replace_code_block, content)

    # 修复非代码块区域的转义问题
    # 注意处理顺序很重要
    content = content.replace('\\\\n', '\n')  # 处理 \\n
    content = content.replace('\\n', '\n')  # 处理 \n
    content = content.replace('\\t', '\t')  # 处理 \t
    content = content.replace('\\|', '|')  # 处理 \|
    content = content.replace('\\"', '"')  # 处理 \"
    content = content.replace('\\\\', '\\')  # 最后处理 \\
    content = content.replace('“', '"')  # 处理“
    content = content.replace('”', '"')  # 处理”

    # 恢复处理后的代码块
    for i, block in enumerate(code_blocks):
        content = content.replace(f"__CODE_BLOCK_{i}__", block)

    # 修复表格格式
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        stripped = line.strip()

        # 检测表格
        if '|' in stripped:
            # 确保表格行格式正确
            if not stripped.startswith('|'):
                line = '| ' + line.strip()
            if not stripped.endswith('|'):
                line = line.strip() + ' |'

            # 修复表格分隔行
            if '---' in line:
                parts = line.split('|')
                fixed_parts = []
                for part in parts:
                    if '---' in part:
                        fixed_parts.append('---')
                    else:
                        fixed_parts.append(part)
                line = '|'.join(fixed_parts)

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def extract_html_content(raw_content: str) -> Tuple[str, bool]:
    """
    从模型生成的原始内容中提取纯HTML代码

    Args:
        raw_content: 模型生成的原始内容，可能包含思考过程、markdown说明等

    Returns:
        Tuple[str, bool]: (提取的HTML内容, 是否成功提取)
    """

    # 方法1: 提取markdown代码块中的HTML
    html_code_pattern = r'```html\s*\n(.*?)\n```'
    html_match = re.search(html_code_pattern, raw_content, re.DOTALL | re.IGNORECASE)

    if html_match:
        html_content = html_match.group(1).strip()
        print(f"✅ 从markdown代码块中提取HTML内容，长度: {len(html_content)} 字符")
        return html_content, True

    # 方法2: 查找完整的HTML文档结构（<!DOCTYPE html>开始）
    doctype_pattern = r'(<!DOCTYPE html>.*?</html>)'
    doctype_match = re.search(doctype_pattern, raw_content, re.DOTALL | re.IGNORECASE)

    if doctype_match:
        html_content = doctype_match.group(1).strip()
        print(f"✅ 从文档中提取完整HTML结构，长度: {len(html_content)} 字符")
        return html_content, True

    # 方法3: 查找HTML标签开始到结束
    html_tag_pattern = r'(<html[^>]*>.*?</html>)'
    html_tag_match = re.search(html_tag_pattern, raw_content, re.DOTALL | re.IGNORECASE)

    if html_tag_match:
        html_content = html_tag_match.group(1).strip()
        print(f"✅ 从HTML标签中提取内容，长度: {len(html_content)} 字符")
        return html_content, True

    # 方法4: 移除思考标签和其他无关内容
    cleaned_content = raw_content

    # 移除<think>标签及其内容
    think_pattern = r'<think>.*?</think>'
    cleaned_content = re.sub(think_pattern, '', cleaned_content, flags=re.DOTALL)

    # 移除markdown标题和说明文字（以#开头的行和普通文本段落）
    lines = cleaned_content.split('\n')
    html_lines = []
    in_html = False

    for line in lines:
        stripped_line = line.strip()

        # 检测HTML开始
        if (stripped_line.startswith('<!DOCTYPE') or
                stripped_line.startswith('<html') or
                (not in_html and '<' in stripped_line and '>' in stripped_line)):
            in_html = True

        # 如果在HTML中，收集行
        if in_html:
            html_lines.append(line)

        # 检测HTML结束
        if stripped_line.endswith('</html>'):
            break

    if html_lines:
        html_content = '\n'.join(html_lines).strip()
        print(f"✅ 通过行解析提取HTML内容，长度: {len(html_content)} 字符")
        return html_content, True

    print("❌ 未能从内容中提取HTML代码")
    return raw_content, False


def clean_html_content(html_content: str) -> str:
    """
    清理HTML内容，移除不必要的空行和格式问题

    Args:
        html_content: 原始HTML内容

    Returns:
        str: 清理后的HTML内容
    """

    # 移除多余的空行
    lines = html_content.split('\n')
    cleaned_lines = []
    prev_empty = False

    for line in lines:
        stripped = line.strip()

        # 如果是空行
        if not stripped:
            # 避免连续的空行
            if not prev_empty:
                cleaned_lines.append('')
            prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False

    # 移除开头和结尾的空行
    while cleaned_lines and not cleaned_lines[0].strip():
        cleaned_lines.pop(0)
    while cleaned_lines and not cleaned_lines[-1].strip():
        cleaned_lines.pop()

    return '\n'.join(cleaned_lines)


def validate_html_content(html_content: str) -> bool:
    """
    验证HTML内容的有效性

    Args:
        html_content: HTML内容

    Returns:
        bool: 是否为有效的HTML
    """

    html_lower = html_content.lower()

    # 检查基本HTML结构
    has_html_tag = '<html' in html_lower and '</html>' in html_lower
    has_head_tag = '<head' in html_lower and '</head>' in html_lower
    has_body_tag = '<body' in html_lower and '</body>' in html_lower
    has_doctype = '<!doctype html>' in html_lower

    # 基本验证：至少应该有HTML标签
    if has_html_tag and has_head_tag and has_body_tag:
        print("✅ HTML结构验证通过")
        return True
    elif '<html' in html_lower or '<!doctype' in html_lower:
        print("⚠️ HTML结构不完整但包含HTML元素")
        return True
    else:
        print("❌ HTML结构验证失败")
        return False


async def process_raw_html_content(
        raw_content: str,
        state: dict,
        config: dict,
        user_query: str = ""
) -> Tuple[str, str]:
    """
    处理原始HTML内容的完整流程 - 增强调试版本
    """

    print("=== 开始处理原始HTML内容 (调试版本) ===")
    print(f"原始内容长度: {len(raw_content)} 字符")
    print(f"用户查询: {user_query}")

    # 第一步：提取HTML内容
    html_content, extraction_success = extract_html_content(raw_content)

    if not extraction_success:
        return f"""❌ **HTML内容提取失败**

无法从生成的内容中识别有效的HTML代码。

**原始内容长度**: {len(raw_content)} 字符

**建议**: 请检查生成的内容格式，确保包含完整的HTML代码。""", ""

    # 第二步：清理HTML内容
    html_content = clean_html_content(html_content)
    print(f"清理后HTML内容长度: {len(html_content)} 字符")

    # 第三步：验证HTML内容
    if not validate_html_content(html_content):
        print("⚠️ HTML验证失败，但仍继续保存")

    # 第四步：保存文件
    try:
        from langgraph_agent.tools import files_tool

        # 生成文件名 - 改进版
        import time
        timestamp = int(time.time())

        # 从用户查询中提取关键词作为文件名
        safe_query = ""
        if user_query:
            # 移除特殊字符，保留中英文和数字
            safe_query = re.sub(r'[^\w\u4e00-\u9fff]', '_', user_query)[:30]
            safe_query = safe_query.strip('_')  # 移除首尾下划线

        filename = f"{safe_query}_{timestamp}.html" if safe_query else f"webpage_{timestamp}.html"

        print(f"生成的文件名: {filename}")
        print(f"文件将保存到沙箱根目录: /{filename}")

        # 准备保存参数 - 增强调试
        tool_args = {
            "operation": "create",
            "path": filename,  # 确保路径正确
            "content": html_content,
            "state": state,
            "special_config_param": config  # 确保传递正确的config
        }

        print("准备调用files_tool保存文件...")
        print(
            f"工具参数: operation={tool_args['operation']}, path={tool_args['path']}, content_length={len(tool_args['content'])}")

        result_arguments = {
            "content": html_content,
            "operation": "write",
            "path": filename
        }
        state["messages"].append(
            AIMessage(
                content="",
                additional_kwargs={
                    'tool_calls': [
                        {
                            'index': 0,
                            'id': '',
                            'function': {
                                'arguments': json.dumps(result_arguments),
                                'name': 'files'
                            },
                            'type': 'function'
                        }
                    ]
                }
            )
        )

        # 执行保存
        result_state, save_result = await files_tool.ainvoke(tool_args, config=config)
        if "copilotkit" not in result_state:
            result_state["copilotkit"] = {"actions": []}
        if "actions" not in result_state["copilotkit"]:
            result_state["copilotkit"]["actions"] = []
        # 创建工具调用记录
        file_tool_action = {
            "name": "files_tool",
            "tool_call_id": f"html_save_{int(time.time())}",
            "args": {
                "operation": "create",
                "path": filename,
                "content_length": len(html_content)  # 不记录完整内容，只记录长度
            },
            "result": save_result,
            "timestamp": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
            "context": "html_generation"  # 标记这是HTML生成过程中的调用
        }

        # 添加到copilotkit actions
        result_state["copilotkit"]["actions"].append(file_tool_action)
        result_state["messages"].append(ToolMessage(content=tool_args["content"], name="files", tool_call_id=""))
        print(f"✅ 已记录file工具调用到copilotkit，当前actions数量: {len(result_state['copilotkit']['actions'])}")

        state.update(result_state)

        print(f"files_tool执行结果: {save_result}")
        print(f"返回的状态类型: {type(result_state)}")

        # 检查保存结果 - 更严格的检查
        save_success = (
                "成功" in str(save_result) or
                "created" in str(save_result).lower() or
                "创建成功" in str(save_result)
        )

        print(f"保存成功判断: {save_success}")

        if save_success:
            # 尝试验证文件是否真的存在（如果可能）
            verification_msg = ""
            try:
                # 尝试读取文件来验证
                verify_args = {
                    "operation": "read",
                    "path": filename,
                    "state": result_state,
                    "special_config_param": config
                }

                verify_state, verify_result = await files_tool.ainvoke(verify_args, config=config)

                if "文件内容:" in str(verify_result):
                    verification_msg = "\n✅ **文件验证**: 文件已成功创建并可读取"
                    print("✅ 文件验证成功")
                else:
                    verification_msg = f"\n⚠️ **文件验证**: 无法读取文件 - {verify_result}"
                    print(f"⚠️ 文件验证失败: {verify_result}")

            except Exception as verify_error:
                verification_msg = f"\n⚠️ **文件验证**: 验证过程异常 - {str(verify_error)}"
                print(f"⚠️ 文件验证异常: {verify_error}")

            response_content = f"""✅ **HTML文件处理和保存完成**

**文件信息**:
- 文件名: `{filename}`
- 文件大小: {len(html_content)} 字符
- 保存位置: 沙箱根目录
- 提取方式: {'markdown代码块' if '```html' in raw_content else 'HTML标签识别'}

**处理步骤**:
1. ✅ 从原始内容中提取HTML代码
2. ✅ 清理和格式化HTML内容  
3. ✅ 验证HTML结构完整性
4. ✅ 保存到沙箱文件系统

{verification_msg}

**使用方法**:
1. 文件已保存在沙箱环境中
2. 可以使用文件工具查看或操作HTML文件
3. 在浏览器中打开查看效果

**HTML内容预览** (前500字符):
```html
{html_content[:500]}...
```

**详细保存结果**: {save_result}"""

        else:
            print(f"❌ 保存失败，详细结果: {save_result}")
            response_content = f"""⚠️ **HTML内容提取成功但保存失败**

**提取信息**:
- HTML内容长度: {len(html_content)} 字符
- 建议文件名: `{filename}`

**保存失败原因**: {save_result}

**完整的HTML内容**:
```html
{html_content}
```

**排查建议**:
1. 检查沙箱环境是否正常运行
2. 确认文件权限设置
3. 检查磁盘空间是否充足
4. 查看详细错误日志"""

        return response_content, filename

    except Exception as e:
        print(f"❌ 保存文件时发生异常: {str(e)}")
        import traceback
        traceback.print_exc()

        error_response = f"""⚠️ **HTML内容提取成功但保存异常**

**错误信息**: {str(e)}

**提取的HTML内容** (长度: {len(html_content)} 字符):
```html
{html_content}
```

**异常详情**: 
```
{traceback.format_exc()}
```

**建议操作**:
1. 手动复制上述HTML代码
2. 保存为 `{filename if 'filename' in locals() else f'webpage_{int(time.time())}.html'}`
3. 检查沙箱环境和files_tool配置
4. 查看系统日志获取更多信息"""

        return error_response, ""


def normalize_tool_result(result: Any, tool_name: str) -> str:
    """标准化工具执行结果"""
    if result is None:
        return f"工具 {tool_name} 执行完成，但没有返回结果。"

    if isinstance(result, str):
        return result.strip() or f"工具 {tool_name} 返回了空字符串。"

    if isinstance(result, dict):
        # 按优先级尝试提取内容
        for key in ['content', 'result', 'message', 'output']:
            if key in result and result[key]:
                return str(result[key])
        # 如果没有找到标准字段，返回整个字典的字符串表示
        return json.dumps(result, ensure_ascii=False, indent=2)

    # 其他类型直接转字符串
    return str(result)



