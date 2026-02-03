"""
Web网页开发专家智能体服务 - 两节点架构（planner + agent）
"""

import os
import sys
from typing import Annotated, Iterator
from typing_extensions import TypedDict

from langchain_core.messages import BaseMessage,SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

# 添加tools目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from tools.base_tools import get_current_time, search_web, read_file, write_file, word_count
from tools.web_tools import generate_html_preview, validate_css, check_responsive


class State(TypedDict):
    """图状态定义"""
    messages: Annotated[list, add_messages]


def create_web_planner():
    """创建Web开发规划节点"""
    
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
    
    # Web开发规划系统提示词
    planner_prompt = """你是Web开发规划助手，负责分析需求并设计技术方案。

【规划任务】
1. 分析用户的Web开发需求
2. 选择合适的技术栈和框架
3. 设计组件结构和架构
4. 规划实现步骤和优先级
5. 制定性能和体验优化策略

【输出格式】
📋 Web开发规划方案：

【需求分析】
- 功能需求：[核心功能列表]
- 用户体验：[交互和视觉要求]

【技术选型】
- 前端框架：[React/Vue/Angular等]
- 样式方案：[CSS框架/预处理器]
- 构建工具：[Webpack/Vite等]
- 其他工具：[状态管理/路由等]

【架构设计】
- 目录结构：[项目组织方式]
- 组件划分：[组件层次和职责]
- 数据流向：[状态管理方案]

【实现步骤】
1. 基础搭建：[环境配置]
2. 核心功能：[主要模块]
3. 优化完善：[性能/体验]

【优化要点】
- 性能优化：[加载/渲染优化]
- 响应式设计：[多设备适配]
- 无障碍性：[可访问性考虑]"""

    def planner_node(state: State) -> Iterator[dict]:
        """Web规划节点 - 同步流式输出"""
        messages = state["messages"]
        
        # 构建规划消息
        planning_messages = [SystemMessage(content=planner_prompt)]
        
        # 添加用户消息
        if messages:
            planning_messages.extend(messages)
        
        # 使用 stream 进行同步流式调用，累积内容
        accumulated_content = ""
        for chunk in llm.stream(planning_messages):
            # 处理流式输出的每个块
            if hasattr(chunk, 'content') and chunk.content:
                accumulated_content += chunk.content
                # 只返回LLM生成的内容
                yield {"messages": [AIMessage(content=accumulated_content)]}
        
        # 如果没有内容生成，返回空消息
        if not accumulated_content:
            yield {"messages": [AIMessage(content="")]}
    
    return planner_node


def create_web_agent():
    """创建Web开发执行节点"""
    
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
        generate_html_preview,
        validate_css,
        check_responsive
    ]
    llm_with_tools = llm.bind_tools(tools)
    
    # Web开发执行系统提示词
    system_prompt = """你是一位资深的Web开发专家，根据前面的规划方案实现Web开发任务。

【核心技术栈】
🔧 前端开发
• HTML5/CSS3：语义化标签、现代布局（Flexbox/Grid）
• JavaScript/ES6+：原生JS、异步编程、模块化
• TypeScript：类型安全、接口设计、泛型应用

📚 框架生态
• React.js：组件化开发、Hooks、状态管理
• Vue.js：响应式数据、组合式API、生态工具
• Angular：企业级应用、依赖注入、RxJS
• Next.js/Nuxt.js：全栈框架、SSR/SSG

🎨 样式与设计
• CSS预处理器：Sass/Less/Stylus
• UI框架：Tailwind CSS、Material-UI、Ant Design
• 响应式设计：移动优先、断点管理
• 动画效果：CSS Animation、Framer Motion

【可用工具】
你可以使用以下工具来辅助Web开发：
- get_current_time: 获取当前时间
- search_web: 搜索网络获取参考信息
- read_file/write_file: 读取或保存文档
- word_count: 统计字数
- generate_html_preview: 生成HTML预览
- validate_css: 验证CSS代码
- check_responsive: 检查响应式设计

【执行要求】
基于前面的规划方案，提供完整的代码实现：
• 遵循规划的技术选型和架构设计
• 实现规划中的功能需求
• 包含详细的代码注释
• 确保代码的可维护性和扩展性
• 考虑浏览器兼容性和性能优化

输出完整、可运行的HTML/CSS/JavaScript代码。"""

    def agent_node(state: State) -> Iterator[dict]:
        """Web开发执行节点 - 同步流式输出"""
        messages = state["messages"]
        
        # 构建执行消息（包含规划信息）
        execution_messages = [SystemMessage(content=system_prompt)]
        
        # 添加所有历史消息（包括规划）
        if messages:
            execution_messages.extend(messages)
        
        # 第一次调用 - 获取工具调用决定（非流式，因为工具调用需要完整响应）
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
            
            # 返回完整的消息链（流式模拟，但保留完整消息）
            yield {"messages": result_messages}
        else:
            # 没有工具调用，直接返回响应
            result_messages.append(response)
            
            # 返回消息链（流式模拟）
            yield {"messages": result_messages}
    
    return agent_node


def create_web_expert_graph():
    """创建Web开发专家智能体图 - 两节点架构，支持流式输出"""
    
    # 创建状态图
    graph_builder = StateGraph(State)
    
    # 创建规划节点和执行节点
    web_planner = create_web_planner()
    web_agent = create_web_agent()
    
    # 添加节点
    graph_builder.add_node("planner", web_planner)
    graph_builder.add_node("agent", web_agent)  # agent节点支持流式输出
    
    # 添加边 - 两节点流程
    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "agent")
    graph_builder.add_edge("agent", END)
    
    # 编译图 - 启用流式支持
    return graph_builder.compile()


# 创建图实例（这是langgraph.json中引用的入口点）
web_expert_graph = create_web_expert_graph()