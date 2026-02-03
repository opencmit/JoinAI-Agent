"""
广播/博客专家专属工具集
"""

from typing import Dict, Any, List
from langchain_core.tools import tool
import re


@tool
def analyze_seo(title: str, content: str, keywords: List[str]) -> Dict[str, Any]:
    """
    分析SEO优化情况
    
    Args:
        title: 文章标题
        content: 文章内容
        keywords: 目标关键词列表
        
    Returns:
        Dict[str, Any]: SEO分析结果
    """
    analysis = {
        "标题分析": {},
        "关键词密度": {},
        "内容分析": {},
        "建议": []
    }
    
    # 标题分析
    title_length = len(title)
    analysis["标题分析"] = {
        "长度": title_length,
        "评价": "合适" if 30 <= title_length <= 60 else "过短" if title_length < 30 else "过长",
        "包含关键词": [kw for kw in keywords if kw.lower() in title.lower()]
    }
    
    # 关键词密度分析
    content_lower = content.lower()
    total_words = len(content.split())
    
    for keyword in keywords:
        count = content_lower.count(keyword.lower())
        density = (count / total_words * 100) if total_words > 0 else 0
        analysis["关键词密度"][keyword] = {
            "出现次数": count,
            "密度": f"{density:.1f}%",
            "评价": "合适" if 1 <= density <= 3 else "偏低" if density < 1 else "过高"
        }
    
    # 内容分析
    paragraphs = [p for p in content.split('\n\n') if p.strip()]
    headings = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)
    
    analysis["内容分析"] = {
        "总字数": len(content),
        "段落数": len(paragraphs),
        "标题数": len(headings),
        "首段包含关键词": any(kw.lower() in paragraphs[0].lower() for kw in keywords) if paragraphs else False,
        "图片alt标签": "建议添加" if "img" not in content else "已包含"
    }
    
    # SEO建议
    if title_length < 30:
        analysis["建议"].append("标题过短，建议扩展到30-60个字符")
    elif title_length > 60:
        analysis["建议"].append("标题过长，建议精简到60个字符以内")
    
    if not analysis["标题分析"]["包含关键词"]:
        analysis["建议"].append("标题中应包含至少一个目标关键词")
    
    if len(content) < 300:
        analysis["建议"].append("内容过短，建议至少300字以上")
    
    if not headings:
        analysis["建议"].append("建议添加小标题（H2-H6）改善内容结构")
    
    if not analysis["建议"]:
        analysis["建议"].append("SEO优化良好，继续保持")
    
    return analysis


@tool
def score_title(title: str) -> Dict[str, Any]:
    """
    评估标题吸引力
    
    Args:
        title: 文章标题
        
    Returns:
        Dict[str, Any]: 标题评分和建议
    """
    score = 50  # 基础分
    factors = {
        "长度": {"score": 0, "reason": ""},
        "数字": {"score": 0, "reason": ""},
        "情感词": {"score": 0, "reason": ""},
        "问句": {"score": 0, "reason": ""},
        "紧迫感": {"score": 0, "reason": ""}
    }
    
    # 长度评分
    title_length = len(title)
    if 10 <= title_length <= 30:
        factors["长度"]["score"] = 10
        factors["长度"]["reason"] = "长度适中"
    elif title_length < 10:
        factors["长度"]["score"] = -5
        factors["长度"]["reason"] = "过短"
    else:
        factors["长度"]["score"] = -5
        factors["长度"]["reason"] = "过长"
    
    # 包含数字
    if re.search(r'\d+', title):
        factors["数字"]["score"] = 15
        factors["数字"]["reason"] = "包含具体数字，增加可信度"
    
    # 情感词汇
    emotion_words = ["最", "必", "秘", "绝", "惊", "神", "超", "极"]
    if any(word in title for word in emotion_words):
        factors["情感词"]["score"] = 10
        factors["情感词"]["reason"] = "包含情感词汇，增强吸引力"
    
    # 问句形式
    if title.endswith("？") or title.endswith("?"):
        factors["问句"]["score"] = 10
        factors["问句"]["reason"] = "问句形式，引发好奇心"
    
    # 紧迫感词汇
    urgency_words = ["立即", "马上", "现在", "今天", "限时", "最新"]
    if any(word in title for word in urgency_words):
        factors["紧迫感"]["score"] = 5
        factors["紧迫感"]["reason"] = "营造紧迫感"
    
    # 计算总分
    total_score = score + sum(f["score"] for f in factors.values())
    total_score = max(0, min(100, total_score))  # 限制在0-100之间
    
    # 评级
    if total_score >= 80:
        rating = "优秀"
    elif total_score >= 60:
        rating = "良好"
    elif total_score >= 40:
        rating = "一般"
    else:
        rating = "需改进"
    
    return {
        "标题": title,
        "总分": total_score,
        "评级": rating,
        "评分因素": factors,
        "改进建议": [
            "添加具体数字" if factors["数字"]["score"] == 0 else None,
            "考虑使用问句形式" if factors["问句"]["score"] == 0 else None,
            "加入情感词汇" if factors["情感词"]["score"] == 0 else None,
            "控制标题长度在10-30字之间" if factors["长度"]["score"] < 0 else None
        ],
        "优秀示例": f"《{title[:10]}...的5个秘诀》" if len(title) > 10 else f"《如何{title}？》"
    }


