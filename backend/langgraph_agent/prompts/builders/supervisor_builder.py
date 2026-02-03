"""
Supervisor Prompt 构建器

负责动态生成 supervisor 的 prompt、Router 类和解析器
"""

from typing import List, Dict, Any, Literal
from pydantic import BaseModel, create_model
from langchain.output_parsers import PydanticOutputParser
from langgraph_agent.constant import TEAM_MEMBERS, TEAM_MEMBERS_INNER
from langgraph_agent.prompts.builders.base import BasePromptBuilder


class SupervisorPromptBuilder(BasePromptBuilder):
    """Supervisor Prompt 构建器"""
    
    async def generate_prompt(
        self,
        a2a_agents: List[Dict[str, Any]] = None,
        mcp_tools: List[Dict[str, Any]] = None
    ) -> str:
        """
        根据 A2A 智能体和 MCP 工具生成动态 supervisor prompt
        
        Args:
            a2a_agents: A2A 智能体列表，例如:
                [{'agent_id': 'xxx', 'name': 'weather', 'desc': '天气查询'}]
            mcp_tools: MCP 工具列表，例如:
                [{'tool_id': 'db', 'desc': '数据库查询'}]
        
        Returns:
            渲染后的 prompt 字符串
        """
        # 构建基础团队成员
        base_team_members = list(TEAM_MEMBERS_INNER)
        
        # 构建 A2A 智能体描述
        a2a_descriptions = []
        if a2a_agents:
            for agent in a2a_agents:
                agent_id = agent.get("agent_id", "")
                agent_name = agent.get("name", "")
                agent_desc = agent.get("desc", "")
                agent_type = agent.get("type", "normal")
                
                if agent_id:
                    a2a_route_name = f"a2a_{agent_name}"
                    description = f"- **`{a2a_route_name}`**: {agent_desc}"
                    a2a_descriptions.append(description)
        
        # 构建 MCP 工具描述
        mcp_tool_descriptions = []
        if mcp_tools:
            for tool in mcp_tools:
                # 兼容两种格式：tool_id/desc 和 name/description
                tool_id = tool.get("tool_id", tool.get("name", ""))
                tool_desc = tool.get("desc", tool.get("description", ""))
                tool_type = tool.get("type", "normal")
                
                if tool_id:
                    mcp_route_name = f"mcp_{tool_id}"
                    description = f"- **`{mcp_route_name}`**: {tool_desc}"
                    mcp_tool_descriptions.append(description)
        
        # 构建完整的团队成员列表
        all_team_members = base_team_members.copy()
        if a2a_agents:
            a2a_names = [f"a2a_{agent.get('name', '')}" for agent in a2a_agents if agent.get('name')]
            all_team_members.extend(a2a_names)
        
        if mcp_tools:
            mcp_names = [f"mcp_{tool.get('tool_id', tool.get('name', ''))}" for tool in mcp_tools if tool.get('tool_id') or tool.get('name')]
            all_team_members.extend(mcp_names)
        
        # 渲染 YAML 模板（使用 Jinja2）
        context = {
            'all_team_members': all_team_members,
            'a2a_agents': a2a_descriptions,
            'mcp_agents': mcp_tool_descriptions
        }
        
        # 调用父类的 render 方法，加载 supervisor.yaml 并渲染
        return await self.render('supervisor.yaml', context)
    
    def create_dynamic_router(
        self,
        a2a_agents: List[Dict[str, Any]] = None,
        mcp_tools: List[Dict[str, Any]] = None
    ) -> type:
        """
        根据 a2a_agents 和 mcp_tools 动态创建 Router 类
        
        Returns:
            动态创建的 Pydantic Router 类
        """
        # 基础路由选项（固定节点）
        base_routes = list(TEAM_MEMBERS) + ["FINISH"]
        
        # 处理 A2A 路由
        a2a_route_names = []
        if a2a_agents:
            a2a_route_names = [
                f"a2a_{agent['name']}"
                for agent in a2a_agents
                if agent.get("name")
            ]
        
        # 处理 MCP 工具路由
        mcp_route_names = []
        if mcp_tools:
            mcp_route_names = [
                f"mcp_{tool.get('tool_id', tool.get('name', ''))}"
                for tool in mcp_tools
                if tool.get("tool_id") or tool.get("name")
            ]
        
        # 合并所有路由选项
        all_routes = base_routes + a2a_route_names + mcp_route_names
        
        # 动态创建 Router 类
        router = create_model(
            'Router',
            next=(Literal[tuple(all_routes)], ...),
            sub_task=(str, ...),
            final_answer=(str, ...),
            __base__=BaseModel
        )
        
        return router
    
    def create_parser(
        self,
        a2a_agents: List[Dict[str, Any]] = None,
        mcp_tools: List[Dict[str, Any]] = None
    ):
        """
        创建动态的 supervisor 输出解析器
        
        Returns:
            PydanticOutputParser 实例
        """
        dynamic_router = self.create_dynamic_router(a2a_agents, mcp_tools)
        return PydanticOutputParser(pydantic_object=dynamic_router)


# ============================================================
# 向后兼容的函数接口（重要！确保原有代码无需修改）
# ============================================================

async def generate_supervisor_prompt(
    a2a_agents: List[Dict[str, Any]] = None,
    mcp_tools: List[Dict[str, Any]] = None
) -> str:
    """
    向后兼容的函数接口 - 生成 supervisor prompt（异步版本）
    
    这个函数保持与原 supervisor.py 相同的签名，
    确保 graph.py 中的调用代码无需修改
    """
    builder = SupervisorPromptBuilder()
    return await builder.generate_prompt(a2a_agents, mcp_tools)


def create_dynamic_router(
    a2a_agents: List[Dict[str, Any]] = None,
    mcp_tools: List[Dict[str, Any]] = None
) -> type:
    """
    向后兼容的函数接口 - 创建动态 Router 类
    """
    builder = SupervisorPromptBuilder()
    return builder.create_dynamic_router(a2a_agents, mcp_tools)


def create_dynamic_supervisor_parser(
    a2a_agents: List[Dict[str, Any]] = None,
    mcp_tools: List[Dict[str, Any]] = None
):
    """
    向后兼容的函数接口 - 创建 supervisor 输出解析器
    """
    builder = SupervisorPromptBuilder()
    return builder.create_parser(a2a_agents, mcp_tools)

