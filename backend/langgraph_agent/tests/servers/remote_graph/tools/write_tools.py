"""
写作专家专属工具集
"""

from typing import List, Dict, Any
from langchain_core.tools import tool
import re


@tool
def check_grammar(text: str) -> Dict[str, Any]:
    """
    基础语法检查（模拟）
    
    Args:
        text: 要检查的文本
        
    Returns:
        Dict[str, Any]: 语法检查结果
    """
    issues = []
    
    # 检查常见的中文标点符号错误
    if '。。' in text or '，，' in text or '！！' in text:
        issues.append("发现重复的标点符号")
    
    # 检查中英文混排时的空格
    chinese_english = re.findall(r'[\u4e00-\u9fff][a-zA-Z]|[a-zA-Z][\u4e00-\u9fff]', text)
    if chinese_english:
        issues.append(f"中英文之间可能需要添加空格（发现 {len(chinese_english)} 处）")
    
    # 检查句子长度
    sentences = re.split(r'[。！？]', text)
    long_sentences = [s for s in sentences if len(s) > 100]
    if long_sentences:
        issues.append(f"发现 {len(long_sentences)} 个过长的句子（超过100字符）")
    
    # 统计段落
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    
    return {
        "语法问题": issues if issues else ["未发现明显的语法问题"],
        "问题数量": len(issues),
        "段落数": len(paragraphs),
        "句子数": len([s for s in sentences if s.strip()]),
        "建议": "请仔细检查标点符号和中英文混排格式" if issues else "文本格式良好"
    }


@tool
def format_citation(author: str, title: str, year: str, citation_style: str = "APA") -> str:
    """
    格式化引用文献
    
    Args:
        author: 作者
        title: 标题
        year: 年份
        citation_style: 引用格式（APA, MLA, Chicago）
        
    Returns:
        str: 格式化后的引用
    """
    if citation_style == "APA":
        # APA格式: Author, A. A. (Year). Title of work. Publisher.
        citation = f"{author} ({year}). {title}."
    elif citation_style == "MLA":
        # MLA格式: Author. "Title of Work." Publisher, Year.
        citation = f'{author}. "{title}." {year}.'
    elif citation_style == "Chicago":
        # Chicago格式: Author. Title of Work. Place: Publisher, Year.
        citation = f"{author}. {title}. {year}."
    else:
        citation = f"{author}, {title}, {year}"
    
    return f"格式化引用（{citation_style}）：\n{citation}"


@tool
def count_paragraphs(text: str) -> Dict[str, Any]:
    """
    统计段落结构信息
    
    Args:
        text: 要分析的文本
        
    Returns:
        Dict[str, Any]: 段落统计信息
    """
    # 分割段落
    paragraphs = [p for p in text.split('\n\n') if p.strip()]
    
    # 统计每个段落的信息
    paragraph_info = []
    for i, para in enumerate(paragraphs, 1):
        sentences = re.split(r'[。！？]', para)
        sentences = [s for s in sentences if s.strip()]
        
        # 计算段落字数
        chinese_chars = sum(1 for char in para if '\u4e00' <= char <= '\u9fff')
        words = para.split()
        english_words = len([w for w in words if any(c.isalpha() for c in w)])
        
        paragraph_info.append({
            "段落": i,
            "句子数": len(sentences),
            "字数": chinese_chars + english_words,
            "首句": sentences[0][:30] + "..." if sentences and len(sentences[0]) > 30 else sentences[0] if sentences else ""
        })
    
    # 计算平均值
    avg_sentences = sum(p["句子数"] for p in paragraph_info) / len(paragraph_info) if paragraph_info else 0
    avg_words = sum(p["字数"] for p in paragraph_info) / len(paragraph_info) if paragraph_info else 0
    
    return {
        "段落总数": len(paragraphs),
        "平均句子数": round(avg_sentences, 1),
        "平均字数": round(avg_words, 1),
        "段落详情": paragraph_info[:5],  # 只返回前5个段落的详情
        "结构评价": "段落结构均衡" if 50 <= avg_words <= 200 else "段落可能过长或过短"
    }


# 导出所有工具
__all__ = [
    'check_grammar',
    'format_citation',
    'count_paragraphs'
]