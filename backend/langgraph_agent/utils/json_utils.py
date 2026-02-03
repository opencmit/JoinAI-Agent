"""
json格式修正、清理相关的函数
"""
import json
import json_repair
import logging

logger = logging.getLogger(__name__)

def sanitize_string_for_json(text: str, context: str = "api") -> str:
    """
    根据上下文进行不同级别的字符串清理

    Args:
        text: 要清理的文本
        context: 使用场景 - "api"(API调用), "file"(文件保存), "display"(显示)
    """
    if not isinstance(text, str):
        return str(text)

    if context == "api":
        # API调用时需要严格的JSON转义
        text = text.replace('\\', '\\\\')
        text = text.replace('"', '\\"')
        text = text.replace('\n', '\\n')
        text = text.replace('\r', '\\r')
        text = text.replace('\t', '\\t')
        # 处理其他可能导致JSON错误的字符
        text = text.replace('\b', '\\b')
        text = text.replace('\f', '\\f')
        # 移除不可见的控制字符
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')

    elif context == "file":
        # 文件保存时保持原始格式
        # 只做最小的清理
        pass

    elif context == "display":
        # 显示时可以适度清理但保持可读性
        text = text.replace('\\\\n', '\n')
        text = text.replace('\\n', '\n')
        text = text.replace('\\t', '\t')

    return text


def safe_json_dumps(data, **kwargs):
    """
    安全的JSON序列化函数，处理可能的格式错误
    """
    try:
        # 首先尝试标准序列化
        return json.dumps(data, ensure_ascii=False, **kwargs)
    except (TypeError, ValueError, UnicodeDecodeError) as e:
        print(f"JSON序列化失败，尝试清理数据: {str(e)}")
        # 如果失败，递归清理数据
        cleaned_data = deep_clean_for_json(data)
        try:
            return json.dumps(cleaned_data, ensure_ascii=False, **kwargs)
        except Exception as clean_e:
            print(f"清理后JSON序列化仍然失败: {str(clean_e)}")
            # 最后的降级方案：强制转换为字符串
            return json.dumps(str(data), ensure_ascii=False, **kwargs)


def deep_clean_for_json(obj):
    """
    递归清理对象以确保JSON序列化兼容性
    """
    if isinstance(obj, str):
        # 对于文件内容，保持原样
        if "content" in str(obj) or "markdown" in str(obj).lower():
            return obj  # 不清理文件内容
        return sanitize_string_for_json(obj, context="api")
    elif isinstance(obj, dict):
        cleaned_dict = {}
        for k, v in obj.items():
            # 清理键名
            clean_key = sanitize_string_for_json(str(k), context="api") if not isinstance(k, (int, float)) else k
            # 特殊处理文件内容相关的键
            if k in ['content', 'markdown_content', 'html_content']:
                cleaned_dict[clean_key] = v  # 保持原样
            else:
                cleaned_dict[clean_key] = deep_clean_for_json(v)
        return cleaned_dict
    elif isinstance(obj, list):
        return [deep_clean_for_json(item) for item in obj]
    elif isinstance(obj, tuple):
        return [deep_clean_for_json(item) for item in obj]
    elif isinstance(obj, (int, float, bool, type(None))):
        return obj
    else:
        # 对于其他类型，转换为字符串并清理
        return sanitize_string_for_json(str(obj), context="api")


def validate_tool_calls_json(tool_calls):
    """验证和修复工具调用的JSON格式"""
    for tc in tool_calls:
        try:
            if 'args' in tc:
                # 对每个参数进行清理
                for key, value in tc['args'].items():
                    if isinstance(value, str):
                        # 特殊处理：对于execute_command工具的command参数
                        if tc['name'] == 'execute_command' and key == 'command':
                            # 命令参数使用特殊的清理策略
                            tc['args'][key] = sanitize_string_for_json(value, context="command")
                        elif key in ['content', 'markdown_content', 'html_content', 'query']:
                            # 对于查询和内容，使用适当的清理
                            if key == 'query':
                                tc['args'][key] = sanitize_string_for_json(value, context="api")
                            else:
                                tc['args'][key] = value  # 文件内容保持原样
                        else:
                            tc['args'][key] = sanitize_string_for_json(value, context="api")

            # 测试序列化
            test_json = safe_json_dumps(tc.get('args', {}))
            print(f"✅ 工具 {tc['name']} 参数验证通过")

        except Exception as e:
            print(f"⚠️ 工具 {tc['name']} 参数JSON格式异常: {str(e)}")
            # 降级处理
            if 'args' in tc:
                tc['args'] = deep_clean_for_json(tc['args'])

    return tool_calls


def repair_json_output(content: str) -> str:
    """
    修复和规范化 JSON 输出。

    Args:
        content (str): 可能包含 JSON 的字符串内容

    Returns:
        str: 修复后的 JSON 字符串，如果不是 JSON 则返回原始内容
    """
    content = content.strip()
    if content.startswith(("{", "[")) or "```json" in content:
        try:
            # 如果内容被包裹在```json代码块中，提取JSON部分
            if content.startswith("```json"):
                content = content.removeprefix("```json")

            if content.endswith("```"):
                content = content.removesuffix("```")

            # 尝试修复并解析JSON
            repaired_content = json_repair.loads(content)
            return json.dumps(repaired_content)
        except Exception as e:
            logger.warning(f"JSON repair failed: {e}")

    return content