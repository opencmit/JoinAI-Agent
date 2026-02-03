"""
多模态识别核心功能
"""
import logging
from typing import Any, Dict, Optional
from openai import OpenAI

from utils.image_utils import process_image
from utils.text_utils import process_text
from config.settings import get_settings

logger = logging.getLogger(__name__)


class MultimodalRecognizer:
    """多模态识别器"""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.settings = get_settings()
    
    async def process(
        self,
        image_url: Optional[str] = None,
        text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        统一的多模态处理方法，支持图片、文本或两者结合
        
        Args:
            image_url: 图像URL、base64编码或文件路径（可选）
            text: 文本内容（可选）
        
        Returns:
            处理结果字典
        """
        logger.debug(f"开始多模态处理 - image_url: {'存在' if image_url else 'None'}, text: {'存在' if text else 'None'}")
        
        # 构建消息内容
        content = []
        
        # 处理文本
        if text:
            logger.debug(f"处理文本，原始长度: {len(text)} 字符")
            processed_text = process_text(text)
            if processed_text:
                content.append({
                    "type": "text",
                    "text": processed_text
                })
                logger.debug(f"文本处理完成，处理后长度: {len(processed_text)} 字符")
        
        # 处理图像
        if image_url:
            logger.debug(f"处理图像: {image_url[:50] + '...' if len(image_url) > 50 else image_url}")
            try:
                image_data = await process_image(image_url)
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": image_data
                    }
                })
                logger.debug("图像处理完成")
            except Exception as e:
                logger.error(f"图像处理失败: {str(e)}", exc_info=True)
                return {
                    "success": False,
                    "error": f"图像处理失败: {str(e)}",
                    "result": None
                }
        
        # 如果没有内容，返回错误
        if not content:
            logger.warning("没有可处理的内容（图片或文本）")
            return {
                "success": False,
                "error": "至少需要提供图片或文本内容",
                "result": None
            }
        
        # 构建系统提示词
        if image_url and text:
            system_prompt = "你是一个专业的多模态分析助手，擅长综合分析图像和文本信息。"
            process_type = "多模态分析"
        elif image_url:
            system_prompt = "你是一个专业的图像识别助手，请详细描述图像的内容，包括主要对象、场景、颜色、文字等信息。"
            process_type = "图像识别"
        else:
            system_prompt = "你是一个专业的文本分析助手，请根据用户的需求对文本进行分析和处理。"
            process_type = "文本分析"
        
        logger.info(f"调用多模态API - 类型: {process_type}, 模型: {self.settings.openai_model}")
        
        # 调用OpenAI多模态API
        try:
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": content
                    }
                ],
                max_tokens=2000
            )
            
            result = response.choices[0].message.content
            logger.info(f"多模态API调用成功，响应长度: {len(result)} 字符")
            
            return {
                "success": True,
                "result": result,
                "model": self.settings.openai_model,
                "has_image": image_url is not None,
                "has_text": text is not None
            }
        except Exception as e:
            logger.error(f"多模态API调用失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "result": None
            }

