"""
团队成员配置模块

定义各个团队成员（智能体）的配置信息
"""

# 团队成员配置
TEAM_MEMBER_CONFIGRATIONS = {
    "researcher": {
        "desc_for_llm": "专业研究员，负责信息搜集、数据分析和深度调研"
    },
    "coder": {
        "desc_for_llm": "编程专家，负责代码开发、调试和技术实现"
    },
    # "browser": {
    #     "desc_for_llm": "网页浏览专家，负责网页操作、信息爬取和在线交互"
    # },
    "reporter": {
        "desc_for_llm": "报告撰写专家，负责总结分析结果并生成最终报告"
    },
    "a2a_agent": {
        "desc_for_llm": "A2A智能体，外部专业智能体服务集成"
    },
    "mcp_tool": {
        "desc_for_llm": "MCP工具集成，提供模型上下文协议工具支持"
    }
}

