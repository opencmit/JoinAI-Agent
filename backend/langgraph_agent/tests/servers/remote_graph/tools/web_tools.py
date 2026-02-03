"""
Web开发专家专属工具集
"""

from typing import Dict, Any, List
from langchain_core.tools import tool
import re


@tool
def generate_html_preview(title: str, content: str, css_style: str = "default") -> str:
    """
    生成HTML预览代码
    
    Args:
        title: 页面标题
        content: 页面内容
        css_style: CSS样式（default, modern, minimal）
        
    Returns:
        str: HTML代码
    """
    css_styles = {
        "default": """
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            p { line-height: 1.6; }
        """,
        "modern": """
            body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; margin-bottom: 20px; }
            p { color: #555; line-height: 1.8; }
        """,
        "minimal": """
            body { font-family: Georgia, serif; max-width: 600px; margin: 50px auto; padding: 20px; }
            h1 { font-weight: normal; border-bottom: 1px solid #eee; padding-bottom: 10px; }
            p { color: #444; line-height: 1.7; }
        """
    }
    
    selected_style = css_styles.get(css_style, css_styles["default"])
    
    html_template = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {selected_style}
    </style>
</head>
<body>
    <div class="container">
        <h1>{title}</h1>
        {content}
    </div>
</body>
</html>"""
    
    return f"HTML预览代码:\n```html\n{html_template}\n```"


@tool
def validate_css(css_code: str) -> Dict[str, Any]:
    """
    验证CSS代码（基础检查）
    
    Args:
        css_code: CSS代码
        
    Returns:
        Dict[str, Any]: 验证结果
    """
    issues = []
    warnings = []
    
    # 检查基本语法
    if css_code.count('{') != css_code.count('}'):
        issues.append("花括号不匹配")
    
    if css_code.count('(') != css_code.count(')'):
        issues.append("圆括号不匹配")
    
    # 检查分号
    rules = re.findall(r'\{[^}]*\}', css_code)
    for rule in rules:
        declarations = rule.strip('{}').split(';')
        for decl in declarations:
            if decl.strip() and ':' not in decl:
                warnings.append(f"可能缺少冒号: {decl.strip()[:30]}")
    
    # 检查常见的CSS属性拼写错误
    common_typos = {
        'colr': 'color',
        'backgroud': 'background',
        'witdh': 'width',
        'heigth': 'height',
        'margn': 'margin',
        'paddng': 'padding'
    }
    
    for typo, correct in common_typos.items():
        if typo in css_code.lower():
            warnings.append(f"可能的拼写错误: '{typo}' 应该是 '{correct}'")
    
    # 检查颜色值
    hex_colors = re.findall(r'#[0-9a-fA-F]{3,6}', css_code)
    invalid_colors = [c for c in hex_colors if len(c) not in [4, 7]]
    if invalid_colors:
        warnings.append(f"无效的十六进制颜色值: {invalid_colors}")
    
    # 统计CSS规则
    selectors = re.findall(r'[^{]+(?=\s*{)', css_code)
    
    return {
        "有效": len(issues) == 0,
        "错误": issues if issues else ["无错误"],
        "警告": warnings if warnings else ["无警告"],
        "规则数量": len(selectors),
        "选择器": selectors[:5] if selectors else [],
        "建议": "CSS代码格式良好" if not issues else "请修复语法错误"
    }


@tool
def check_responsive(breakpoints: List[int] = None) -> Dict[str, Any]:
    """
    检查响应式设计断点
    
    Args:
        breakpoints: 自定义断点列表（像素）
        
    Returns:
        Dict[str, Any]: 响应式设计建议
    """
    if breakpoints is None:
        # 默认断点
        breakpoints = [320, 768, 1024, 1440]
    
    responsive_guide = {
        "断点设置": [],
        "设备覆盖": [],
        "CSS媒体查询": [],
        "注意事项": []
    }
    
    # 生成断点建议
    for i, bp in enumerate(breakpoints):
        if bp <= 480:
            device = "移动设备（手机）"
            query = f"@media (max-width: {bp}px)"
        elif bp <= 768:
            device = "平板设备（竖屏）"
            query = f"@media (min-width: {breakpoints[i-1] if i > 0 else 0}px) and (max-width: {bp}px)"
        elif bp <= 1024:
            device = "平板设备（横屏）/小型笔记本"
            query = f"@media (min-width: {breakpoints[i-1] if i > 0 else 769}px) and (max-width: {bp}px)"
        else:
            device = "桌面设备"
            query = f"@media (min-width: {bp}px)"
        
        responsive_guide["断点设置"].append(f"{bp}px - {device}")
        responsive_guide["设备覆盖"].append(device)
        responsive_guide["CSS媒体查询"].append(query)
    
    # 添加注意事项
    responsive_guide["注意事项"] = [
        "使用相对单位（rem, em, %）而非固定像素",
        "图片使用 max-width: 100% 确保自适应",
        "考虑触摸设备的交互（按钮最小44x44px）",
        "测试不同设备的实际显示效果",
        "使用 viewport meta 标签"
    ]
    
    # 生成示例代码
    example_css = """
/* 移动优先的响应式CSS示例 */
.container {
    width: 100%;
    padding: 15px;
}

@media (min-width: 768px) {
    .container {
        max-width: 750px;
        margin: 0 auto;
    }
}

@media (min-width: 1024px) {
    .container {
        max-width: 1000px;
    }
}"""
    
    responsive_guide["示例代码"] = example_css
    
    return responsive_guide


# 导出所有工具
__all__ = [
    'generate_html_preview',
    'validate_css',
    'check_responsive'
]