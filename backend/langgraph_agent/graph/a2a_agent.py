import asyncio
import json
import logging
import os
import traceback
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

import aiohttp
from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from python_a2a import Message, TextContent, MessageRole, A2AClient

from .state import AgentState

# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class A2AAgentInfo:
    """A2A 智能体信息数据类 - 简化版本"""
    agent_id: str  # A2A 服务 ID (从 agent_id 字段获取)
    name: str  # 智能体名称
    description: str  # 功能描述 (从 desc 字段获取)
    base_url: str  # A2A 服务基础URL (从环境变量获取)
    user_id: str = ""  # 用户ID (从 user_id 字段获取)


@dataclass
class A2AExecutionResult:
    """A2A 执行结果数据类"""
    type: str  # 响应类型: text/form_input/skill_start/skill_end
    content: Any  # 响应内容
    final: bool  # 是否最终响应
    status: bool  # 执行状态
    session_id: str  # 会话ID
    task_id: str = ""  # 任务ID
    error_msg: str = ""  # 错误信息

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "type": self.type,
            "content": self.content,
            "final": self.final,
            "status": self.status,
            "session_id": self.session_id,
            "task_id": self.task_id,
            "error_msg": self.error_msg
        }


class A2AHttpClient2:

    def __init__(self, base_url: str, timeout: int = None):
        base_url = base_url.rstrip('/')
        self._client: Optional[A2AClient] = None
        self._base_url = base_url
        self._timeout = timeout

    async def _ensure_client(self) -> A2AClient:
        """确保客户端已创建（在线程中创建，避免阻塞）"""
        if self._client is None:
            def _create_client():
                return A2AClient(endpoint_url=self._base_url, timeout=self._timeout)
            self._client = await asyncio.to_thread(_create_client)
        return self._client

    async def _get_agent_card(self) -> Optional[Any]:
        """获取agent card，复用客户端或创建新客户端"""
        # 如果客户端已存在，尝试直接使用
        if self._client is not None:
            try:
                card = await asyncio.to_thread(self._client.get_agent_card)
                if card and card.name != "Unknown Agent" and card.description != "Agent card not available":
                    return card
            except Exception:
                self._client = None

        # 在单独的线程中创建客户端并获取card
        def _get_card_sync():
            client = A2AClient(endpoint_url=self._base_url, timeout=self._timeout)
            card = client.get_agent_card()
            return client, card

        client, card = await asyncio.to_thread(_get_card_sync)

        # 如果获取成功，保存客户端实例
        if card and card.name != "Unknown Agent" and card.description != "Agent card not available":
            self._client = client

        return card

    async def get_a2a_name(self) -> str:
        """获取A2A智能体名称"""
        try:
            card = await self._get_agent_card()
            return card.name if card else "Unknown Agent"
        except Exception as e:
            logger.warning(f"获取A2A名称失败: {str(e)}")
            return "Unknown Agent"

    async def get_a2a_desc(self) -> str:
        """获取A2A智能体描述"""
        try:
            card = await self._get_agent_card()
            return card.description if card else "Agent card not available"
        except Exception as e:
            logger.warning(f"获取A2A描述失败: {str(e)}")
            return "Agent card not available"

    async def call_a2a_agent(self, agent_id: str, session_id: str,
                             messages: List[Dict], user_id: str = "") -> A2AExecutionResult:
        """
         调用 A2A 智能体

         Args:
             agent_id: A2A 智能体ID
             session_id: 会话ID
             messages: 消息列表
             user_id: 用户ID

         Returns:
             A2AExecutionResult: 执行结果
         """
        # 确保客户端已创建
        await self._ensure_client()

        # 创建带有必需 role 参数的消息
        message = Message(
            content=TextContent(text=messages[0]['content']),
            role=MessageRole.USER
        )

        # 检查流式支持（异步方法，直接await）
        stream_flag = await self._client.check_streaming_support()

        try:
            if stream_flag:
                return await self._handle_sse_response(message, session_id)
            else:
                return await self._handle_json_response(message, session_id)
        except Exception as e:
            logger.error(f"A2A 请求异常: {str(e)}", exc_info=True)
            return A2AExecutionResult(
                type="error",
                content="",
                final=True,
                status=False,
                session_id=session_id,
                error_msg=f"请求异常: {str(e)}"
            )

    async def _handle_json_response(self, message: Message, session_id: str) -> A2AExecutionResult:
        """
        处理普通 JSON 响应

        Args:
            message: A2A 消息对象
            session_id: 会话ID

        Returns:
            A2AExecutionResult: 处理后的结果
        """
        try:
            await self._ensure_client()

            # 包装同步的 send_message 调用
            def _send_message():
                return self._client.send_message(message)
            data = await asyncio.to_thread(_send_message)

            return A2AExecutionResult(
                type='text',
                content=data,
                # 兼容 'final' 和 'finished' 两个字段名
                final=True,
                status=True,
                session_id=session_id,
                task_id='',
                error_msg=''
            )

        except Exception as e:
            logger.error(f"处理 JSON 响应异常: {str(e)}")
            return A2AExecutionResult(
                type="error",
                content="",
                final=True,
                status=False,
                session_id=session_id,
                error_msg=f"JSON 处理异常: {str(e)}"
            )

    async def _handle_sse_response(self, message: Message, session_id: str) -> A2AExecutionResult:
        """
        处理 SSE 流式响应 - 简化版本
        只收集所有接收到的内容，当流结束时返回结果
        """
        all_content = ""  # 累积所有内容

        def _process_sse_line(line: str) -> Tuple[str, bool]:
            """处理SSE行，返回(内容, 是否结束)"""
            line = line.strip()
            if line.startswith('data:'):
                data_content = line[5:].lstrip()
                if data_content == '[DONE]':
                    return "", True
                if data_content and data_content != '[DONE]':
                    return data_content, False
            elif line and not (line == '' or line.startswith(':')):
                return line, False
            return "", False

        try:
            # 尝试作为异步迭代器使用 stream_response
            try:
                async for line in self._client.stream_response(message):
                    content, is_done = _process_sse_line(line)
                    if is_done:
                        break
                    if content:
                        all_content += content
            except (TypeError, AttributeError):
                # 如果是同步迭代器，在线程中运行并转换为异步
                def _get_stream():
                    return list(self._client.stream_response(message))
                lines = await asyncio.to_thread(_get_stream)
                for line in lines:
                    content, is_done = _process_sse_line(line)
                    if is_done:
                        break
                    if content:
                        all_content += content

        except asyncio.TimeoutError:
            logger.error("SSE流读取超时")
            return A2AExecutionResult(
                type="error",
                content="",
                final=True,
                status=False,
                session_id=session_id,
                error_msg="SSE流读取超时，A2A服务响应时间过长"
            )

        except Exception as e:
            logger.error(f"处理 SSE 响应异常: {str(e)}")
            return A2AExecutionResult(
                type="error",
                content="",
                final=True,
                status=False,
                session_id=session_id,
                error_msg=f"SSE 处理异常: {str(e)}"
            )

        # 流结束，返回结果
        if all_content.strip():
            return A2AExecutionResult(
                type="text",
                content=all_content,
                final=True,
                status=True,
                session_id=session_id,
                error_msg=""
            )
        else:
            return A2AExecutionResult(
                type="text",
                content="",
                final=True,
                status=False,
                session_id=session_id,
                error_msg="未收到SSE响应内容"
            )


