"""
Suna System Prompt 构建器

负责生成 Suna 系统 prompt，动态注入当前时间信息
"""

import datetime
from langgraph_agent.prompts.builders.base import BasePromptBuilder


class SunaPromptBuilder(BasePromptBuilder):
    """Suna System Prompt 构建器"""
    
    async def generate_prompt(self) -> str:
        """
        异步生成 Suna 系统 prompt，动态注入当前时间
        
        Returns:
            渲染后的 prompt 字符串
        """
        # 获取当前 UTC 时间（每次调用时都是最新的！）
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        
        context = {
            'current_date': now_utc.strftime('%Y-%m-%d'),
            'current_time': now_utc.strftime('%H:%M:%S'),
            'current_year': now_utc.year
        }
        
        # 调用父类的异步 render 方法，加载 suna.yaml 并渲染
        return await self.render('suna.yaml', context)
    
    def generate_prompt_sync(self) -> str:
        """
        同步生成 Suna 系统 prompt（仅用于模块初始化）
        
        Returns:
            渲染后的 prompt 字符串
        """
        import os
        import yaml
        from jinja2 import Template
        
        # 获取当前 UTC 时间
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        
        context = {
            'current_date': now_utc.strftime('%Y-%m-%d'),
            'current_time': now_utc.strftime('%H:%M:%S'),
            'current_year': now_utc.year
        }
        
        # 同步加载并渲染 YAML
        filepath = os.path.join(self.loader.templates_dir, 'suna.yaml')
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            prompt_template = data.get('prompt', '')
            template = Template(prompt_template)
            return template.render(**context)


# ============================================================
# 向后兼容的函数接口
# ============================================================

async def get_suna_system_prompt() -> str:
    """
    向后兼容的函数接口 - 异步生成 Suna 系统 prompt
    
    这个函数修复了原来的 bug：
    - 原来：datetime.datetime.now() 在模块加载时执行一次，时间固定
    - 现在：每次调用时都获取最新时间
    """
    builder = SunaPromptBuilder()
    return await builder.generate_prompt()


# 为了保持完全向后兼容，导出一个 SYSTEM_PROMPT 常量
# 但注意：这个常量在模块加载时就固定了，和原来的 bug 一样
# 使用同步版本在模块初始化时生成（仅为向后兼容）
# 推荐在代码中使用 get_suna_system_prompt() 函数来获取最新时间
_builder = SunaPromptBuilder()
SYSTEM_PROMPT = _builder.generate_prompt_sync()


# 原来的 get_system_prompt() 函数（向后兼容，异步版本）
async def get_system_prompt() -> str:
    """
    向后兼容的函数接口 - 返回 Suna 系统 prompt（异步版本）
    
    注意：这个函数现在会返回动态生成的 prompt（修复了原来的时间 bug）
    """
    return await get_suna_system_prompt()

