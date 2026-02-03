"""
Broadcast博客写作专家智能体服务 - 两节点架构（planner + agent）
"""

import os
import sys
import asyncio
from typing import Annotated, AsyncIterator
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage,SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 添加tools目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.base_tools import get_current_time, search_web, read_file, write_file, word_count
from tools.broadcast_tools import analyze_seo, score_title, format_social_media


class State(TypedDict):
    """图状态定义"""
    messages: Annotated[list, add_messages]


def create_broadcast_planner():
    """创建博客写作规划节点"""
    
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
    
    # 博客写作规划系统提示词
    planner_prompt = """你是内容营销规划助手，负责分析需求并制定传播策略。

【规划任务】
1. 分析内容营销需求和目标
2. 确定目标受众和传播渠道
3. 设计内容结构和SEO策略
4. 规划内容风格和互动设计
5. 制定发布和推广方案

【输出格式】
📋 内容营销规划方案：

【营销目标】
- 内容定位：[主题角度和价值主张]
- 传播目标：[期望达成的效果]

【受众分析】
- 目标人群：[用户画像]
- 痛点需求：[解决什么问题]
- 阅读习惯：[内容偏好]

【SEO策略】
- 核心关键词：[主要关键词]
- 长尾关键词：[相关词组]
- 内链外链：[链接策略]

【内容架构】
- 标题策略：[吸引力设计]
- 段落结构：[内容组织]
- 视觉元素：[图表/信息图]

【传播策略】
- 发布渠道：[平台选择]
- 发布时机：[最佳时间]
- 互动设计：[CTA/引导]
- 病毒因子：[分享动机]

【成效指标】
- 阅读指标：[浏览/停留]
- 互动指标：[评论/分享]
- 转化指标：[注册/购买]"""

    async def planner_node(state: State) -> AsyncIterator[dict]:
        """博客规划节点 - 异步流式输出"""
        messages = state["messages"]
        
        # 构建规划消息
        planning_messages = [SystemMessage(content=planner_prompt)]
        
        # 添加用户消息
        if messages:
            planning_messages.extend(messages)
        
        # 使用 astream 进行异步流式调用，累积内容
        accumulated_content = ""
        async for chunk in llm.astream(planning_messages):
            # 处理流式输出的每个块
            if hasattr(chunk, 'content') and chunk.content:
                accumulated_content += chunk.content
                # 只返回LLM生成的内容
                yield {"messages": [AIMessage(content=accumulated_content)]}
        
        # 如果没有内容生成，返回空消息
        if not accumulated_content:
            yield {"messages": [AIMessage(content="")]}
    
    return planner_node


def create_broadcast_agent():
    """创建博客写作执行节点"""
    
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
        analyze_seo,
        score_title,
        format_social_media
    ]
    llm_with_tools = llm.bind_tools(tools)
    
    # 博客写作执行系统提示词
    system_prompt = """你是一位专业的博客写作与内容营销专家，根据前面的规划方案创作营销内容。

【核心专长】
🎯 内容营销战略
• 目标受众分析与用户画像构建
• 内容主题规划与发布日程
• 品牌声音定位与调性把控
• 跨平台内容适配策略

📈 SEO优化技能
• 关键词研究与长尾词挖掘
• 标题优化与元标签设置
• 内链建设与外链策略
• 技术SEO与页面性能优化
• Google Analytics数据分析

✍️ 写作技巧精通
• 吸引眼球的标题创作
• 结构化内容组织（AIDA、PAS框架）
• 故事化叙述与情感共鸣
• 行动召唤(CTA)设计

【可用工具】
你可以使用以下工具来辅助内容营销：
- get_current_time: 获取当前时间
- search_web: 搜索网络获取参考信息
- read_file/write_file: 读取或保存文档
- word_count: 统计字数
- analyze_seo: 分析SEO优化
- score_title: 评估标题吸引力
- format_social_media: 格式化社交媒体内容

【执行要求】
基于前面的规划方案，创作高质量的博客内容：
1. 遵循SEO策略，合理布局关键词
2. 按照规划的结构组织内容
3. 保持目标受众喜欢的风格
4. 设计有效的互动元素
5. 确保内容原创性和价值性

输出完整的博客文章，包括：
- 吸引人的标题
- 结构化的正文内容
- SEO优化建议
- 社交媒体推广文案
- 关键词和标签建议"""

    async def agent_node(state: State) -> AsyncIterator[dict]:
        """博客写作执行节点 - 异步流式输出"""
        messages = state["messages"]
        
        # 构建执行消息（包含规划信息）
        execution_messages = [SystemMessage(content=system_prompt)]
        
        # 添加所有历史消息（包括规划）
        if messages:
            execution_messages.extend(messages)
        
        # 第一次调用 - 获取工具调用决定（非流式，因为需要完整的工具调用信息）
        response = await llm_with_tools.ainvoke(execution_messages)
        
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
            
            # 第二次调用 - 基于工具结果生成最终响应（可以流式）
            final_messages = execution_messages + result_messages
            
            # 流式生成最终响应
            accumulated_content = ""
            async for chunk in llm.astream(final_messages):
                if hasattr(chunk, 'content') and chunk.content:
                    accumulated_content += chunk.content
                    # 创建临时的 AIMessage 用于流式输出
                    temp_final_message = AIMessage(content=accumulated_content)
                    # 返回完整的消息链加上正在生成的最终消息
                    yield {"messages": result_messages + [temp_final_message]}
            
            # 如果没有生成内容，添加空的最终消息
            if not accumulated_content:
                result_messages.append(AIMessage(content=""))
                yield {"messages": result_messages}
        else:
            # 没有工具调用，直接返回响应
            result_messages.append(response)
            yield {"messages": result_messages}
    
    return agent_node


def create_broadcast_expert_graph():
    """创建博客写作专家智能体图 - 两节点架构，支持异步流式输出"""
    
    # 创建状态图
    graph_builder = StateGraph(State)
    
    # 创建规划节点和执行节点
    broadcast_planner = create_broadcast_planner()
    broadcast_agent = create_broadcast_agent()
    
    # 添加节点
    graph_builder.add_node("planner", broadcast_planner)
    graph_builder.add_node("agent", broadcast_agent)  # agent节点支持异步流式输出
    
    # 添加边 - 两节点流程
    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "agent")
    graph_builder.add_edge("agent", END)
    
    # 编译图 - 启用流式支持
    return graph_builder.compile()


# 创建图实例（这是langgraph.json中引用的入口点）
broadcast_expert_graph = create_broadcast_expert_graph()