class A2AHttpClient:
    """A2A HTTP 客户端，处理与 A2A 服务的通信"""

    def __init__(self, base_url: str, timeout: int = None):
        """
        初始化 A2A HTTP 客户端

        Args:
            base_url: A2A 服务基础URL
            timeout: 请求超时时间（秒），如果为None则从环境变量读取
        """
        self.base_url = base_url.rstrip('/')

        # 从环境变量读取配置，提供默认值
        if timeout is None:
            timeout = int(os.environ.get("A2A_TIMEOUT", "600"))  # 默认10分钟

        connect_timeout = int(os.environ.get("A2A_CONNECT_TIMEOUT", "150"))  # 连接超时
        read_timeout = int(os.environ.get("A2A_READ_TIMEOUT", "300"))  # 读取超时

        # 设置不同类型的超时时间
        self.timeout = aiohttp.ClientTimeout(
            total=timeout,  # 总超时时间
            connect=connect_timeout,  # 连接超时
            sock_read=read_timeout,  # 单次读取超时
            sock_connect=connect_timeout  # socket连接超时
        )
        self.api_url = f"{self.base_url}/mae/api/v1.0/rest/a2aChat"

        logger.info(f"A2A客户端初始化完成: 总超时={timeout}s, 连接超时={connect_timeout}s, 读取超时={read_timeout}s")

    async def call_a2a_agent(self, agent_id: str, session_id: str,
                             messages: List[Dict], user_id: str = "") -> A2AExecutionResult:
        """
        调用 A2A 智能体

        Args:
            agent_id: A2A 智能体ID
            session_id: 会话ID
            messages: 消息列表
            user_id: 用户ID

        Returns:
            A2AExecutionResult: 执行结果
        """
        try:
            # 构造请求数据
            payload = {
                "agentId": agent_id,
                "sessionId": session_id,
                "userId": user_id,
                "messages": messages
            }

            logger.info(f"调用 A2A 智能体: {agent_id}")
            logger.info(f"请求URL: {self.api_url}")
            logger.info(f"请求数据: {json.dumps(payload, indent=2, ensure_ascii=False)}")

            # 发送 POST 请求
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'text/event-stream'  # 支持 SSE
                }

                async with session.post(
                        self.api_url,
                        json=payload,
                        headers=headers
                ) as response:

                    logger.info(f"响应状态码: {response.status}")

                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"A2A 请求失败: {response.status}, 内容: {error_text}")
                        return A2AExecutionResult(
                            type="error",
                            content="",
                            final=True,
                            status=False,
                            session_id=session_id,
                            error_msg=f"HTTP {response.status}: {error_text}"
                        )

                    # 检查是否是 SSE 响应
                    content_type = response.headers.get('content-type', '')
                    if 'text/event-stream' in content_type:
                        return await self._handle_sse_response(response, session_id)
                    else:
                        # 处理普通 JSON 响应
                        return await self._handle_json_response(response, session_id)

        except asyncio.TimeoutError:
            logger.error("A2A 请求超时")
            return A2AExecutionResult(
                type="error",
                content="",
                final=True,
                status=False,
                session_id=session_id,
                error_msg="请求超时"
            )
        except Exception as e:
            logger.error(f"A2A 请求异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return A2AExecutionResult(
                type="error",
                content="",
                final=True,
                status=False,
                session_id=session_id,
                error_msg=f"请求异常: {str(e)}"
            )

    async def _handle_sse_response(self, response: aiohttp.ClientResponse,
                                   session_id: str) -> A2AExecutionResult:
        """
        处理 SSE 流式响应

        Args:
            response: HTTP 响应对象
            session_id: 会话ID

        Returns:
            A2AExecutionResult: 处理后的结果
        """
        logger.info("处理 SSE 流式响应")
        final_result = None
        content_parts = []
        all_lines = []  # 记录所有接收到的原始行

        try:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                all_lines.append(line)  # 记录原始行用于调试

                logger.debug(f"收到原始SSE行: {line}")

                # 处理标准SSE格式：data: xxx 或 data:xxx（兼容有无空格）
                if line.startswith('data:'):
                    # 移除 'data:' 前缀，同时处理可能存在的空格
                    data_str = line[5:].lstrip()  # 移除 'data:' 并去除前导空格

                    if data_str == '[DONE]':
                        logger.debug("收到SSE结束标记: [DONE]")
                        break

                    try:
                        data = json.loads(data_str)
                        logger.debug(f"收到 SSE 数据: {data}")

                        # 解析响应数据
                        result_type = data.get('type', 'text')
                        content = data.get('content', '')
                        # 兼容 'final' 和 'finished' 两个字段名
                        final = data.get('final', data.get('finished', False))
                        status = data.get('status', True)
                        task_id = data.get('taskId', '')

                        # 添加详细的调试日志
                        logger.debug(
                            f"解析后的数据 - type: {result_type}, content: '{content}', final: {final}, status: {status}")
                        logger.debug(
                            f"字段检查 - 'final'字段: {data.get('final')}, 'finished'字段: {data.get('finished')}, 最终final值: {final}, 类型: {type(final)}")

                        # 收集内容
                        if content:
                            content_parts.append(str(content))
                            logger.debug(f"添加内容片段: '{content}', 当前片段数: {len(content_parts)}")
                        else:
                            logger.debug(f"内容为空，跳过收集")

                        # 如果是最终响应，记录下来
                        if final:
                            final_result = A2AExecutionResult(
                                type=result_type,
                                content=content,
                                final=final,
                                status=status,
                                session_id=session_id,
                                task_id=task_id
                            )
                            logger.info(f"收到最终SSE响应: {final_result}")
                            break
                        else:
                            logger.debug(f"当前不是最终响应，继续处理下一行")

                    except json.JSONDecodeError as e:
                        logger.warning(f"解析 SSE JSON数据失败: {data_str}, 错误: {str(e)}")
                        continue

                # 处理非标准格式：直接是JSON数据（无data:前缀）
                elif line.startswith('{') and line.endswith('}'):
                    try:
                        data = json.loads(line)
                        logger.info(f"收到直接JSON数据: {data}")

                        result_type = data.get('type', 'text')
                        content = data.get('content', '')
                        # 兼容 'final' 和 'finished' 两个字段名
                        final = data.get('final', data.get('finished', False))
                        status = data.get('status', True)
                        task_id = data.get('taskId', '')

                        if content:
                            content_parts.append(str(content))

                        if final:
                            final_result = A2AExecutionResult(
                                type=result_type,
                                content=content,
                                final=final,
                                status=status,
                                session_id=session_id,
                                task_id=task_id
                            )
                            logger.info(f"收到最终直接JSON响应: {final_result}")
                            break

                    except json.JSONDecodeError as e:
                        logger.warning(f"解析直接JSON数据失败: {line}, 错误: {str(e)}")
                        continue

                # 忽略空行和注释行
                elif line == '' or line.startswith(':'):
                    continue

                # 其他格式的行，记录但不处理
                else:
                    logger.debug(f"收到未识别格式的SSE行: {line}")

            logger.info(f"SSE流处理完成，共处理 {len(all_lines)} 行数据")

        except asyncio.TimeoutError:
            logger.error("SSE流读取超时")
            return A2AExecutionResult(
                type="error",
                content="",
                final=True,
                status=False,
                session_id=session_id,
                error_msg="SSE流读取超时，A2A服务响应时间过长"
            )

        except Exception as e:
            logger.error(f"处理 SSE 响应异常: {str(e)}")
            import traceback
            traceback.print_exc()

            return A2AExecutionResult(
                type="error",
                content="",
                final=True,
                status=False,
                session_id=session_id,
                error_msg=f"SSE 处理异常: {str(e)}"
            )

        # 处理结果
        # 调试信息：记录所有接收到的原始数据
        logger.info(f"SSE响应总共接收到 {len(all_lines)} 行数据")
        logger.info(f"收集到 {len(content_parts)} 个内容片段")
        # 只输出前10行作为调试信息，避免日志过长
        logger.debug(f"前10行SSE原始数据: {all_lines[:10]}")

        # 调试信息：检查final_result的状态
        logger.info(f"SSE处理循环结束后，final_result状态: {final_result}")

        # 如果没有收到最终结果，使用收集的内容组合
        if final_result is None:
            if content_parts:
                combined_content = "".join(content_parts)  # 直接连接，不用换行
                final_result = A2AExecutionResult(
                    type="text",
                    content=combined_content,
                    final=True,
                    status=True,  # 有内容就认为成功
                    session_id=session_id,
                    error_msg=""
                )
                logger.info(f"使用收集的内容组合最终结果: {len(combined_content)} 字符")
            else:
                # 记录详细的调试信息
                debug_info = f"原始SSE行数: {len(all_lines)}, 前10行: {all_lines[:10]}"
                logger.error(f"未收到任何有效内容: {debug_info}")

                final_result = A2AExecutionResult(
                    type="text",
                    content="未收到有效响应",
                    final=True,
                    status=False,
                    session_id=session_id,
                    error_msg=f"未收到明确的最终响应，{debug_info}"
                )
        else:
            # 如果收到了最终结果，但内容为空，则使用收集的内容片段
            if not final_result.content and content_parts:
                combined_content = "".join(content_parts)  # 直接连接，不用换行
                final_result = A2AExecutionResult(
                    type=final_result.type,
                    content=combined_content,
                    final=final_result.final,
                    status=final_result.status,
                    session_id=final_result.session_id,
                    task_id=final_result.task_id,
                    error_msg=final_result.error_msg
                )
                logger.info(f"最终结果内容为空，使用收集的内容片段: {len(combined_content)} 字符")

        logger.info(f"SSE 处理完成: {final_result}")
        return final_result

    async def _handle_json_response(self, response: aiohttp.ClientResponse,
                                    session_id: str) -> A2AExecutionResult:
        """
        处理普通 JSON 响应

        Args:
            response: HTTP 响应对象
            session_id: 会话ID

        Returns:
            A2AExecutionResult: 处理后的结果
        """
        try:
            data = await response.json()
            logger.info(f"收到 JSON 响应: {data}")

            return A2AExecutionResult(
                type=data.get('type', 'text'),
                content=data.get('content', ''),
                # 兼容 'final' 和 'finished' 两个字段名
                final=data.get('final', data.get('finished', True)),
                status=data.get('status', True),
                session_id=session_id,
                task_id=data.get('taskId', ''),
                error_msg=data.get('errorMsg', '')
            )

        except Exception as e:
            logger.error(f"处理 JSON 响应异常: {str(e)}")
            return A2AExecutionResult(
                type="error",
                content="",
                final=True,
                status=False,
                session_id=session_id,
                error_msg=f"JSON 处理异常: {str(e)}"
            )


