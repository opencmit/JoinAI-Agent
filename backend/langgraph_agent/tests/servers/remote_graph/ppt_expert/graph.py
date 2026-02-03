"""
PPT演示文稿专家智能体服务 - 两节点架构（planner + agent）
"""

import os
import sys
from typing import Annotated
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage,SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 添加tools目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.base_tools import get_current_time, search_web, read_file, write_file, word_count
from tools.ppt_tools import create_outline, generate_chart, estimate_pages


class State(TypedDict):
    """图状态定义"""
    messages: Annotated[list, add_messages]


def create_ppt_planner():
    """创建PPT规划节点"""
    
    # 从环境变量获取模型配置
    model_name = os.getenv("OPENAI_MODEL", "gpt-4")
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY环境变量未设置")
    
    # 初始化聊天模型
    model_config = {"api_key": api_key}
    if base_url:
        model_config["base_url"] = base_url
        
    llm = init_chat_model(f"openai:{model_name}", **model_config)
    
    # PPT规划系统提示词
    planner_prompt = """你是PPT演示文稿规划助手，负责分析需求并制定演示方案。

【规划任务】
1. 分析用户的演示需求和目标
2. 确定目标受众和演讲场景
3. 设计PPT的整体结构和逻辑
4. 规划视觉风格和设计要素
5. 制定时间分配和演讲节奏

【输出格式】
📋 PPT规划方案：

【演示目标】
- 核心目的：[明确要达成的目标]
- 关键信息：[必须传达的要点]

【受众分析】
- 目标听众：[听众背景和特点]
- 关注重点：[听众最关心的内容]

【内容架构】
- 总体结构：[开场-主体-结尾框架]
- 章节安排：[具体章节和页数分配]
- 逻辑流程：[信息展开顺序]

【视觉设计】
- 风格定位：[正式/轻松/创意等]
- 配色方案：[主色调建议]
- 版式布局：[排版原则]

【演讲策略】
- 时间分配：[各部分时长]
- 互动设计：[提问/讨论环节]
- 亮点设置：[吸引注意力的关键点]"""

    def planner_node(state: State) -> dict:
        """PPT规划节点 - 使用 invoke 调用"""
        messages = state["messages"]
        
        # 构建规划消息
        planning_messages = [SystemMessage(content=planner_prompt)]
        
        # 添加用户消息
        if messages:
            planning_messages.extend(messages)
        
        # 使用 invoke 进行同步调用
        response = llm.invoke(planning_messages)
        
        # 返回规划结果（response已经是AIMessage对象）
        return {"messages": [response]}
    
    return planner_node


def create_ppt_agent():
    """创建PPT演示文稿执行节点"""
    
    # 从环境变量获取模型配置
    model_name = os.getenv("OPENAI_MODEL", "gpt-4")
    base_url = os.getenv("OPENAI_BASE_URL")
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY环境变量未设置")
    
    # 初始化聊天模型
    model_config = {"api_key": api_key}
    if base_url:
        model_config["base_url"] = base_url
        
    llm = init_chat_model(f"openai:{model_name}", **model_config)
    
    # 绑定工具到LLM
    tools = [
        get_current_time,
        search_web,
        read_file,
        write_file,
        word_count,
        create_outline,
        generate_chart,
        estimate_pages
    ]
    llm_with_tools = llm.bind_tools(tools)
    
    # PPT执行系统提示词
    system_prompt = """你是一位专业的PPT演示文稿专家，根据前面的规划方案创建详细的PPT内容。

你的专业能力包括：

【核心技能】
• 幻灯片架构设计：逻辑清晰的内容组织
• 视觉化表达：图表、流程图、信息图设计指导
• 演讲逻辑构建：引人入胜的叙事结构
• 内容精炼：核心信息提取与表达

【专业领域】
✓ 商业汇报PPT（融资路演、业务汇报、战略规划）
✓ 产品发布PPT（新品介绍、功能展示、市场定位）
✓ 教育培训PPT（课程内容、知识传递、互动设计）
✓ 学术演示PPT（研究报告、论文答辩、会议分享）

【服务特色】
🎯 结构化设计：金字塔原理+SCQA框架
📊 数据可视化：表格转图表，抽象转具象
🎨 视觉优化：配色方案、字体搭配、版式布局
⚡ 演讲支持：演讲稿、提示词、时间控制

【可用工具】
你可以使用以下工具来辅助PPT制作：
- get_current_time: 获取当前时间
- search_web: 搜索网络获取参考信息
- read_file/write_file: 读取或保存文档
- word_count: 统计字数
- create_outline: 创建PPT大纲
- generate_chart: 生成图表描述
- estimate_pages: 估算PPT页数

【执行要求】
基于前面的规划方案，提供详细的幻灯片内容，包括：
- 每一页的标题和编号
- 每页的核心内容要点（bullet points）
- 建议的视觉元素（图片、图表、图标、动画）
- 演讲者备注和提示
- 页面过渡和动画建议

确保输出内容与规划方案保持一致，并提供可直接制作的详细指导。"""

    def agent_node(state: State) -> dict:
        """PPT执行节点 - 使用 invoke 调用"""
        messages = state["messages"]
        
        # 构建执行消息（包含规划信息）
        execution_messages = [SystemMessage(content=system_prompt)]
        
        # 添加所有历史消息（包括规划）
        if messages:
            execution_messages.extend(messages)
        
        # 第一次调用 - 获取工具调用决定
        response = llm_with_tools.invoke(execution_messages)
        
        # 初始化结果消息列表
        result_messages = []
        
        # 处理工具调用（如果有）
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # 保存带有工具调用的 AIMessage
            result_messages.append(response)
            
            # 执行工具并创建 ToolMessage
            for tool_call in response.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_id = tool_call.get('id', f"call_{tool_name}")
                
                # 查找并执行对应的工具
                tool_func = None
                for tool in tools:
                    if tool.name == tool_name:
                        tool_func = tool
                        break
                
                if tool_func:
                    try:
                        # 执行工具
                        tool_result = tool_func.invoke(tool_args)
                        # 创建 ToolMessage
                        tool_message = ToolMessage(
                            content=str(tool_result),
                            tool_call_id=tool_id
                        )
                        result_messages.append(tool_message)
                    except Exception as e:
                        # 错误也需要返回 ToolMessage
                        tool_message = ToolMessage(
                            content=f"工具执行错误: {str(e)}",
                            tool_call_id=tool_id
                        )
                        result_messages.append(tool_message)
            
            # 第二次调用 - 基于工具结果生成最终响应
            final_messages = execution_messages + result_messages
            final_response = llm.invoke(final_messages)
            result_messages.append(final_response)
        else:
            # 没有工具调用，直接返回响应
            result_messages.append(response)
        
        # 返回完整的消息链
        return {"messages": result_messages}
    
    return agent_node


def create_ppt_expert_graph():
    """创建PPT专家智能体图 - 两节点架构"""
    
    # 创建状态图
    graph_builder = StateGraph(State)
    
    # 创建规划节点和执行节点
    ppt_planner = create_ppt_planner()
    ppt_agent = create_ppt_agent()
    
    # 添加节点
    graph_builder.add_node("planner", ppt_planner)
    graph_builder.add_node("agent", ppt_agent)
    
    # 添加边 - 两节点流程
    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "agent")
    graph_builder.add_edge("agent", END)
    
    # 编译图
    return graph_builder.compile()


# 创建图实例（这是langgraph.json中引用的入口点）
ppt_expert_graph = create_ppt_expert_graph()