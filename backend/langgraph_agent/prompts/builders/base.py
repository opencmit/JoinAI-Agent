"""
Prompt 构建器基类
"""
import os
from typing import Dict, Any
from langgraph_agent.prompts.loader import get_loader

class BasePromptBuilder:
    """Prompt 构建器基类"""
    
    def __init__(self):
        self.loader = get_loader()
    
    async def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        异步加载 YAML 模板
        
        Args:
            template_name: YAML 文件名
        
        Returns:
            解析后的 YAML 数据（字典）
        """
        return await self.loader.load_yaml(template_name)
    
    async def render(self, template_name: str, context: Dict[str, Any] = None) -> str:
        """
        异步渲染模板
        
        Args:
            template_name: YAML 文件名（如 'supervisor.yaml'）
            context: Jinja2 模板的上下文变量
        
        Returns:
            渲染后的 prompt 字符串
        """
        return await self.loader.render(template_name, context)

