"""
专家智能体工具集合
"""

from .base_tools import (
    get_current_time,
    search_web,
    read_file,
    write_file,
    word_count
)

from .write_tools import (
    check_grammar,
    format_citation,
    count_paragraphs
)

from .ppt_tools import (
    create_outline,
    generate_chart,
    estimate_pages
)

from .web_tools import (
    generate_html_preview,
    validate_css,
    check_responsive
)

from .broadcast_tools import (
    analyze_seo,
    score_title,
    format_social_media
)

__all__ = [
    # 基础工具
    'get_current_time',
    'search_web',
    'read_file',
    'write_file',
    'word_count',
    # 写作工具
    'check_grammar',
    'format_citation',
    'count_paragraphs',
    # PPT工具
    'create_outline',
    'generate_chart',
    'estimate_pages',
    # Web工具
    'generate_html_preview',
    'validate_css',
    'check_responsive',
    # 广播工具
    'analyze_seo',
    'score_title',
    'format_social_media'
]