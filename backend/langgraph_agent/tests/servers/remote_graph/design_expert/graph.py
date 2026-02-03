"""
设计专家智能体 - 两节点架构实现
支持图像生成、修改和设计文件管理
"""

import os
import json
from typing import Dict, List, TypedDict, Annotated
from datetime import datetime

from langchain_core.messages import (
    AIMessage,
    SystemMessage,
    HumanMessage,
    ToolMessage,
    BaseMessage
)
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph
from langgraph.graph.message import add_messages

# 导入设计工具
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tools.design_tools import (
    generate_image,
    modify_image,
    analyze_design_request,
    save_design_file,
    create_design_preview
)


# 定义状态类型
class State(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


def create_design_planner():
    """创建设计规划节点"""
    
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
    
    # 设计规划系统提示词
    planner_prompt = """你是专业设计规划助手，负责分析设计需求并制定设计计划。

【规划任务】
1. 分析用户的设计需求（生成或修改）
2. 确定设计类型和目标效果
3. 识别设计风格和规格要求
4. 制定具体的执行方案
5. 预估输出格式和数量

【输出格式】
📋 设计规划方案：

【设计目标】
- 任务类型：[生成/修改]
- 设计内容：[具体描述]
- 核心需求：[要达成的效果]

【设计规格】
- 风格定位：[简约/专业/创意等]
- 尺寸要求：[具体规格]
- 数量预期：[生成数量]

【执行策略】
- 创意方向：[设计理念]
- 技术路线：[实现方式]
- 质量标准：[评估标准]

【预期输出】
- 交付形式：[图片/文件]
- 输出数量：[具体数量]
- 附加说明：[使用建议]"""

    async def planner_node(state: State) -> dict:
        """设计规划节点 - 使用 ainvoke 调用"""
        messages = state["messages"]

        # 构建规划消息
        planning_messages = [SystemMessage(content=planner_prompt)]

        # 添加用户消息
        if messages:
            last_message = messages[-1]
            content = last_message.content

            # 解析输入 - 支持多种格式
            try:
                query = ""
                image = ""

                if isinstance(content, str):
                    # 尝试解析为 JSON
                    if content.strip().startswith("{"):
                        try:
                            user_input = json.loads(content)
                            query = user_input.get("query", content)
                            image = user_input.get("image", "")
                        except:
                            # JSON 解析失败，使用原始内容
                            query = content
                    else:
                        # 纯文本输入
                        query = content
                else:
                    # 非字符串内容
                    query = str(content)

                # 处理特殊输入
                if query == "？" or query == "?" or not query.strip():
                    query = "生成一个示例设计图"

                # 构建规划请求
                planning_request = f"设计需求：{query}"
                if image:
                    planning_request += f"\n已提供原始图片：是（需要进行修改）"
                else:
                    planning_request += f"\n原始图片：无（需要生成新设计）"

                planning_messages.append(HumanMessage(content=planning_request))
            except Exception as e:
                # 使用原始消息
                planning_messages.extend(messages)
        
        # 使用 ainvoke 进行异步调用
        response = await llm.ainvoke(planning_messages)
        
        # 返回规划结果
        return {"messages": [response]}
    
    return planner_node


def create_design_agent():
    """创建设计执行节点"""
    
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
        generate_image,
        modify_image,
        analyze_design_request,
        save_design_file,
        create_design_preview
    ]
    llm_with_tools = llm.bind_tools(tools)
    
    # 设计执行系统提示词
    system_prompt = """你是专业设计执行智能体，根据前面的规划方案执行设计任务。

你的专长包括：
- 图像生成（海报、Logo、图标、横幅等）
- 图像修改（风格转换、效果调整、元素编辑）
- 设计文件管理（预览生成、文件保存）
- 多样化设计方案（提供多个选项）

【可用工具】
你可以使用以下工具来执行设计任务：
- generate_image: 生成新图像
- modify_image: 修改现有图像
- analyze_design_request: 分析设计需求
- save_design_file: 保存设计文件
- create_design_preview: 创建预览页面

【执行要求】
1. 严格按照规划方案执行
2. 确保设计质量和创意性
3. 提供多个设计选项供选择
4. 生成用户友好的描述信息
5. 按照指定格式返回结果"""

    async def agent_node(state: State) -> dict:
        """设计执行节点 - 处理设计任务并返回特定格式"""
        messages = state["messages"]

        # 解析用户输入 - 查找原始用户消息
        user_message = None
        for msg in messages:
            if hasattr(msg, 'type') and msg.type == 'human':
                user_message = msg
                break
            elif isinstance(msg, HumanMessage):
                user_message = msg
                break

        # 如果没有找到 human 消息，使用第一条消息
        if not user_message and messages:
            user_message = messages[0]

        user_input = {}
        query = ""
        image = ""

        if user_message:
            content = user_message.content

            # 解析输入 - 支持多种格式
            if isinstance(content, str):
                # 尝试解析为 JSON
                if content.strip().startswith("{"):
                    try:
                        user_input = json.loads(content)
                        query = user_input.get("query", content)
                        image = user_input.get("image", "")
                    except:
                        # JSON 解析失败，使用原始内容
                        query = content
                else:
                    # 纯文本输入
                    query = content
            else:
                # 非字符串内容
                query = str(content)

        # 处理特殊输入
        if query == "？" or query == "?" or not query.strip():
            query = "生成一个示例设计图"
        
        # 构建执行消息
        execution_messages = [SystemMessage(content=system_prompt)]
        
        # 添加所有历史消息（包括规划）
        if messages:
            execution_messages.extend(messages)
        
        # 第一次调用 - 获取工具调用决定
        response = await llm_with_tools.ainvoke(execution_messages)
        
        # 初始化结果
        result_messages = []
        generated_images = []
        generated_files = []
        task_description = ""
        
        # 处理工具调用（如果有）
        if hasattr(response, 'tool_calls') and response.tool_calls:
            # 保存带有工具调用的 AIMessage
            result_messages.append(response)
            
            # 执行工具并收集结果
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
                        
                        # 根据工具类型处理结果
                        if tool_name in ['generate_image', 'modify_image']:
                            generated_images.extend(tool_result.get('images', []))
                            if tool_name == 'generate_image':
                                task_description = f"已成功生成'{query}'相关的设计图，共{len(tool_result.get('images', []))}张"
                            else:
                                task_description = f"已成功修改图片，应用了'{query}'的效果"
                        elif tool_name == 'save_design_file':
                            generated_files.append(tool_result)
                            task_description = f"已保存设计文件：{tool_result['name']}"
                        elif tool_name == 'create_design_preview':
                            # 保存预览文件
                            file_info = save_design_file.invoke({
                                'content': tool_result['html_content'],
                                'filename': tool_result['filename'],
                                'file_type': 'html'
                            })
                            generated_files.append(file_info)
                            task_description = f"已创建设计预览文件：{file_info['name']}"
                        
                        # 创建工具消息
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
        
        # 如果没有通过工具调用生成图片，直接根据请求类型生成
        if not generated_images and not generated_files:
            if image:
                # 修改图像
                result = modify_image.invoke({
                    "image_base64": image,
                    "modification": query,
                    "style": "default"
                })
                generated_images = result.get("images", [])
                task_description = f"已成功修改图片，应用了'{query}'的效果，生成了{len(generated_images)}个设计方案"
            else:
                # 生成图像
                result = generate_image.invoke({
                    "prompt": query,
                    "style": "professional",
                    "size": "1024x1024"
                })
                generated_images = result.get("images", [])
                task_description = f"已成功生成'{query}'，创建了{len(generated_images)}张设计图"
        
        # 构建最终的返回消息
        if generated_images:
            # 返回图片类型的ToolMessage
            final_message = ToolMessage(
                content=task_description,  # 用户友好的描述
                tool_call_id="design_task",
                additional_kwargs={
                    "toolCalls": [{
                        "id": f"design_{datetime.now().timestamp()}",
                        "function": {
                            "name": "image",
                            "arguments": json.dumps(generated_images)  # 图片base64数组
                        },
                        "type": "function"
                    }],
                    "name": "image"
                }
            )
        elif generated_files:
            # 返回文件类型的ToolMessage
            file_info = generated_files[0]  # 使用第一个文件
            final_message = ToolMessage(
                content=task_description,  # 用户友好的描述
                tool_call_id="design_file",
                additional_kwargs={
                    "toolCalls": [{
                        "id": f"file_{datetime.now().timestamp()}",
                        "function": {
                            "name": "files",
                            "arguments": json.dumps({
                                "name": file_info["name"],
                                "path": file_info["path"],
                                "date": file_info["date"]
                            })
                        },
                        "type": "function"
                    }],
                    "name": "files"
                }
            )
        else:
            # 如果没有生成内容，返回普通消息
            final_message = AIMessage(content="设计任务已完成，但未生成具体内容。请提供更详细的需求。")
        
        result_messages.append(final_message)
        
        # 返回完整的消息链
        return {"messages": result_messages}
    
    return agent_node


