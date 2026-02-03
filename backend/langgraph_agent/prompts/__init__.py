"""
Prompts 模块 - 统一导出接口

这个模块提供了向后兼容的接口，确保现有代码无需修改即可使用新的 YAML + Builder 架构
"""

# ============================================================
# 1. 简单 Prompt - 从 YAML 文件加载
# ============================================================
from .loader import get_loader

_loader = get_loader()

# 加载简单的 YAML prompt（这些 prompt 不需要动态生成）
# 使用同步方法在模块初始化时加载，避免异步复杂性
COORDINATOR_PROMPT = _loader.load_simple_prompt_sync('coordinator.yaml')
CODER_PROMPT = _loader.load_simple_prompt_sync('coder.yaml')
RESEARCHER_PROMPT = _loader.load_simple_prompt_sync('researcher.yaml')
REPORTER_PROMPT = _loader.load_simple_prompt_sync('reporter.yaml')
BROWSER_PROMPT = _loader.load_simple_prompt_sync('browser.yaml')


# ============================================================
# 2. 复杂 Prompt - 使用 Builder 动态生成
# ============================================================

# Supervisor Prompt Builder - 动态生成基于 A2A/MCP 的 prompt
from .builders.supervisor_builder import (
    generate_supervisor_prompt,
    create_dynamic_supervisor_parser,
    create_dynamic_router
)

# Suna System Prompt Builder - 动态生成包含实时时间的 prompt
from .builders.suna_builder import (
    get_suna_system_prompt,
    get_system_prompt,
    SYSTEM_PROMPT
)


# ============================================================
# 3. MCP Prompt - 使用 Builder 动态生成
# ============================================================
# MCP prompt 由 builder 动态生成，包含工具列表和使用说明
from .builders.mcp_builder import get_mcp_prompt
from .formatters.mcp_formatter import format_mcp_tools_for_prompt_english


# ============================================================
# 4. 导出所有接口（向后兼容）
# ============================================================
__all__ = [
    # 简单 Prompt 常量
    'COORDINATOR_PROMPT',
    'CODER_PROMPT',
    'RESEARCHER_PROMPT',
    'REPORTER_PROMPT',
    'BROWSER_PROMPT',
    
    # Supervisor Prompt Builder
    'generate_supervisor_prompt',
    'create_dynamic_supervisor_parser',
    'create_dynamic_router',
    
    # Suna System Prompt Builder
    'get_suna_system_prompt',
    'get_system_prompt',
    'SYSTEM_PROMPT',
    
    # MCP Prompt and Formatter
    'get_mcp_prompt',
    'format_mcp_tools_for_prompt_english',
]
