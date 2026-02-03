"""
YAML Prompt 加载器和渲染引擎
"""
import os
import yaml
from jinja2 import Environment, FileSystemLoader, Template
from typing import Dict, Any, Optional
import aiofiles

class PromptLoader:
    """YAML Prompt 加载器和渲染引擎"""
    
    def __init__(self, templates_dir: str = None):
        if templates_dir is None:
            # 默认模板目录：langgraph_agent/prompts/templates/
            templates_dir = os.path.join(
                os.path.dirname(__file__), 
                'templates'
            )
        self.templates_dir = templates_dir
        
        # 创建 Jinja2 环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(templates_dir),
            trim_blocks=True,      # 移除块标签后的第一个换行
            lstrip_blocks=True     # 移除块标签前的空格和制表符
        )
    
    async def load_yaml(self, template_name: str) -> Dict[str, Any]:
        """
        异步加载 YAML 文件
        
        Args:
            template_name: YAML 文件名（如 'supervisor.yaml'）
        
        Returns:
            解析后的 YAML 数据（字典）
        """
        filepath = os.path.join(self.templates_dir, template_name)
        async with aiofiles.open(filepath, 'r', encoding='utf-8') as f:
            content = await f.read()
            return yaml.safe_load(content)
    
    async def render(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """
        异步渲染 Jinja2 模板
        
        Args:
            template_name: YAML 文件名
            context: 模板变量（字典）
        
        Returns:
            渲染后的 prompt 字符串
        """
        # 1. 异步加载 YAML 文件
        data = await self.load_yaml(template_name)
        
        # 2. 提取 prompt 字段
        prompt_template = data.get('prompt', '')
        
        # 3. 如果提供了 context，使用 Jinja2 渲染
        if context:
            template = Template(prompt_template)
            return template.render(**context)
        
        # 4. 没有 context，直接返回原始 prompt
        return prompt_template
    
    async def load_simple_prompt(self, template_name: str) -> str:
        """
        异步加载简单 prompt（无需渲染）
        
        Args:
            template_name: YAML 文件名
        
        Returns:
            prompt 字符串
        """
        return await self.render(template_name)
    
    def load_simple_prompt_sync(self, template_name: str) -> str:
        """
        同步加载简单 prompt（仅用于模块初始化，非异步环境）
        
        Args:
            template_name: YAML 文件名
        
        Returns:
            prompt 字符串
        """
        filepath = os.path.join(self.templates_dir, template_name)
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            return data.get('prompt', '')

# 全局加载器实例（单例模式）
_loader = PromptLoader()

def get_loader() -> PromptLoader:
    """获取全局加载器实例"""
    return _loader