async def a2a_agent_node(state: AgentState, config: RunnableConfig, agent_info: A2AAgentInfo) -> Dict:
    """
    A2A 智能体节点执行函数 - 优化版本

    Args:
        state: 智能体状态
        config: 运行配置
    """
    node_name = "a2a_agent"
    logger.info(f"🤖 执行 A2A 智能体节点: {agent_info.name}")

    try:
        # 1. 获取或创建 sessionId
        session_key = f"a2a_{agent_info.agent_id}"
        session_id = state["a2a_sessions"].get(session_key)
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:8]}"
            state["a2a_sessions"][session_key] = session_id
            logger.info(f"✅ 为 A2A 智能体 {agent_info.name} 创建新会话: {session_id}")
        else:
            logger.info(f"♻️ 使用现有会话: {session_id}")

        # 2. 获取Supervisor生成的任务指令（优先使用）或用户消息
        task_instruction = get_task_instruction_from_supervisor(state, agent_info)
        logger.info(f"📝 为智能体 {agent_info.name} 获取的任务指令: {task_instruction}")

        # 3. 构造 A2A 消息格式
        messages = [{
            "type": "text",
            "content": task_instruction
        }]

        # 4. 调用 A2A API（带重试机制）
        logger.info(f"🔗 调用 A2A 智能体 API: {agent_info.base_url}")

        # 重试配置（从环境变量读取）
        max_retries = int(os.environ.get("A2A_MAX_RETRIES", "5"))
        retry_count = 0
        result = None

        logger.info(f"A2A调用配置: 最大重试次数={max_retries}")

        while retry_count < max_retries:
            try:
                client = A2AHttpClient2(agent_info.base_url)
                result = await client.call_a2a_agent(
                    agent_info.agent_id,
                    session_id,
                    messages,
                    agent_info.user_id
                )

                # 如果成功或者不是超时错误，跳出重试循环
                if result.status or "超时" not in result.error_msg:
                    break

                # 如果是超时错误，进行重试
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count  # 指数退避：2, 4, 8秒
                    logger.warning(f"A2A调用超时，等待 {wait_time} 秒后重试 (尝试 {retry_count + 1}/{max_retries})")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"A2A调用失败，已达到最大重试次数: {result.error_msg}")

            except Exception as e:
                retry_count += 1
                logger.error(f"A2A调用异常 (尝试 {retry_count}/{max_retries}): {str(e)}")

                if retry_count < max_retries:
                    wait_time = 2 ** retry_count
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                else:
                    # 创建错误结果
                    result = A2AExecutionResult(
                        type="error",
                        content="",
                        final=True,
                        status=False,
                        session_id=session_id,
                        error_msg=f"A2A调用异常，已达到最大重试次数: {str(e)}"
                    )
                    break

        logger.info(f"📊 A2A 执行结果: {result.status}, 类型: {result.type}")
        if not result.status:
            logger.warning(f"A2A 执行失败原因: {result.error_msg}")

        # 5. 处理结果并更新状态
        if result.status:
            # 成功：添加 AI 响应消息
            ai_content = format_a2a_response(result, agent_info.name)

            message_id = str(uuid.uuid4())
            # 先临时提交消息，用于向用户快速展示结果
            await adispatch_custom_event(
                "copilotkit_manually_emit_message",
                {
                    "message": ai_content,
                    "message_id": message_id,
                    "role": "assistant"
                },
                config=config,
            )
            await asyncio.sleep(0.02)

            # 再永久保存消息
            ai_message = AIMessage(id=message_id, content=ai_content, name=node_name)
            state["messages"].append(ai_message)
            state["inner_messages"].append(ai_message)

            state["last_a2a_result"] = ai_content

            logger.info(f"✅ A2A 智能体 {agent_info.name} 执行成功")

            # 🔥 关键修复：当前步骤完成，但不结束整个工作流，让Supervisor决定下一步
            state["current_step_completed"] = True

            # 🔥 在节点内部递增步骤索引（正确的地方）
            current_step_index = state.get("current_step_index", 0)
            state["current_step_index"] = current_step_index + 1
            logger.info(f"🔄 步骤索引已递增: {current_step_index} → {current_step_index + 1}")

            # 保存执行结果供后续步骤使用
            if "execution_results" not in state:
                state["execution_results"] = {}
            state["execution_results"][agent_info.agent_id] = {
                "agent_name": agent_info.name,
                "result": ai_content,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "step_id": current_step_index + 1  # 记录这是第几步的结果
            }

        else:
            # 失败：添加错误消息
            error_content = format_a2a_error(result, agent_info.name)
            error_message = AIMessage(content=error_content, name=node_name)

            state["messages"].append(error_message)
            state["inner_messages"].append(error_message)

            logger.error(f"❌ A2A 智能体 {agent_info.name} 执行失败: {result.error_msg}")

            # 记录A2A失败次数
            state["a2a_failure_count"] = state.get("a2a_failure_count", 0) + 1
            state["last_a2a_result"] = f"A2A智能体执行失败: {result.error_msg}"

            # 🚨 关键修复：记录失败的智能体到failed_a2a_agents
            failed_agents = state.get("failed_a2a_agents", [])
            failed_route_id = f"a2a_{agent_info.agent_id}"
            if failed_route_id not in failed_agents:
                failed_agents.append(failed_route_id)
                state["failed_a2a_agents"] = failed_agents
                logger.warning(f"🚫 记录失败智能体: {failed_route_id} ({agent_info.name})")

            # A2A执行失败时的处理策略 - 🔥 修复：移除A2A层面的直接fallback逻辑
            # 所有情况都回到supervisor，由supervisor决定是否fallback

            #  失败时标记当前步骤完成，记录失败结果，让supervisor决定下一步
            current_step_index = state.get("current_step_index", 0)  # 在使用前获取变量
            state["current_step_completed"] = True
            if "execution_results" not in state:
                state["execution_results"] = {}
            state["execution_results"][agent_info.agent_id] = {
                "agent_name": agent_info.name,
                "result": f"执行失败: {result.error_msg}",
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "step_id": current_step_index + 1  # 记录这是第几步的结果
            }
            logger.info(f"🚫 A2A 智能体执行失败，标记当前步骤完成，让Supervisor决定下一步")

            # 6. 返回到 Supervisor 进行下一轮决策
            return {
                "messages": state["messages"],
                "inner_messages": state["inner_messages"],
                "logs": state["logs"],
                "a2a_sessions": state["a2a_sessions"],
                "last_a2a_result": state.get("last_a2a_result"),
                "route_to_a2a": None,  # 清除路由决策
                "completed": False,  # 🔥 关键修复：不在A2A层面设置completed，由supervisor决定
                "a2a_failure_count": state.get("a2a_failure_count", 0),
                # 🔥 关键修复：保持多步骤工作流状态
                "workflow_plan": state.get("workflow_plan"),
                "current_step_index": state.get("current_step_index", 0),
                "execution_results": state.get("execution_results", {}),
                "current_step_completed": state.get("current_step_completed", False),
                # 🔥 关键修复：保留supervisor决策信息
                "supervisor_decision": state.get("supervisor_decision", {})
            }

        # 6. 返回到 Supervisor 进行下一轮决策
        return {
            "messages": state["messages"],
            "inner_messages": state["inner_messages"],
            "logs": state["logs"],
            "a2a_sessions": state["a2a_sessions"],
            "last_a2a_result": state.get("last_a2a_result"),
            "route_to_a2a": None,  # 清除路由决策
            "completed": state.get("completed", False),
            "a2a_failure_count": state.get("a2a_failure_count", 0),
            # 🔥 关键修复：保持多步骤工作流状态
            "workflow_plan": state.get("workflow_plan"),
            "current_step_index": state.get("current_step_index", 0),
            "execution_results": state.get("execution_results", {}),
            "current_step_completed": state.get("current_step_completed", False),
            # 🔥 关键修复：保留supervisor决策信息
            "supervisor_decision": state.get("supervisor_decision", {})
        }

    except Exception as e:
        logger.error(f"💥 A2A 智能体节点执行异常: {str(e)}")
        import traceback
        traceback.print_exc()

        # 添加异常错误消息
        error_message = AIMessage(content=f"A2A 智能体 {agent_info.name} 执行异常: {str(e)}", name=node_name)
        state["messages"].append(error_message)
        state["inner_messages"].append(error_message)

        # 记录异常失败次数和状态
        state["a2a_failure_count"] = state.get("a2a_failure_count", 0) + 1
        state["last_a2a_result"] = f"A2A智能体执行异常: {str(e)}"

        # 🚨 关键修复：记录失败的智能体到failed_a2a_agents
        failed_agents = state.get("failed_a2a_agents", [])
        failed_route_id = f"a2a_{agent_info.agent_id}"
        if failed_route_id not in failed_agents:
            failed_agents.append(failed_route_id)
            state["failed_a2a_agents"] = failed_agents
            logger.warning(f"🚫 记录异常失败智能体: {failed_route_id} ({agent_info.name})")

        # 🔥 关键修复：移除A2A层面的异常处理逻辑，统一由supervisor处理
        # 异常时标记当前步骤完成，记录异常结果，让supervisor决定下一步
        current_step_index = state.get("current_step_index", 0)  # 在使用前定义变量
        state["current_step_completed"] = True
        if "execution_results" not in state:
            state["execution_results"] = {}
        state["execution_results"][agent_info.agent_id] = {
            "agent_name": agent_info.name,
            "result": f"执行异常: {str(e)}",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "step_id": current_step_index + 1  # 记录这是第几步的结果
        }
        logger.info(f"🚫 A2A 智能体执行异常，标记当前步骤完成，让Supervisor决定下一步")

        # 🔥 关键修复：无论异常与否，都统一返回到Supervisor
        return {
            "messages": state["messages"],
            "inner_messages": state["inner_messages"],
            "logs": state["logs"],
            "a2a_sessions": state["a2a_sessions"],
            "route_to_a2a": None,  # 清除路由决策
            "last_a2a_result": state["last_a2a_result"],
            "a2a_failure_count": state["a2a_failure_count"],
            "completed": False,  # 🔥 关键修复：不在A2A层面设置completed，由supervisor决定
            # 🔥 关键修复：异常时也要保持多步骤工作流状态
            "workflow_plan": state.get("workflow_plan"),
            "current_step_index": state.get("current_step_index", 0),
            "execution_results": state.get("execution_results", {}),
            "current_step_completed": state.get("current_step_completed", False),
            # 🔥 关键修复：保留supervisor决策信息
            "supervisor_decision": state.get("supervisor_decision", {})
        }


