"""
A2A智能体核心实现
"""
import asyncio
import logging
from typing import Any, Dict, Optional

from openai import OpenAI
from python_a2a import (
    A2AServer,
    AgentCard,
    Message,
    MessageRole,
    TextContent,
    FunctionResponseContent,
    ErrorContent,
)

from app.multimodal import MultimodalRecognizer
from config.settings import get_settings

logger = logging.getLogger(__name__)


class MultimodalAgent(A2AServer):
    """多模态识别智能体"""

    def __init__(self, name: str = "multimodal-recognizer", **kwargs):
        logger.info(f"初始化多模态智能体: {name}")
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.recognizer = MultimodalRecognizer(client=self.client)
        logger.debug(
            f"智能体配置 - 模型: {self.settings.openai_model}, 主机: {self.settings.agent_host}, 端口: {self.settings.agent_port}")

        # 创建AgentCard，定义智能体的能力
        agent_card = AgentCard(
            name=name,
            description="多模态识别智能体，支持图像和文本的识别与分析。在对话中提供图片路径、URL或base64编码，我会自动识别并调用相应的工具进行处理。",
            url=f"http://{self.settings.agent_host}:{self.settings.agent_port}",
            version="1.0.0",
            capabilities={"streaming": False},
            skills=[]  # 不设置任何技能，agent具备多模态能力
        )

        # 初始化A2AServer
        super().__init__(
            agent_card=agent_card,
            message_handler=self.handle_message,
            **kwargs
        )

        # 覆盖父类强制设置的streaming为False
        # 注意：父类A2AServer在__init__中会强制设置streaming=True（第63行）
        # 必须在super().__init__()之后重新设置才能生效
        if hasattr(self, 'agent_card') and self.agent_card is not None:
            if not hasattr(self.agent_card, 'capabilities') or self.agent_card.capabilities is None:
                self.agent_card.capabilities = {}
            if isinstance(self.agent_card.capabilities, dict):
                self.agent_card.capabilities["streaming"] = False

    def handle_message(self, message: Message) -> Message:
        """
        处理接收到的消息，智能识别图片路径/URL并自动调用相应工具
        
        Args:
            message: 接收到的A2A消息
        
        Returns:
            响应消息
        """
        logger.info(
            f"收到消息 - 类型: {message.content.type}, 消息ID: {message.message_id}, 会话ID: {message.conversation_id}")
        try:
            # 处理文本消息
            if message.content.type == "text":
                text = message.content.text
                logger.debug(f"处理文本消息，长度: {len(text)} 字符")

                # 智能识别并处理
                result = asyncio.run(self._process_text_message(text))
                logger.info("文本消息处理完成")

                return Message(
                    content=TextContent(text=result),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )

            # 处理函数调用（统一使用多模态处理）
            elif message.content.type == "function_call":
                function_name = message.content.name
                parameters = {param.name: param.value for param in message.content.parameters}
                logger.info(f"处理函数调用: {function_name}, 参数: {list(parameters.keys())}")

                # 统一使用多模态处理
                image_url = parameters.get("image_url") or parameters.get("image")
                text = parameters.get("text") or parameters.get("prompt")
                logger.debug(
                    f"函数调用参数 - image_url: {'存在' if image_url else 'None'}, text: {'存在' if text else 'None'}")

                result = asyncio.run(self._handle_multimodal_process(
                    image_url=image_url,
                    text=text
                ))

                logger.info(f"函数调用处理完成: {function_name}, 成功: {result.get('success', False)}")

                # 返回函数响应
                return Message(
                    content=FunctionResponseContent(
                        name=function_name,
                        response=result
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )

            else:
                # 其他类型消息返回错误
                logger.warning(f"不支持的消息类型: {message.content.type}")
                return Message(
                    content=ErrorContent(message=f"不支持的消息类型: {message.content.type}"),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )

        except Exception as e:
            # 返回错误消息
            logger.error(f"处理消息时发生错误: {str(e)}", exc_info=True)
            return Message(
                content=ErrorContent(message=f"处理消息时发生错误: {str(e)}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )

    async def _process_text_message(self, text: str) -> str:
        """
        智能处理文本消息，使用一次LLM调用提取信息并处理
        
        Args:
            text: 用户输入的文本
        
        Returns:
            处理结果文本
        """
        logger.debug(f"开始处理文本消息，长度: {len(text)} 字符")
        if not text or not text.strip():
            logger.warning("收到空文本消息")
            return "请输入有效的内容。"

        # 合并的LLM调用：从用户输入中提取图片和文本信息
        logger.info("开始第1次LLM调用：提取图片和文本信息")
        extracted_data = await self._extract_and_process_input(text)

        if not extracted_data.get("success"):
            logger.error(f"信息提取失败: {extracted_data.get('error', '未知错误')}")
            return f"信息提取失败：{extracted_data.get('error', '未知错误')}"

        image_url = extracted_data.get("image_url")
        extracted_text = extracted_data.get("text")
        logger.info(
            f"信息提取成功 - image_url: {'存在' if image_url else 'None'}, text: {'存在' if extracted_text else 'None'}")

        # 直接调用多模态处理
        logger.info("开始第2次LLM调用：多模态处理")
        result = await self._handle_multimodal_process(
            image_url=image_url,
            text=extracted_text
        )

        if result.get("success"):
            logger.info("多模态处理成功")
            return result.get('result', '处理完成。')
        else:
            error_msg = result.get('error', '未知错误')
            logger.error(f"多模态处理失败: {error_msg}")
            return f"处理失败：{error_msg}"

    async def _extract_and_process_input(self, user_input: str) -> Dict[str, Any]:
        """
        合并的LLM调用：从用户输入中提取图片URL和文本信息
        
        Args:
            user_input: 用户输入的原始文本
        
        Returns:
            包含提取结果的字典
        """
        import json
        try:
            import json_repair
            HAS_JSON_REPAIR = True
        except ImportError:
            json_repair = None
            HAS_JSON_REPAIR = False

        system_prompt = """你是一个信息提取助手。你的任务是从用户的输入中提取图片和文本信息。

JSON格式要求：
{
    "image_url": "图片URL、base64编码或文件路径（如果存在，否则为null）",
    "text": "提取的文本内容（如果存在，否则为null）"
}

规则：
1. 如果用户输入中包含图片URL（http://或https://）、base64编码（data:image/...）或文件路径，提取到image_url字段
2. 提取用户输入中的文本内容到text字段
3. 如果某个字段不存在，设置为null
4. 只返回JSON，不要包含任何其他文字说明
5. 确保JSON格式正确，可以被解析

示例：
输入："请识别这张图片 https://example.com/image.jpg"
输出：{"image_url": "https://example.com/image.jpg", "text": "请识别这张图片"}

输入："分析这段文本：这是一段很长的文本内容..."
输出：{"image_url": null, "text": "这是一段很长的文本内容..."}

输入："对比分析图片 https://example.com/photo.png 和文本：相关说明"
输出：{"image_url": "https://example.com/photo.png", "text": "相关说明"}
"""

        raw_response = None
        try:
            logger.debug(f"调用LLM提取信息，输入长度: {len(user_input)} 字符")
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"请从以下输入中提取图片和文本信息：\n\n{user_input}"
                    }
                ],
                temperature=0.1,
                max_tokens=500,
                response_format={"type": "json_object"}
            )

            raw_response = response.choices[0].message.content
            logger.debug(f"LLM响应长度: {len(raw_response)} 字符")

            # 尝试直接解析JSON
            try:
                json_data = json.loads(raw_response)
                logger.debug("JSON解析成功（直接解析）")
            except json.JSONDecodeError as e:
                logger.warning(f"直接JSON解析失败，尝试修复: {str(e)}")
                # 使用json_repair修复JSON
                if HAS_JSON_REPAIR:
                    try:
                        logger.debug("使用json_repair修复JSON")
                        repaired_json = json_repair.repair_json(raw_response)
                        json_data = json.loads(repaired_json)
                        logger.info("json_repair修复成功")
                    except Exception as repair_error:
                        logger.warning(f"json_repair修复失败，尝试提取: {str(repair_error)}")
                        # 如果json_repair也失败，尝试提取JSON
                        try:
                            json_str = self._extract_json_from_response(raw_response)
                            json_data = json.loads(json_str)
                            logger.info("JSON提取成功")
                        except Exception as extract_error:
                            logger.error(f"JSON提取也失败: {str(extract_error)}")
                            return {
                                "success": False,
                                "error": f"JSON解析失败，json_repair修复失败: {str(repair_error)}，提取也失败: {str(extract_error)}",
                                "image_url": None,
                                "text": None
                            }
                else:
                    # 如果没有json_repair，使用备用提取方法
                    logger.debug("使用备用方法提取JSON")
                    json_str = self._extract_json_from_response(raw_response)
                    json_data = json.loads(json_str)
                    logger.info("备用方法提取成功")

            # 提取数据
            image_url = json_data.get("image_url")
            extracted_text = json_data.get("text")

            # 处理null值
            if image_url == "null" or image_url is None:
                image_url = None
            if extracted_text == "null" or extracted_text is None:
                extracted_text = None

            logger.info(
                f"信息提取完成 - image_url: {image_url[:50] + '...' if image_url and len(image_url) > 50 else image_url}, text: {extracted_text[:50] + '...' if extracted_text and len(extracted_text) > 50 else extracted_text}")

            return {
                "success": True,
                "image_url": image_url,
                "text": extracted_text
            }
        except json.JSONDecodeError as e:
            logger.warning(f"JSON解析异常，尝试容灾处理: {str(e)}")
            # 容灾：尝试使用json_repair修复
            if raw_response and HAS_JSON_REPAIR:
                try:
                    logger.debug("容灾：使用json_repair修复JSON")
                    repaired_json = json_repair.repair_json(raw_response)
                    json_data = json.loads(repaired_json)
                    logger.info("容灾：json_repair修复成功")
                    return {
                        "success": True,
                        "image_url": json_data.get("image_url"),
                        "text": json_data.get("text")
                    }
                except Exception as repair_error:
                    logger.error(f"容灾：json_repair修复失败: {str(repair_error)}")
                    return {
                        "success": False,
                        "error": f"JSON解析失败: {str(e)}，json_repair修复也失败: {str(repair_error)}",
                        "image_url": None,
                        "text": None
                    }
            elif raw_response:
                # 如果没有json_repair，使用备用提取方法
                try:
                    logger.debug("容灾：使用备用方法提取JSON")
                    json_str = self._extract_json_from_response(raw_response)
                    json_data = json.loads(json_str)
                    logger.info("容灾：备用方法提取成功")
                    return {
                        "success": True,
                        "image_url": json_data.get("image_url"),
                        "text": json_data.get("text")
                    }
                except Exception as extract_error:
                    logger.error(f"容灾：备用方法提取失败: {str(extract_error)}")
                    return {
                        "success": False,
                        "error": f"JSON解析失败: {str(e)}，容灾提取也失败: {str(extract_error)}",
                        "image_url": None,
                        "text": None
                    }
            logger.error(f"JSON解析失败且无容灾数据: {str(e)}")
            return {
                "success": False,
                "error": f"JSON解析失败: {str(e)}",
                "image_url": None,
                "text": None
            }
        except Exception as e:
            logger.error(f"信息提取异常: {str(e)}", exc_info=True)
            # 容灾：如果API调用失败，尝试从错误响应中提取
            if raw_response and HAS_JSON_REPAIR:
                try:
                    logger.debug("容灾：从异常响应中使用json_repair修复")
                    repaired_json = json_repair.repair_json(raw_response)
                    json_data = json.loads(repaired_json)
                    logger.info("容灾：从异常响应中成功提取")
                    return {
                        "success": True,
                        "image_url": json_data.get("image_url"),
                        "text": json_data.get("text")
                    }
                except Exception as repair_error:
                    logger.debug(f"容灾修复失败: {str(repair_error)}")
            elif raw_response:
                try:
                    logger.debug("容灾：从异常响应中使用备用方法提取")
                    json_str = self._extract_json_from_response(raw_response)
                    json_data = json.loads(json_str)
                    logger.info("容灾：从异常响应中成功提取")
                    return {
                        "success": True,
                        "image_url": json_data.get("image_url"),
                        "text": json_data.get("text")
                    }
                except Exception as extract_error:
                    logger.debug(f"容灾提取失败: {str(extract_error)}")
            return {
                "success": False,
                "error": f"信息提取失败: {str(e)}",
                "image_url": None,
                "text": None
            }

    def _extract_json_from_response(self, response: str) -> str:
        """
        从LLM响应中提取JSON，支持多种格式容灾处理
        
        Args:
            response: LLM的原始响应
        
        Returns:
            提取的JSON字符串
        """
        import json
        import re

        if not response:
            raise ValueError("响应为空")

        # 1. 尝试直接解析（可能是纯JSON）
        try:
            json.loads(response.strip())
            return response.strip()
        except:
            pass

        # 2. 尝试提取markdown代码块中的JSON
        # 匹配 ```json ... ``` 或 ``` ... ```
        json_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        matches = re.findall(json_block_pattern, response, re.DOTALL | re.IGNORECASE)
        if matches:
            json_str = matches[0].strip()
            try:
                json.loads(json_str)
                return json_str
            except:
                pass

        # 3. 尝试提取 { ... } 之间的内容
        json_object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(json_object_pattern, response, re.DOTALL)
        for match in matches:
            try:
                json.loads(match)
                return match
            except:
                continue

        # 4. 尝试提取第一行到最后一行的JSON
        lines = response.strip().split('\n')
        # 找到第一个包含 { 的行和最后一个包含 } 的行
        start_idx = None
        end_idx = None
        for i, line in enumerate(lines):
            if '{' in line and start_idx is None:
                start_idx = i
            if '}' in line:
                end_idx = i

        if start_idx is not None and end_idx is not None:
            json_str = '\n'.join(lines[start_idx:end_idx + 1])
            try:
                json.loads(json_str)
                return json_str
            except:
                pass

        # 5. 如果都不行，尝试清理后解析
        # 移除可能的markdown标记、多余空白等
        cleaned = response.strip()
        # 移除开头的markdown代码块标记
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
        # 移除结尾的markdown代码块标记
        cleaned = re.sub(r'\n?```\s*$', '', cleaned, flags=re.IGNORECASE)
        # 移除可能的说明文字（在JSON之前或之后）
        # 尝试找到第一个 { 和最后一个 }
        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            json_str = cleaned[first_brace:last_brace + 1]
            try:
                json.loads(json_str)
                return json_str
            except:
                pass

        # 6. 最后尝试：返回清理后的原始响应
        raise ValueError(f"无法从响应中提取有效的JSON: {response[:200]}")

    async def _handle_multimodal_process(
            self,
            image_url: Optional[str] = None,
            text: Optional[str] = None
    ) -> Dict[str, Any]:
        """统一的多模态处理"""
        logger.debug(
            f"开始多模态处理 - image_url: {'存在' if image_url else 'None'}, text: {'存在' if text else 'None'}")
        try:
            result = await self.recognizer.process(
                image_url=image_url,
                text=text
            )
            if result.get("success"):
                logger.info("多模态处理成功")
            else:
                logger.error(f"多模态处理失败: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"多模态处理异常: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
