"""
专业写作智能体服务 - 两节点架构（planner + agent）
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
from tools.write_tools import check_grammar, format_citation, count_paragraphs


class State(TypedDict):
    """图状态定义"""
    messages: Annotated[list, add_messages]


def create_writing_planner():
    """创建写作规划节点"""
    
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
    
    # 写作规划系统提示词
    planner_prompt = """你是专业写作规划助手，负责分析写作需求并制定写作计划。

【规划任务】
1. 分析用户的写作需求和目标
2. 确定文档类型和目标读者
3. 设计内容结构和逻辑框架
4. 规划写作风格和语言基调
5. 制定质量标准和检查要点

【输出格式】
📋 写作规划方案：

【写作目标】
- 文档类型：[报告/文章/提案等]
- 核心目的：[要达成的目标]

【读者分析】
- 目标读者：[读者群体特征]
- 阅读需求：[读者期望获得什么]

【内容架构】
- 总体结构：[引言-主体-结论框架]
- 章节大纲：[具体章节和要点]
- 逻辑脉络：[论述展开方式]

【写作风格】
- 语言风格：[正式/通俗/专业等]
- 语气基调：[客观/亲切/权威等]
- 表达特点：[简洁/详细/生动等]

【质量要求】
- 信息准确性：[事实核查要点]
- 逻辑严密性：[论证要求]
- 可读性标准：[易读性指标]"""

    async def planner_node(state: State) -> dict:
        """写作规划节点 - 使用 ainvoke 调用"""
        messages = state["messages"]
        
        # 构建规划消息
        planning_messages = [SystemMessage(content=planner_prompt)]
        
        # 添加用户消息
        if messages:
            planning_messages.extend(messages)
        
        # 使用 ainvoke 进行异步调用
        response = await llm.ainvoke(planning_messages)
        
        # 返回规划结果（response已经是AIMessage对象）
        return {"messages": [response]}
    
    return planner_node


def create_writing_agent():
    """创建专业写作执行节点"""
    
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
        check_grammar,
        format_citation,
        count_paragraphs
    ]
    llm_with_tools = llm.bind_tools(tools)
    
    # 专业写作执行系统提示词
    system_prompt = """你是一位专业的写作智能体，根据前面的规划方案执行写作任务。

你的专长包括：
- 商业文档撰写（报告、提案、备忘录等）
- 技术文档编写（说明书、用户指南、API文档等）
- 创意内容创作（文章、博客、营销文案等）
- 学术写作（论文、研究报告、分析文章等）
- 多种文体和风格适配

【可用工具】
你可以使用以下工具来辅助写作：
- get_current_time: 获取当前时间
- search_web: 搜索网络获取参考信息
- read_file/write_file: 读取或保存文档
- word_count: 统计字数和段落
- check_grammar: 检查语法问题
- format_citation: 格式化引用文献
- count_paragraphs: 分析段落结构

【执行要求】
基于前面的规划方案，创作高质量的专业内容：
1. 严格遵循规划的结构和框架
2. 保持规划确定的写作风格和语气
3. 满足目标读者的阅读需求
4. 确保内容准确、逻辑清晰、语言流畅
5. 注重格式规范和专业性
6. 适当使用工具增强内容质量

输出完整、详细、可直接使用的文档内容。"""

    async def agent_node(state: State) -> dict:
        """专业写作执行节点 - 使用 ainvoke 调用"""
        messages = state["messages"]
        
        # 构建执行消息（包含规划信息）
        execution_messages = [SystemMessage(content=system_prompt)]
        
        # 添加所有历史消息（包括规划）
        if messages:
            execution_messages.extend(messages)
        
        # 第一次调用 - 获取工具调用决定
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
            
            # 第二次调用 - 基于工具结果生成最终响应
            final_messages = execution_messages + result_messages
            final_response = await llm.ainvoke(final_messages)
            result_messages.append(final_response)
        else:
            # 没有工具调用，直接返回响应
            result_messages.append(response)
        
        # 返回完整的消息链
        return {"messages": result_messages}
    
    return agent_node


def create_write_expert_graph():
    """创建专业写作智能体图 - 两节点架构"""
    
    # 创建状态图
    graph_builder = StateGraph(State)
    
    # 创建规划节点和执行节点
    writing_planner = create_writing_planner()
    writing_agent = create_writing_agent()
    
    # 添加节点
    graph_builder.add_node("planner", writing_planner)
    graph_builder.add_node("agent", writing_agent)
    
    # 添加边 - 两节点流程
    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "agent")
    graph_builder.add_edge("agent", END)
    
    # 编译图
    return graph_builder.compile()


# 创建图实例（这是langgraph.json中引用的入口点）
write_expert_graph = create_write_expert_graph()