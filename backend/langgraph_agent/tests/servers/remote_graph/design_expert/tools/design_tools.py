"""
设计专家工具集 - 图像生成和修改
"""

from langchain_core.tools import tool
import base64
import json
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
import random


@tool
def generate_image(prompt: str, style: str = "default", size: str = "1024x1024") -> Dict:
    """
    生成图像
    
    Args:
        prompt: 图像生成提示词
        style: 设计风格 (default, minimalist, professional, creative)
        size: 图像尺寸
        
    Returns:
        Dict: 包含生成的图像信息
    """
    # 模拟图像生成 - 实际应调用 DALL-E 或 Stable Diffusion API
    # 生成模拟的 base64 数据（实际应该是真实的图片数据）
    mock_base64_prefix = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA"
    
    # 根据提示词生成不同的模拟图像
    seed = hashlib.md5(prompt.encode()).hexdigest()[:8]
    
    images = []
    # 生成 1-3 张图片
    num_images = min(3, max(1, len(prompt) % 4))
    for i in range(num_images):
        mock_image = f"{mock_base64_prefix}_{seed}_{i}_{style}...MOCK_IMAGE_DATA"
        images.append(mock_image)
    
    return {
        "images": images,
        "prompt": prompt,
        "style": style,
        "size": size,
        "count": len(images)
    }


@tool
def modify_image(image_base64: str, modification: str, style: str = "default") -> Dict:
    """
    修改现有图像
    
    Args:
        image_base64: 原始图像的base64编码
        modification: 修改描述
        style: 目标风格
        
    Returns:
        Dict: 包含修改后的图像信息
    """
    # 模拟图像修改
    mock_base64_prefix = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA"
    
    # 根据修改描述生成新的图像
    seed = hashlib.md5(f"{image_base64[:50]}{modification}".encode()).hexdigest()[:8]
    modified_image = f"{mock_base64_prefix}_{seed}_modified_{style}...MOCK_MODIFIED_DATA"
    
    # 可能生成多个变体
    variations = [modified_image]
    if "多个" in modification or "变体" in modification:
        for i in range(2):
            variant = f"{mock_base64_prefix}_{seed}_variant_{i}_{style}...MOCK_VARIANT_DATA"
            variations.append(variant)
    
    return {
        "images": variations,
        "modification": modification,
        "style": style,
        "original_preview": image_base64[:50] + "..." if len(image_base64) > 50 else image_base64
    }


@tool
def analyze_design_request(query: str, image: Optional[str] = None) -> Dict:
    """
    分析设计请求，确定任务类型
    
    Args:
        query: 用户查询
        image: 可选的输入图像
        
    Returns:
        Dict: 任务分析结果
    """
    task_type = "modification" if image else "generation"
    
    # 分析设计风格
    styles = {
        "简约": "minimalist",
        "专业": "professional", 
        "创意": "creative",
        "现代": "modern",
        "复古": "vintage",
        "扁平": "flat"
    }
    
    detected_style = "default"
    for zh_style, en_style in styles.items():
        if zh_style in query:
            detected_style = en_style
            break
    
    # 分析尺寸需求
    size = "1024x1024"  # 默认
    if "横幅" in query or "banner" in query.lower():
        size = "1920x600"
    elif "海报" in query or "poster" in query.lower():
        size = "768x1024"
    elif "头像" in query or "avatar" in query.lower():
        size = "512x512"
    
    return {
        "task_type": task_type,
        "detected_style": detected_style,
        "suggested_size": size,
        "has_image": bool(image),
        "query_analysis": {
            "main_subject": extract_main_subject(query),
            "requirements": extract_requirements(query)
        }
    }


@tool
def save_design_file(content: str, filename: str, file_type: str = "html") -> Dict:
    """
    保存设计文件
    
    Args:
        content: 文件内容
        filename: 文件名
        file_type: 文件类型 (html, svg, json)
        
    Returns:
        Dict: 文件保存信息
    """
    # 确保文件名有正确的扩展名
    if not filename.endswith(f".{file_type}"):
        filename = f"{filename}.{file_type}"
    
    # 模拟文件保存
    file_path = f"deepresearch/{filename}"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "name": filename,
        "path": file_path,
        "date": current_time,
        "size": len(content),
        "type": file_type
    }


@tool
def create_design_preview(images: List[str], title: str = "设计预览") -> Dict:
    """
    创建设计预览HTML文件
    
    Args:
        images: 图像base64列表
        title: 预览标题
        
    Returns:
        Dict: 预览文件信息
    """
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; padding: 20px; }}
        .gallery {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .image-container {{ border: 1px solid #ddd; padding: 10px; border-radius: 8px; }}
        img {{ width: 100%; height: auto; border-radius: 4px; }}
        h1 {{ color: #333; }}
        .metadata {{ color: #666; font-size: 14px; margin-top: 10px; }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <div class="gallery">
"""
    
    for i, img in enumerate(images, 1):
        html_content += f"""
        <div class="image-container">
            <img src="{img}" alt="设计 {i}">
            <div class="metadata">设计方案 {i} - 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
"""
    
    html_content += """
    </div>
</body>
</html>"""
    
    filename = f"design_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    return {
        "html_content": html_content,
        "filename": filename,
        "image_count": len(images),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


def extract_main_subject(query: str) -> str:
    """提取查询中的主要主题"""
    subjects = ["海报", "logo", "图标", "横幅", "名片", "传单", "画册", "封面"]
    for subject in subjects:
        if subject in query.lower():
            return subject
    return "设计"


def extract_requirements(query: str) -> List[str]:
    """提取设计要求"""
    requirements = []
    
    # 颜色要求
    colors = ["红色", "蓝色", "绿色", "黑白", "彩色", "暖色", "冷色"]
    for color in colors:
        if color in query:
            requirements.append(f"颜色: {color}")
    
    # 风格要求
    if "简约" in query:
        requirements.append("风格: 简约")
    if "现代" in query:
        requirements.append("风格: 现代")
    if "专业" in query:
        requirements.append("风格: 专业")
    
    # 用途要求
    if "打印" in query:
        requirements.append("用途: 打印")
    if "网络" in query or "网站" in query:
        requirements.append("用途: 网络")
    
    return requirements


# 导出所有工具
__all__ = [
    'generate_image',
    'modify_image',
    'analyze_design_request',
    'save_design_file',
    'create_design_preview'
]