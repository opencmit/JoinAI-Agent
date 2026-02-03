"""
图像处理工具函数
"""
import base64
import re
from typing import Union
from urllib.parse import urlparse


async def process_image(image_input: str) -> str:
    """
    处理图像输入，支持URL和base64编码
    
    Args:
        image_input: 图像URL或base64编码字符串
    
    Returns:
        处理后的图像数据（URL或base64 data URI）
    """
    # 检查是否是base64编码
    if image_input.startswith("data:image"):
        # 已经是data URI格式
        return image_input
    
    # 检查是否是base64字符串（不含data URI前缀）
    base64_pattern = r"^[A-Za-z0-9+/=]+$"
    if re.match(base64_pattern, image_input) and len(image_input) > 100:
        # 假设是base64编码，转换为data URI
        # 尝试检测图像类型
        image_type = "jpeg"  # 默认类型
        return f"data:image/{image_type};base64,{image_input}"
    
    # 检查是否是URL
    parsed = urlparse(image_input)
    if parsed.scheme in ("http", "https"):
        return image_input
    
    # 如果是本地文件路径，读取并转换为base64
    try:
        with open(image_input, "rb") as f:
            image_data = f.read()
            image_base64 = base64.b64encode(image_data).decode("utf-8")
            # 根据文件扩展名确定MIME类型
            ext = image_input.lower().split(".")[-1]
            mime_types = {
                "jpg": "jpeg",
                "jpeg": "jpeg",
                "png": "png",
                "gif": "gif",
                "webp": "webp"
            }
            mime_type = mime_types.get(ext, "jpeg")
            return f"data:image/{mime_type};base64,{image_base64}"
    except Exception:
        pass
    
    # 如果无法识别，假设是URL
    return image_input

