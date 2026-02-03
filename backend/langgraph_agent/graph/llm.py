import copy

from langgraph_agent.config import global_config

import os
import asyncio
import logging
import re

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from langgraph_agent.graph.state import AgentState

from copilotkit.langgraph import copilotkit_customize_config

try:
    import httpx
except ImportError:
    httpx = None



logger = logging.getLogger(__name__)

def get_llm_client(state: AgentState, config: RunnableConfig) -> (ChatOpenAI, str):
    """获取或创建LLM客户端（无缓存版本）"""
    print("\n=== 获取 LLM 客户端 ===")

    # model_name = (
    #     state.get("model")
    #     if "model" in state and state.get("model") is not None
    #     else config.get("configurable", {}).get("model_name", global_config.BASE_LLM)
    # )

    model_name = os.getenv("BASE_LLM", "deepseek-ai/DeepSeek-V3")
    # print("model_name:{}".format(model_name))

    # openai_api_key = config.get("configurable", {}).get("model_key", os.getenv("OPENAI_API_KEY"))
    openai_api_key = os.getenv("OPENAI_API_KEY")
    # print("openai_api_key:{}".format(openai_api_key))
    base_url = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

    if not model_name:
        model_name = global_config.BASE_LLM

    print(f"模型名称: {model_name}")
    print(f"Base URL: {base_url}")
    print(f"创建新的 LLM 客户端（无缓存）...")

    try:
        # 配置 SSL 验证（默认启用，可通过环境变量禁用）
        ssl_verify = os.getenv('OPENAI_SSL_VERIFY', 'true').lower() == 'true'
        
        # 创建 httpx 客户端配置（如果可用）
        http_client_kwargs = {}
        if httpx is not None:
            # ChatOpenAI 期望同步版 httpx.Client，传 AsyncClient 会触发类型校验错误
            http_client = httpx.Client(
                verify=ssl_verify,
                timeout=int(os.getenv('OPENAI_REQUEST_TIMEOUT', '300')),
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10
                )
            )
            http_client_kwargs['http_client'] = http_client
        
        # print("base_url:{}".format(base_url))
        # print("model_name:{}".format(model_name))
        # print("openai_api_key:{}".format(openai_api_key))
        client = ChatOpenAI(
            base_url=base_url,
            model=model_name,
            temperature=0.1,
            api_key=openai_api_key,
            model_kwargs={
                "extra_headers": {
                    "Authorization": f"Bearer {openai_api_key}"
                }
            },
            request_timeout=int(os.getenv('OPENAI_REQUEST_TIMEOUT', '300')),
            max_retries=int(os.getenv('OPENAI_MAX_RETRIES', '5')),
            **http_client_kwargs
        )
        
        
        print(f"[LLM客户端] ✅ 创建新的客户端成功，模型: {model_name}")
        return client, model_name

    except Exception as e:
        print(f"[LLM客户端] ❌ 创建客户端失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def build_messages_for_llm(model_name, messages):
    messages_for_llm = []


    # for msg in messages:
    #     if hasattr(msg, 'content'):
    #         # 确保内容可以被JSON序列化
    #         try:
    #             json.dumps({"content": msg.content})
    #             cleaned_messages.append(msg)
    #         except:
    #             # 如果序列化失败，创建清理后的消息
    #             cleaned_content = sanitize_string_for_json(msg.content, context="api")
    #             if hasattr(msg, 'type'):
    #                 if msg.type == "system":
    #                     cleaned_messages.append(SystemMessage(content=cleaned_content))
    #                 elif msg.type == "human":
    #                     cleaned_messages.append(HumanMessage(content=cleaned_content))
    #                 elif msg.type == "ai":
    #                     ai_msg = AIMessage(content=cleaned_content)
    #                     # 保留工具调用
    #                     if hasattr(msg, 'tool_calls') and msg.tool_calls:
    #                         ai_msg.tool_calls = msg.tool_calls
    #                     cleaned_messages.append(ai_msg)
    #     else:
    #         cleaned_messages.append(msg)

    # logger.info(f"Messages For LLM start: {messages}")

    for msg in messages:

        # 验证message中的name字段是否被设置
        if isinstance(msg, AIMessage) or isinstance(msg, ToolMessage):
            if not msg.name:
                logger.error("message的name字段未被正确设置")
                logger.error(f"有问题的msg: {msg}")

            if isinstance(msg, AIMessage):
                if not msg.name == "a2a_agent":
                    msg.content = f"Response from {msg.name}: " + msg.content
                messages_for_llm.append(
                    HumanMessage(
                        content=msg.content,
                        name=msg.name,
                        tool_calls=msg.tool_calls if msg.tool_calls else [],
                        additional_kwargs=msg.additional_kwargs if msg.additional_kwargs else {}
                    ))

            elif isinstance(msg, ToolMessage):
                msg.content = f"Response from {msg.name} tool: " + msg.content
                messages_for_llm.append(
                    HumanMessage(
                        content=msg.content,
                        name=msg.name,
                        additional_kwargs=msg.additional_kwargs if msg.additional_kwargs else {}
                    ))

        else:
            messages_for_llm.append(msg)

    if model_name and "Qwen3-235B" in model_name:
        messages[0].content += ' /no_think'

    # logger.info(f"Messages For LLM: {messages_for_llm}")

    return messages_for_llm


async def safe_llm_invoke(llm, config: RunnableConfig, model_name, messages, max_retries=3, hidden=False, disable_emit=False):
    """安全的LLM调用，包含重试逻辑"""
    for attempt in range(max_retries):
        try:
            # 在调用前再次验证消息格式
            messages_for_llm = build_messages_for_llm(model_name, copy.deepcopy(messages))
            # 调用LLM
            if hidden:
                config["tags"] = ["langsmith:hidden"]
                # mcp工具场景，需禁用llm自动emit。因为此时message不是实际调用mcp工具的参数。
                modified_config = copilotkit_customize_config(
                    config,
                    emit_messages=False if disable_emit else True,  # if you want to disable message streaming #
                    emit_tool_calls=False  # if you want to disable tool call streaming #
                )
                # print(f"safe_llm_invoke: {modified_config}")
            else:
                modified_config = copilotkit_customize_config(
                    config,
                    emit_messages=False if disable_emit else True,  # if you want to disable message streaming #
                    emit_tool_calls=False  # if you want to disable tool call streaming #
                )

            response = await llm.ainvoke(messages_for_llm, config=modified_config)
            # print(f"safe_llm_invoke: {modified_config}")

            return response

        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"LLM invoke error: {error_msg}")
            
            # 特殊处理 SSL 错误
            if "SSL" in error_msg or "ssl" in error_msg or "SSLError" in error_type:
                print(f"检测到 SSL 错误 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                if attempt < max_retries - 1:
                    # 等待一下再重试，SSL 错误可能是暂时的网络问题
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    # 最后一次重试失败，提供解决建议
                    raise Exception(
                        f"SSL 连接失败: {error_msg}\n"
                        "可能的解决方案:\n"
                        "1. 检查网络连接是否正常\n"
                        "2. 检查 OPENAI_BASE_URL 是否正确\n"
                        "3. 如果是自签名证书，可以设置 OPENAI_SSL_VERIFY=false（仅用于测试）\n"
                        "4. 检查防火墙或代理设置"
                    ) from e
            
            # 特殊处理连接关闭错误
            elif "Cannot send a request, as the client has been closed" in error_msg:
                print(f"检测到客户端已关闭错误 (尝试 {attempt + 1}/{max_retries})")
                # 这种情况下，我们无法在这里重新创建客户端
                # 因为客户端是在外部创建的，所以直接抛出异常
                # 让调用方处理
                raise Exception("LLM客户端已关闭，需要重新创建") from e

            # 处理其他JSON相关错误
            elif "delimiter" in error_msg or "JSON" in error_msg or "Expecting" in error_msg:
                print(f"JSON格式错误 (尝试 {attempt + 1}/{max_retries}): {error_msg}")
                if attempt < max_retries - 1:
                    # 等待一下再重试
                    await asyncio.sleep(1)
                    continue

            # 其他错误直接抛出
            raise

    raise Exception("LLM调用失败，超过最大重试次数")


LLM_ERROR_LIST = {
    "json": [
        "1. 用户输入包含特殊字符未正确转义",
        "2. 工具调用参数格式错误",
        "3. 系统prompt或消息包含格式错误的JSON",
        "4. 中文字符编码问题",
    ],
    "connection": [
        "1. 网络连接问题 - 检查网络连接是否正常",
        "2. API 端点不可访问 - 检查 Base URL 是否正确",
        "3. 防火墙或代理问题 - 检查是否有网络限制",
        "4. SSL/TLS 证书问题 - 尝试禁用 SSL 验证（仅用于测试）"
    ],
    "timeout": [
        "1. 请求超时 - 考虑增加超时时间",
        "2. 服务器响应缓慢 - 检查服务器负载",
        "3. 网络延迟高 - 检查网络质量"
    ],
    "authentication": [
        "1. API Key 无效或过期"
        "2. API Key 权限不足"
        "3. 认证头格式错误"
    ],
    "rate limit": [
        "1. API 调用频率超限",
        "2. 并发请求过多",
        "3. 配额已用完"
    ],
    "other": [
        "1. API 服务异常",
        "2. 请求格式错误",
        "3. 模型不存在或不可用"
    ]
}


def get_error_msg(type: str) -> str:
    if type == "json":
        return "\n🔍 检测到JSON格式错误，执行专项处理:\n" + "\n".join(LLM_ERROR_LIST[type])
    elif type in ("connection", "timeout", "authentication", "rate limit"):
        return "\n可能的原因:\n" + "\n".join(LLM_ERROR_LIST[type])
    elif type == "other":
        return "\n其他可能的原因:\n" + "\n".join(LLM_ERROR_LIST[type])
    else:
        return "未知错误类型"

def remove_text_between_delimiters(text, start_delim, end_delim):
    '''
    本函数用于删除一个字符串中两个指定分隔符之间的内容。目前用于清除qwen3-235b回复内容中的<think></think>标签
    Args:
        text: 原始字符串
        start_delim: 分隔符（左）
        end_delim: 分隔符（右）
    Returns:
    '''
    start_escaped = re.escape(start_delim)
    end_escaped = re.escape(end_delim)
    pattern = f'{start_escaped}.*?{end_escaped}'
    return re.sub(pattern, '', text, flags=re.DOTALL)
