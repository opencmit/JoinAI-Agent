"""
通用基础工具集 - 所有专家智能体都可以使用
"""

from datetime import datetime
from typing import Optional, Dict, Any
from langchain_core.tools import tool
import json
import os


@tool
def get_current_time() -> str:
    """
    获取当前时间
    
    Returns:
        str: 格式化的当前时间字符串
    """
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


@tool
def search_web(query: str, max_results: int = 3) -> str:
    """
    搜索网络获取相关信息（模拟）
    
    Args:
        query: 搜索查询
        max_results: 最大结果数
        
    Returns:
        str: 搜索结果摘要
    """
    # 这是一个模拟的搜索功能
    # 在实际使用中，可以集成真实的搜索API
    results = [
        {
            "title": f"关于 {query} 的专业分析",
            "snippet": f"这是关于 {query} 的详细信息和最新发展...",
            "url": f"https://example.com/{query.replace(' ', '-')}"
        },
        {
            "title": f"{query} 最佳实践指南",
            "snippet": f"了解 {query} 的行业标准和推荐做法...",
            "url": f"https://guide.example.com/{query.replace(' ', '-')}"
        }
    ]
    
    result_text = f"搜索 '{query}' 的结果：\n\n"
    for i, result in enumerate(results[:max_results], 1):
        result_text += f"{i}. {result['title']}\n"
        result_text += f"   {result['snippet']}\n"
        result_text += f"   链接: {result['url']}\n\n"
    
    return result_text


@tool
def read_file(file_path: str) -> str:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 文件内容或错误信息
    """
    try:
        # 安全检查：只允许读取特定目录下的文件
        safe_dir = "/tmp/expert_workspace"
        if not os.path.exists(safe_dir):
            os.makedirs(safe_dir)
        
        # 确保路径在安全目录内
        if not file_path.startswith(safe_dir):
            file_path = os.path.join(safe_dir, os.path.basename(file_path))
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return f"文件内容：\n{content}"
        else:
            return f"文件不存在: {file_path}"
    except Exception as e:
        return f"读取文件时出错: {str(e)}"


@tool
def write_file(file_path: str, content: str) -> str:
    """
    写入文件内容
    
    Args:
        file_path: 文件路径
        content: 要写入的内容
        
    Returns:
        str: 操作结果
    """
    try:
        # 安全检查：只允许写入特定目录下的文件
        safe_dir = "/tmp/expert_workspace"
        if not os.path.exists(safe_dir):
            os.makedirs(safe_dir)
        
        # 确保路径在安全目录内
        if not file_path.startswith(safe_dir):
            file_path = os.path.join(safe_dir, os.path.basename(file_path))
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"文件已成功写入: {file_path}"
    except Exception as e:
        return f"写入文件时出错: {str(e)}"


@tool
def word_count(text: str) -> Dict[str, int]:
    """
    统计文本的字数、字符数和行数
    
    Args:
        text: 要统计的文本
        
    Returns:
        Dict[str, int]: 包含各种统计信息的字典
    """
    # 统计中文字符
    chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
    
    # 统计英文单词
    words = text.split()
    english_words = len([w for w in words if any(c.isalpha() for c in w)])
    
    # 统计总字符数
    total_chars = len(text)
    
    # 统计行数
    lines = text.count('\n') + 1 if text else 0
    
    # 统计段落数（以空行分隔）
    paragraphs = len([p for p in text.split('\n\n') if p.strip()])
    
    return {
        "中文字数": chinese_chars,
        "英文单词数": english_words,
        "总字符数": total_chars,
        "行数": lines,
        "段落数": paragraphs,
        "总字数": chinese_chars + english_words
    }


# 导出所有工具
__all__ = [
    'get_current_time',
    'search_web',
    'read_file',
    'write_file',
    'word_count'
]