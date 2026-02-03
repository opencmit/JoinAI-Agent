"""
文本处理工具函数
"""


def process_text(text: str) -> str:
    """
    预处理文本内容
    
    Args:
        text: 原始文本
    
    Returns:
        处理后的文本
    """
    if not text:
        return ""
    
    # 去除首尾空白
    text = text.strip()
    
    # 限制文本长度（避免超出模型限制）
    max_length = 10000
    if len(text) > max_length:
        text = text[:max_length] + "...[文本已截断]"
    
    return text

