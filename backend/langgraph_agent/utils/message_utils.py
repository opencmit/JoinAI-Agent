from typing import Dict, List, Tuple, Any
import re
import json
import logging

from langchain_core.messages import AIMessage, ToolMessage, SystemMessage, HumanMessage, BaseMessage
from langgraph_agent.utils.json_utils import sanitize_string_for_json, safe_json_dumps, deep_clean_for_json

logger = logging.getLogger(__name__)

# 在调用LLM之前，验证和清理所有消息
def clean_messages(messages) -> List[BaseMessage]:
    print(f"\n=== 消息清理和验证 ===")
    cleaned_messages = []
    for i, msg in enumerate(messages):
        try:
            if hasattr(msg, 'content'):
                # 清理消息内容
                cleaned_content = sanitize_string_for_json(msg.content, context="api")

                # 验证清理后的内容能否正常JSON序列化
                try:
                    test_json = safe_json_dumps({"content": cleaned_content})
                    print(f"✅ 消息 {i} 清理和验证通过")
                except Exception as json_e:
                    print(f"⚠️ 消息 {i} JSON验证失败: {str(json_e)}")
                    # 进一步清理
                    cleaned_content = re.sub(r'[^\w\s\u4e00-\u9fff.,!?;:()\[\]{}/@#$%^&*+=\-_|\\<>]', ' ',
                                             cleaned_content)
                    cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()

                # 创建新的消息对象，保持原有类型
                if hasattr(msg, 'type'):
                    if msg.type == "system":
                        cleaned_messages.append(SystemMessage(content=cleaned_content))
                    elif msg.type == "human":
                        cleaned_messages.append(HumanMessage(content=cleaned_content))
                    elif msg.type == "ai":
                        # 保留 AI 消息的 tool_calls 属性
                        ai_msg = AIMessage(content=cleaned_content)
                        if hasattr(msg, 'tool_calls') and msg.tool_calls:
                            # 也要清理 tool_calls 中的参数
                            cleaned_tool_calls = []
                            for tc in msg.tool_calls:
                                cleaned_tc = tc.copy() if isinstance(tc, dict) else {
                                    'name': tc.get('name', ''),
                                    'args': tc.get('args', {}),
                                    'id': tc.get('id', '')
                                }
                                # 清理工具调用参数
                                if 'args' in cleaned_tc:
                                    cleaned_tc['args'] = deep_clean_for_json(cleaned_tc['args'])
                                cleaned_tool_calls.append(cleaned_tc)
                            ai_msg.tool_calls = cleaned_tool_calls
                        cleaned_messages.append(ai_msg)
                    elif msg.type == "tool":
                        # 对于工具消息，保持原有结构但清理内容
                        tool_msg = ToolMessage(
                            content=cleaned_content,
                            name=getattr(msg, 'name', ''),
                            tool_call_id=getattr(msg, 'tool_call_id', '')
                        )
                        cleaned_messages.append(tool_msg)
                    else:
                        # 其他类型消息，尝试保持原有结构
                        cleaned_messages.append(msg)
                else:
                    cleaned_messages.append(msg)
            else:
                # 没有content的消息直接添加
                cleaned_messages.append(msg)

        except Exception as msg_e:
            print(f"⚠️ 消息 {i} 处理异常: {str(msg_e)}")
            # 如果某条消息处理失败，跳过它
            continue

    print(f"消息清理完成，原始消息数: {len(messages)}, 清理后消息数: {len(cleaned_messages)}")
    return cleaned_messages

def print_messages_in_log(messages: List[BaseMessage]):

    log_content = "\n".join([str(msg) for msg in messages])
    logger.info(log_content)

def get_last_show_message_id(messages: List[BaseMessage]):
    for message in reversed(messages):
        if not isinstance(message, ToolMessage):
            if not hasattr(message, "tool_calls"):
                return message.id
            elif hasattr(message, "tool_calls") and not message.tool_calls:
                return message.id
    return messages[-1].id