def create_a2a_agent_info_from_config(config: Dict[str, Any]) -> A2AAgentInfo:
    """
    从配置字典创建 A2A 智能体信息 - 适配新格式

    Args:
        config: 配置字典，包含 agent_id, name, desc, user_id

    Returns:
        A2AAgentInfo: A2A 智能体信息对象
    """
    # 字段映射处理
    base_url = config.get("base_url", "")
    agent_id = config.get("agent_id") or config.get("agent_ID") or config.get("agentId", "")
    name = config.get("name", "")
    description = config.get("desc") or config.get("description", "")
    user_id = config.get("user_id") or config.get("userId", "")

    return A2AAgentInfo(
        agent_id=agent_id,
        name=name,
        description=description,
        base_url=base_url,
        user_id=user_id
    )


# 全局缓存，避免重复解析和日志打印
_global_a2a_cache = {
    "configs": None,
    "agents": None,
    "last_config_hash": None
}


def _get_config_hash(a2a_configs: List[Dict]) -> str:
    """计算配置的哈希值，用于检测变化"""
    import hashlib
    import json
    config_str = json.dumps(a2a_configs, sort_keys=True)
    return hashlib.md5(config_str.encode()).hexdigest()


def get_a2a_agents_from_state(state: AgentState) -> List[A2AAgentInfo]:
    """
    从状态中获取 A2A 智能体配置并转换为 A2AAgentInfo 对象
    统一处理多个可能的数据来源

    Args:
        state: 智能体状态

    Returns:
        List[A2AAgentInfo]: A2A 智能体信息列表
    """
    global _global_a2a_cache

    # 按优先级尝试从多个位置获取配置
    a2a_configs = []

    # 优先级1: 直接从状态的 a2a_agents 字段获取
    if state.get("a2a_agents"):
        a2a_configs = state["a2a_agents"]

    # 优先级2: 从 input 字段获取
    elif state.get("input", {}).get("a2a_agents"):
        a2a_configs = state["input"]["a2a_agents"]

    # 优先级3: 从 input_data 字段获取
    elif state.get("input_data", {}).get("a2a_agents"):
        a2a_configs = state["input_data"]["a2a_agents"]

    # 如果还没找到，检查是否有嵌套的配置结构
    else:
        # 检查 input.input.a2a_agents（支持嵌套结构）
        input_section = state.get("input", {})
        if isinstance(input_section, dict) and "input" in input_section:
            nested_input = input_section["input"]
            if isinstance(nested_input, dict) and "a2a_agents" in nested_input:
                a2a_configs = nested_input["a2a_agents"]

    # 🔧 检查全局缓存，避免重复解析和日志打印
    if a2a_configs:
        config_hash = _get_config_hash(a2a_configs)

        # 如果配置没有变化，使用缓存
        if (_global_a2a_cache["last_config_hash"] == config_hash and
                _global_a2a_cache["agents"] is not None):
            logger.debug(f"使用缓存的 A2A 智能体配置: {len(_global_a2a_cache['agents'])} 个")
            return _global_a2a_cache["agents"]

        # 配置有变化或首次加载，重新解析
        logger.info(f"从状态获取到 {len(a2a_configs)} 个 A2A 智能体配置")
    else:
        logger.warning("未找到 A2A 智能体配置")
        return []

    # 转换为 A2AAgentInfo 对象
    a2a_agents = []
    for i, config in enumerate(a2a_configs):
        try:
            # 验证配置完整性
            if not validate_a2a_config(config):
                logger.warning(f"A2A 智能体配置 {i} 验证失败，跳过: {config}")
                continue

            agent_info = create_a2a_agent_info_from_config(config)
            a2a_agents.append(agent_info)
            logger.info(f"✓ 加载 A2A 智能体: {agent_info.name} (ID: {agent_info.agent_id})")

        except Exception as e:
            logger.error(f"✗ 创建 A2A 智能体信息失败: {config}, 错误: {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    logger.info(f"总共成功加载了 {len(a2a_agents)} 个 A2A 智能体")

    # 输出加载的智能体详情
    for agent in a2a_agents:
        logger.info(f"  - {agent.name} (ID: {agent.agent_id}, URL: {agent.base_url})")
        logger.info(f"    描述: {agent.description}")

    # 🔧 更新全局缓存
    _global_a2a_cache["configs"] = a2a_configs
    _global_a2a_cache["agents"] = a2a_agents
    _global_a2a_cache["last_config_hash"] = _get_config_hash(a2a_configs)

    return a2a_agents


def validate_a2a_config(config: Dict[str, Any]) -> bool:
    """
    验证 A2A 智能体配置的完整性 - 适配新格式

    Args:
        config: A2A 智能体配置字典

    Returns:
        bool: 配置是否有效
    """
    required_fields = ["name"]  # name是必需的

    # 检查必需字段
    for field in required_fields:
        if field not in config or not config[field]:
            logger.error(f"A2A 配置缺少必需字段或字段为空: {field}")
            return False

    # 检查agent_id字段（支持两种格式）
    agent_id = config.get("agent_id") or config.get("agent_ID") or config.get("agentId")
    if not agent_id:
        logger.error("A2A 配置缺少必需字段: agent_id")
        return False

    # 检查desc字段（支持两种格式）
    desc = config.get("desc") or config.get("description")
    if not desc:
        logger.error("A2A 配置缺少必需字段: desc 或 description")
        return False

    base_url = config.get("base_url") or config.get("baseUrl")
    if not base_url:
        logger.error("A2A 配置缺少必需字段: base_url")
        return False

    # 标准化字段名（确保使用新格式）
    config["agent_id"] = agent_id
    config["desc"] = desc
    config["base_url"] = base_url

    return True


def get_task_instruction_from_supervisor(state: AgentState, agent_info: A2AAgentInfo) -> str:
    """
    获取Supervisor生成的任务指令，如果没有则使用fallback逻辑

    Args:
        state: 智能体状态
        agent_info: A2A智能体信息

    Returns:
        str: 任务指令
    """
    # 1. 优先使用Supervisor决策中的task_instruction
    # supervisor_decision = state.get("supervisor_decision", {})
    # task_instruction = supervisor_decision.get("task_instruction", "")
    task_instruction = state.get("sub_task", "")

    if task_instruction and task_instruction.strip():
        logger.info(f"使用Supervisor生成的任务指令，长度: {len(task_instruction)} 字符")
        return task_instruction.strip()

    # 2. 如果没有Supervisor生成的指令，使用简化的fallback逻辑
    logger.warning("Supervisor未生成任务指令，使用fallback逻辑")
    return generate_fallback_task_instruction(state, agent_info)


def generate_fallback_task_instruction(state: AgentState, agent_info: A2AAgentInfo) -> str:
    """
    Fallback任务指令生成逻辑（当Supervisor未生成时使用）

    Args:
        state: 智能体状态
        agent_info: A2A智能体信息

    Returns:
        str: 简化的任务指令
    """
    user_message = extract_latest_user_message(state)
    agent_name = agent_info.name
    agent_desc = agent_info.description

    # 简化的任务指令（避免过度复杂化）
    task_instruction = f"""作为专业的{agent_name}，请处理以下任务：

**用户请求**: {user_message}

**您的专长**: {agent_desc}

**任务要求**: 请根据您的专业能力提供高质量的服务和解决方案。"""

    logger.info(f"生成fallback任务指令，长度: {len(task_instruction)} 字符")
    return task_instruction


# 注意：原来的硬编码任务指令生成函数已移除
# 现在使用Supervisor智能生成的任务指令，具备更强的扩展性和适应性

def extract_latest_user_message(state: AgentState) -> str:
    """
    从状态中提取最新的用户消息

    Args:
        state: 智能体状态

    Returns:
        str: 最新的用户消息内容
    """
    # 1. 从消息历史中查找最新的用户消息
    messages = state.get("messages", [])
    for message in reversed(messages):
        if hasattr(message, 'type') and message.type == "human":
            return message.content if hasattr(message, 'content') else str(message)

    # 2. 从 input_data 中查找
    input_data = state.get("input_data", {})
    if "message" in input_data:
        messages_data = input_data["message"]
        for msg in reversed(messages_data):
            if isinstance(msg, dict) and msg.get("type") == "human":
                return msg.get("content", "")
            elif hasattr(msg, 'type') and msg.type == "human":
                return msg.content if hasattr(msg, 'content') else str(msg)

    # 3. 从 input 中查找
    if "input" in state:
        input_section = state["input"]
        if isinstance(input_section, dict) and "message" in input_section:
            messages_data = input_section["message"]
            for msg in reversed(messages_data):
                if isinstance(msg, dict) and msg.get("type") == "human":
                    return msg.get("content", "")
                elif hasattr(msg, 'type') and msg.type == "human":
                    return msg.content if hasattr(msg, 'content') else str(msg)

    # 4. 返回默认消息
    return "你好，请帮助我"


def format_a2a_response(result: A2AExecutionResult, agent_name: str) -> str:
    """
    格式化 A2A 智能体的成功响应

    Args:
        result: A2A 执行结果
        agent_name: 智能体名称

    Returns:
        str: 格式化后的响应内容
    """
    content = str(result.content)

    # 根据响应类型进行特殊格式化
    if result.type == "form_input":
        return f"🔧 **{agent_name}** 需要更多信息\n\n请填写以下表单信息：\n{content}"

    elif result.type == "skill_start":
        return f"⚡ **{agent_name}** 开始执行任务\n\n{content}"

    elif result.type == "skill_end":
        return f"✅ **{agent_name}** 任务执行完成\n\n{content}"

    elif result.type == "text":
        return f"🤖 **{agent_name}** 的回复\n\n{content}"

    else:
        return f"📄 **{agent_name}** 响应 ({result.type})\n\n{content}"


def format_a2a_error(result: A2AExecutionResult, agent_name: str) -> str:
    """格式化A2A执行错误信息"""
    error_msg = result.error_msg or "未知错误"

    # 根据错误类型提供更具体的说明
    if "not found" in error_msg.lower():
        reason = f"智能体 '{agent_name}' 不存在于A2A服务中"
        suggestion = "系统将自动使用通用智能体来处理您的请求"
    elif "timeout" in error_msg.lower():
        reason = f"智能体 '{agent_name}' 执行超时"
        suggestion = "可能是由于任务复杂度较高，系统将重试或使用其他智能体"
    elif "connection" in error_msg.lower():
        reason = f"无法连接到智能体 '{agent_name}' 的服务"
        suggestion = "系统将尝试重新连接或使用备用智能体"
    else:
        reason = f"智能体 '{agent_name}' 执行过程中出现问题"
        suggestion = "系统将分析错误并选择合适的备用方案"

    return f"""⚠️ **智能体执行失败**

**失败智能体**: {agent_name}
**失败原因**: {reason}
**错误详情**: {error_msg}
**后续处理**: {suggestion}

*系统正在为您寻找最佳的替代解决方案...*"""