@tool
def format_social_media(content: str, platform: str = "weixin") -> Dict[str, str]:
    """
    为不同社交媒体平台格式化内容
    
    Args:
        content: 原始内容
        platform: 平台类型（weixin, weibo, xiaohongshu, douyin）
        
    Returns:
        Dict[str, str]: 格式化后的内容
    """
    formatted = {}
    
    if platform == "weixin":
        # 微信公众号格式
        formatted["标题"] = content.split('\n')[0] if content else "标题"
        formatted["摘要"] = content[:100] + "..." if len(content) > 100 else content
        formatted["正文"] = content
        formatted["建议"] = [
            "标题控制在20字以内",
            "摘要突出核心价值",
            "正文分段清晰，每段3-5句",
            "适当添加表情符号增强亲和力",
            "文末添加互动引导"
        ]
        
    elif platform == "weibo":
        # 微博格式（140字限制）
        if len(content) > 140:
            formatted["内容"] = content[:137] + "..."
            formatted["提示"] = "内容已截断至140字"
        else:
            formatted["内容"] = content
        formatted["话题标签"] = "#话题1# #话题2#"
        formatted["建议"] = [
            "开头抓人眼球",
            "使用热门话题标签",
            "配图增加曝光",
            "选择最佳发布时间"
        ]
        
    elif platform == "xiaohongshu":
        # 小红书格式
        formatted["标题"] = "✨ " + (content.split('\n')[0] if content else "标题")
        formatted["正文"] = content[:1000] if len(content) > 1000 else content
        formatted["标签"] = "#种草 #好物推荐 #生活分享"
        formatted["表情建议"] = "多使用emoji表情符号"
        formatted["建议"] = [
            "标题使用emoji吸引注意",
            "图文并茂，图片质量要高",
            "真实分享，避免硬广",
            "互动回复评论"
        ]
        
    elif platform == "douyin":
        # 抖音格式
        formatted["文案"] = content[:500] if len(content) > 500 else content
        formatted["话题"] = "#抖音热点 #日常 #vlog"
        formatted["建议"] = [
            "前3秒要吸引人",
            "文案简洁有力",
            "配合热门音乐",
            "选择合适的发布时间",
            "引导互动（点赞、评论、关注）"
        ]
    
    else:
        formatted["原始内容"] = content
        formatted["提示"] = f"不支持的平台: {platform}"
    
    # 添加通用建议
    formatted["通用建议"] = [
        "保持内容原创性",
        "定期更新保持活跃",
        "分析数据优化内容",
        "建立个人风格"
    ]
    
    return formatted


# 导出所有工具
__all__ = [
    'analyze_seo',
    'score_title',
    'format_social_media'
]