def create_design_expert_graph():
    """创建设计专家智能体图 - 两节点架构"""
    
    # 创建状态图
    graph_builder = StateGraph(State)
    
    # 创建节点
    planner = create_design_planner()
    agent = create_design_agent()
    
    # 添加节点到图
    graph_builder.add_node("planner", planner)
    graph_builder.add_node("agent", agent)
    
    # 定义边（工作流）
    graph_builder.set_entry_point("planner")  # 从planner开始
    graph_builder.add_edge("planner", "agent")  # planner -> agent
    graph_builder.set_finish_point("agent")  # agent结束
    
    # 编译图
    graph = graph_builder.compile()
    
    return graph


# 创建并导出图实例
design_expert_graph = create_design_expert_graph()

# 这允许LangGraph CLI直接运行这个图
if __name__ == "__main__":
    import asyncio
    
    async def test():
        # 测试图像生成
        test_input = {
            "messages": [
                HumanMessage(content=json.dumps({
                    "query": "生成一个校庆海报",
                    "image": ""
                }))
            ]
        }
        
        result = await design_expert_graph.ainvoke(test_input)
        print("生成测试结果:", result)
        
        # 测试图像修改
        test_input2 = {
            "messages": [
                HumanMessage(content=json.dumps({
                    "query": "对这个图片调一下风格，改为简约风",
                    "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA..."
                }))
            ]
        }
        
        result2 = await design_expert_graph.ainvoke(test_input2)
        print("修改测试结果:", result2)
    
    # 运行测试
    # asyncio.run(test())