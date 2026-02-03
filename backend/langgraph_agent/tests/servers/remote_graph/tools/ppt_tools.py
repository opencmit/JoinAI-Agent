"""
PPT专家专属工具集
"""

from typing import List, Dict, Any
from langchain_core.tools import tool


@tool
def create_outline(title: str, main_points: List[str], sub_points_per_main: int = 3) -> str:
    """
    创建PPT大纲结构
    
    Args:
        title: PPT标题
        main_points: 主要观点列表
        sub_points_per_main: 每个主要观点的子观点数量
        
    Returns:
        str: 格式化的大纲
    """
    outline = f"# {title}\n\n"
    outline += "## 幻灯片大纲\n\n"
    
    # 封面页
    outline += "### 第1页 - 封面\n"
    outline += f"- 标题: {title}\n"
    outline += "- 副标题: [待定]\n"
    outline += "- 演讲者: [待定]\n"
    outline += "- 日期: [待定]\n\n"
    
    # 目录页
    outline += "### 第2页 - 目录\n"
    for i, point in enumerate(main_points, 1):
        outline += f"- {i}. {point}\n"
    outline += "\n"
    
    # 内容页
    page_num = 3
    for i, main_point in enumerate(main_points, 1):
        outline += f"### 第{page_num}页 - {main_point}\n"
        outline += f"**主要观点**: {main_point}\n"
        outline += "**支撑内容**:\n"
        for j in range(1, sub_points_per_main + 1):
            outline += f"- 要点 {j}: [待补充]\n"
        outline += "**视觉元素**: [图表/图片建议]\n\n"
        page_num += 1
    
    # 总结页
    outline += f"### 第{page_num}页 - 总结\n"
    outline += "- 核心要点回顾\n"
    outline += "- 关键收获\n"
    outline += "- 下一步行动\n\n"
    
    # Q&A页
    outline += f"### 第{page_num + 1}页 - Q&A\n"
    outline += "- 感谢聆听\n"
    outline += "- 问题与讨论\n"
    outline += "- 联系方式\n"
    
    return outline


@tool
def generate_chart(data_type: str, title: str, values: List[float]) -> str:
    """
    生成图表描述（文本表示）
    
    Args:
        data_type: 图表类型（bar, pie, line）
        title: 图表标题
        values: 数据值列表
        
    Returns:
        str: 图表的文本描述
    """
    chart_text = f"📊 {title}\n"
    chart_text += f"图表类型: {data_type}\n\n"
    
    if data_type == "bar":
        # 柱状图文本表示
        chart_text += "柱状图数据:\n"
        max_val = max(values) if values else 1
        for i, val in enumerate(values):
            bar_length = int((val / max_val) * 20)
            bar = "█" * bar_length
            chart_text += f"项目{i+1}: {bar} {val:.1f}\n"
    
    elif data_type == "pie":
        # 饼图文本表示
        total = sum(values)
        chart_text += "饼图数据:\n"
        for i, val in enumerate(values):
            percentage = (val / total * 100) if total > 0 else 0
            chart_text += f"部分{i+1}: {percentage:.1f}% ({val:.1f})\n"
    
    elif data_type == "line":
        # 折线图文本表示
        chart_text += "折线图趋势:\n"
        for i, val in enumerate(values):
            if i > 0:
                trend = "↑" if val > values[i-1] else "↓" if val < values[i-1] else "→"
                chart_text += f"点{i+1}: {val:.1f} {trend}\n"
            else:
                chart_text += f"点{i+1}: {val:.1f} (起始)\n"
    
    chart_text += "\n建议: 使用专业图表工具生成实际图表"
    return chart_text


@tool
def estimate_pages(content_items: List[str], items_per_page: int = 5) -> Dict[str, Any]:
    """
    估算PPT页数
    
    Args:
        content_items: 内容项列表
        items_per_page: 每页的内容项数量
        
    Returns:
        Dict[str, Any]: 页数估算结果
    """
    total_items = len(content_items)
    content_pages = (total_items + items_per_page - 1) // items_per_page
    
    # 标准PPT结构页面
    fixed_pages = {
        "封面": 1,
        "目录": 1,
        "总结": 1,
        "Q&A": 1
    }
    
    total_pages = content_pages + sum(fixed_pages.values())
    
    # 估算演讲时间（每页约1-2分钟）
    min_time = total_pages * 1
    max_time = total_pages * 2
    
    return {
        "内容页数": content_pages,
        "固定页数": sum(fixed_pages.values()),
        "总页数": total_pages,
        "页面分布": {
            **fixed_pages,
            "内容页": content_pages
        },
        "预计演讲时间": f"{min_time}-{max_time}分钟",
        "建议": "每页控制3-5个要点" if items_per_page <= 5 else "考虑减少每页内容量",
        "内容项详情": content_items[:10]  # 显示前10个内容项
    }


# 导出所有工具
__all__ = [
    'create_outline',
    'generate_chart',
    'estimate_pages'
]