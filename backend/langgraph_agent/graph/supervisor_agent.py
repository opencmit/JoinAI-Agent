"""
Supervisor 智能体节点实现
负责路由决策和智能体协调
"""

'''
import os
import logging
import asyncio
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from langgraph_agent.graph.state import AgentState
from langgraph_agent.config import llm_config
from langgraph_agent.prompts.supervisor_prompt import (
    create_supervisor_decision_prompt,
    parse_supervisor_decision,
    get_latest_user_message
)

logger = logging.getLogger(__name__)

async def supervisor_agent_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    Supervisor 智能体节点 - 负责路由决策
    
    Args:
        state: 智能体状态
        config: 运行配置
        
    Returns:
        AgentState: 更新后的状态，包含路由决策
    """
    logger.info("=== Supervisor 智能体开始路由决策 ===")
    
    # 🔥 新增：更新迭代计数器，防止无限循环
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    current_iteration = state["iteration_count"]
    max_iterations = state.get("max_iterations", 50)
    
    logger.info(f"🔄 当前迭代次数: {current_iteration}/{max_iterations}")
    
    # 如果迭代次数接近上限，记录警告
    if current_iteration >= max_iterations * 0.8:  # 80%时开始警告
        logger.warning(f"⚠️ 迭代次数接近上限: {current_iteration}/{max_iterations}")
    
    try:
        # 1. 检查是否有A2A智能体，如果没有直接路由到通用智能体
        a2a_agents = state.get("a2a_agents", [])
        if not a2a_agents:
            logger.info("没有A2A智能体，直接路由到通用智能体")
            state["route_to_a2a"] = None
            state["supervisor_decision"] = {
                "analysis": "没有配置A2A智能体",
                "recommended_agent": "通用智能体",
                "confidence": 1.0,
                "reasoning": "系统中没有配置A2A智能体，直接使用通用智能体处理",
                "fallback": "通用智能体"
            }
            return state
        
        # 2. 获取用户最新消息和工作流状态
        user_message = get_latest_user_message(state)
        logger.info(f"用户消息: {user_message}")
        
        # 🔥 检查是否为多步骤工作流的后续步骤
        workflow_plan = state.get("workflow_plan")
        current_step_index = state.get("current_step_index", 0)
        execution_results = state.get("execution_results", {})
        
        # 🔥 重置当前步骤完成标志（在Supervisor节点内重置）
        if state.get("current_step_completed", False):
            state["current_step_completed"] = False
            logger.info("🔄 重置当前步骤完成标志")
        
        # 🔥 检查是否为多步骤工作流（包括初始状态和后续步骤）
        if workflow_plan:
            workflow_type = workflow_plan.get("workflow_type", "single_step")
            total_steps = workflow_plan.get("total_steps", 1)
            
            logger.info(f"🔄 处理工作流，类型: {workflow_type}, 当前步骤索引: {current_step_index}, 总步骤: {total_steps}")
            
            # 🔥 关键修复：检查单步任务是否已完成
            if workflow_type == "single_step":
                # 单步任务：检查是否有messages且任务已开始
                messages = state.get("messages", [])
                has_agent_response = False
                
                # 检查是否有来自智能体的响应（不包括supervisor的决策消息）
                for msg in reversed(messages):
                    if hasattr(msg, 'content') and isinstance(msg.content, str):
                        # 跳过supervisor的路由决策消息
                        if not msg.content.startswith("🔀 **路由决策**"):
                            has_agent_response = True
                            break
                
                if has_agent_response and current_step_index >= total_steps:
                    logger.info("🎉 单步任务已完成")
                    state["completed"] = True
                    # 为单步任务添加完成确认消息
                    completion_message = "✅ **任务完成** - 您的请求已经处理完毕。"
                    state["messages"].append(AIMessage(content=completion_message))
                    return state
            elif workflow_type == "multi_step":
                # 多步骤工作流逻辑保持不变
                logger.info(f"🔄 处理多步骤工作流，当前步骤索引: {current_step_index}")
                
                # 检查是否还有待执行的步骤
                if current_step_index < total_steps:
                    # 获取下一步骤信息
                    steps = workflow_plan.get("steps", [])
                    if current_step_index < len(steps):
                        next_step = steps[current_step_index]
                        next_agent_type = next_step.get("agent_type", "通用智能体")
                        next_description = next_step.get("description", "")
                        
                        logger.info(f"🎯 执行工作流步骤 {current_step_index + 1}/{total_steps}: {next_description}")
                        
                        # 构建包含之前执行结果的任务指令
                        task_instruction = build_workflow_step_instruction(
                            user_message, 
                            next_step, 
                            execution_results, 
                            current_step_index + 1
                        )
                        
                        # 设置下一步骤的路由决策
                        decision = {
                            "analysis": f"多步骤工作流第{current_step_index + 1}步，共{total_steps}步",
                            "recommended_agent": next_agent_type,
                            "confidence": 0.95,
                            "reasoning": f"根据工作流计划执行第{current_step_index + 1}步：{next_description}",
                            "task_instruction": task_instruction,
                            "fallback": "通用智能体",
                            "workflow_type": "multi_step",
                            "workflow_plan": workflow_plan
                        }
                        
                        if decision["recommended_agent"] == "通用智能体":
                            state["route_to_a2a"] = None
                        else:
                            state["route_to_a2a"] = decision["recommended_agent"]
                        
                        state["supervisor_decision"] = decision
                        logger.info(f"🔄 工作流步骤路由: {decision['recommended_agent']}")
                        
                        # 🔥 设置工作流计划并更新步骤索引（继续保持工作流状态）
                        # 🔥 关键修复：确保workflow_plan中包含workflow_type字段
                        if "workflow_type" not in workflow_plan:
                            workflow_plan["workflow_type"] = "multi_step"
                        state["workflow_plan"] = workflow_plan
                        state["current_step_index"] = current_step_index
                        
                        return state
                else:
                    # 所有步骤已完成，标记工作流完成
                    logger.info("🎉 多步骤工作流已完成所有步骤")
                    state["completed"] = True
                    completion_message = create_workflow_completion_message(execution_results, workflow_plan)
                    state["messages"].append(AIMessage(content=completion_message))
                    return state
        
        # 3. 创建LLM实例进行决策
        llm_instance = create_supervisor_llm_instance(state, config)
        
        # 4. 尝试使用LLM进行智能决策
        decision = None
        if llm_instance:
            try:
                decision = await make_llm_decision(state, user_message, llm_instance)
                logger.info(f"LLM决策结果: {decision}")
            except Exception as e:
                logger.error(f"LLM决策失败: {str(e)}")
                decision = None
        
        # 5. 如果LLM决策失败，使用默认的通用智能体决策
        if not decision:
            logger.warning("LLM决策失败，使用默认通用智能体决策")
            
            # 记录决策失败的详细信息用于监控
            failure_info = {
                "user_message_length": len(user_message),
                "a2a_agents_count": len(a2a_agents),
                "failed_agents_count": len(state.get("failed_a2a_agents", [])),
                "iteration_count": current_iteration
            }
            logger.info(f"LLM决策失败详情: {failure_info}")
            
            # 构建更详细的reasoning信息
            reasoning_parts = ["LLM路由决策失败"]
            if state.get("failed_a2a_agents"):
                reasoning_parts.append(f"已排除{len(state.get('failed_a2a_agents', []))}个失败的智能体")
            if len(a2a_agents) > 0:
                reasoning_parts.append(f"系统中有{len(a2a_agents)}个可用的A2A智能体")
            reasoning_parts.append("为确保任务能够完成，使用通用智能体处理用户请求")
            
            decision = {
                "analysis": "LLM决策失败，使用默认fallback策略",
                "recommended_agent": "通用智能体",
                "confidence": 0.7,
                "reasoning": "；".join(reasoning_parts),
                "fallback": "通用智能体",
                "llm_failure": True,  # 标记这是LLM失败后的决策
                "failure_info": failure_info
            }
        
        # 🚨 关键修复：强制过滤失败的智能体，防止LLM重复推荐
        failed_agents = state.get("failed_a2a_agents", [])
        if decision and decision.get("recommended_agent") in failed_agents:
            logger.warning(f"🚫 LLM推荐的智能体 {decision['recommended_agent']} 已失败，强制fallback到通用智能体")
            
            # 获取失败智能体的名称用于reasoning
            failed_agent_name = decision['recommended_agent']
            original_reasoning = decision.get('reasoning', '原始LLM推荐')
            
            decision = {
                "analysis": f"LLM推荐的智能体已失败: {decision['recommended_agent']}",
                "recommended_agent": "通用智能体",
                "confidence": 0.8,
                "reasoning": f"原本推荐使用 {failed_agent_name}，但该智能体之前执行失败。为确保任务能够完成，现改为使用通用智能体处理。原始推荐理由：{original_reasoning}",
                "fallback": "通用智能体",
                "failure_reason": f"智能体 {failed_agent_name} 执行失败",
                "retry_count": state.get("supervisor_retry_count", 0)
            }

        # 🔥 新增：验证推荐的智能体ID格式是否正确
        if decision and decision.get("recommended_agent") != "通用智能体":
            recommended_agent = decision.get("recommended_agent")
            valid_agent_ids = []
            
            # 收集所有有效的智能体ID
            for agent in a2a_agents:
                agent_id = agent.get("agent_id") or agent.get("agent_ID") or agent.get("agentId", "unknown")
                valid_route_id = f"a2a_{agent_id}"
                valid_agent_ids.append(valid_route_id)
            
            # 检查推荐的ID是否在有效列表中
            if recommended_agent not in valid_agent_ids:
                logger.error(f"🚫 LLM推荐了无效的智能体ID: {recommended_agent}")
                logger.error(f"🔍 有效的智能体ID列表: {valid_agent_ids}")
                
                # 记录无效的智能体ID为失败
                if recommended_agent not in failed_agents:
                    failed_agents.append(recommended_agent)
                    state["failed_a2a_agents"] = failed_agents
                
                # 增加supervisor重试计数
                current_retry_count = state.get("supervisor_retry_count", 0) + 1
                state["supervisor_retry_count"] = current_retry_count
                
                # 🔥 改进策略：优先重新决策，只有重试过多时才强制使用通用智能体
                if current_retry_count >= 5:
                    logger.warning(f"🚨 Supervisor已重试 {current_retry_count} 次，强制使用通用智能体")
                    # 强制使用通用智能体
                    original_reasoning = decision.get('reasoning', '原始LLM推荐')
                    decision = {
                        "analysis": f"经过多次重试仍推荐无效智能体ID: {recommended_agent}",
                        "recommended_agent": "通用智能体",
                        "confidence": 0.8,
                        "reasoning": f"经过 {current_retry_count} 次重试，LLM仍推荐无效的智能体ID。有效ID: {', '.join(valid_agent_ids)}。为避免无限循环，强制使用通用智能体。最后推荐理由：{original_reasoning}",
                        "fallback": "通用智能体",
                        "failure_reason": f"重试次数过多，最后无效ID: {recommended_agent}",
                        "retry_count": current_retry_count
                    }
                    state["route_to_a2a"] = None
                    logger.info("🔄 已设置路由到通用智能体")
                else:
                    logger.warning(f"🔄 第 {current_retry_count} 次重试，记录无效ID并重新进行supervisor决策")
                    
                    # 添加重试消息给用户
                    retry_message = AIMessage(content=f"⚠️ 检测到智能体路由错误（第{current_retry_count}次），正在重新选择合适的智能体...")
                    state["messages"].append(retry_message)
                    
                    # 🔥 关键修复：直接在supervisor内部重新进行决策，而不是依赖路由
                    logger.info(f"🔄 当前重试次数: {current_retry_count}/5，立即重新进行决策")
                    
                    # 清除之前的决策，重新开始决策过程
                    state["route_to_a2a"] = None
                    
                    # 🔄 重新执行决策逻辑（从第4步开始）
                    logger.info("🔄 重新调用决策引擎...")
                    
                    # 重新尝试LLM决策
                    llm_instance = create_supervisor_llm_instance(state, config)
                    new_decision = None
                    if llm_instance:
                        try:
                            new_decision = await make_llm_decision(state, user_message, llm_instance)
                            logger.info(f"🔄 重新决策结果: {new_decision}")
                        except Exception as e:
                            logger.error(f"🔄 重新决策LLM调用失败: {str(e)}")
                    
                    # 如果LLM重新决策也失败，使用默认决策
                    if not new_decision:
                        logger.info("🔄 重新决策也失败，使用默认通用智能体决策")
                        new_decision = {
                            "analysis": "LLM重新决策失败",
                            "recommended_agent": "通用智能体",
                            "confidence": 0.7,
                            "reasoning": "LLM多次决策失败，使用通用智能体确保任务能够完成",
                            "fallback": "通用智能体"
                        }
                    
                    # 更新decision为新的决策结果，继续后续流程
                    decision = new_decision
                    logger.info(f"🔄 重新决策完成，新推荐: {decision.get('recommended_agent')}")
                    
                    # 继续执行验证逻辑（让它重新检查新的决策）
        
        # 6. 设置路由状态
        if decision["recommended_agent"] == "通用智能体":
            state["route_to_a2a"] = None
            logger.info("路由决策: 通用智能体")
        else:
            state["route_to_a2a"] = decision["recommended_agent"]
            logger.info(f"路由决策: {decision['recommended_agent']}")
        
        # 7. 🔥 处理工作流计划（对于单步和多步任务都要设置）
        workflow_plan = decision.get("workflow_plan")
        if decision.get("workflow_type") == "multi_step":
            if workflow_plan:
                # 🔥 关键修复：确保workflow_plan中包含workflow_type字段
                workflow_plan["workflow_type"] = "multi_step"
                state["workflow_plan"] = workflow_plan
                state["current_step_index"] = 0  # 重置为第一步
                logger.info(f"🔄 初始化多步骤工作流，总步数: {workflow_plan.get('total_steps', 1)}")
        else:
            # 🔥 新增：为单步任务也创建workflow_plan
            if workflow_plan:
                # 使用LLM提供的workflow_plan，确保包含workflow_type
                workflow_plan["workflow_type"] = "single_step"
                state["workflow_plan"] = workflow_plan
            else:
                # 为单步任务创建默认的workflow_plan
                state["workflow_plan"] = {
                    "workflow_type": "single_step",
                    "total_steps": 1,
                    "current_step": 1,
                    "steps": [{
                        "step_id": 1,
                        "description": decision.get("reasoning", "执行单步任务"),
                        "agent_type": decision.get("recommended_agent", "通用智能体"),
                        "dependencies": [],
                        "outputs": ["任务完成结果"]
                    }]
                }
            state["current_step_index"] = 0
            logger.info(f"🔄 设置单步任务工作流：{decision.get('recommended_agent', '通用智能体')}")
        
        # 8. 记录决策信息
        state["supervisor_decision"] = decision
        
        # 9. 添加决策说明消息（可选，用于调试）
        if logger.isEnabledFor(logging.INFO):
            workflow_info = ""
            if decision.get("workflow_type") == "multi_step":
                workflow_plan = decision.get("workflow_plan", {})
                total_steps = workflow_plan.get("total_steps", 1)
                steps = workflow_plan.get("steps", [])
                
                # 🔥 新增：显示完整的工作流步骤规划
                if steps:
                    step_summary = []
                    for i, step in enumerate(steps, 1):
                        agent_type = step.get("agent_type", "未知智能体")
                        description = step.get("description", "未知任务")
                        
                        # 美化智能体名称显示
                        if agent_type == "通用智能体":
                            agent_display = "通用智能体"
                        elif agent_type.startswith("a2a_"):
                            # 从A2A智能体列表中找到对应的中文名称
                            agent_display = agent_type
                            for agent in state.get("a2a_agents", []):
                                agent_id = agent.get("agent_id") or agent.get("agent_ID") or agent.get("agentId", "")
                                if f"a2a_{agent_id}" == agent_type:
                                    agent_display = agent.get("name", agent_type)
                                    break
                        else:
                            agent_display = agent_type
                        
                        step_summary.append(f"第{i}步: {description} (执行者: {agent_display})")
                    
                    steps_detail = "\n".join([f"   {step}" for step in step_summary])
                    workflow_info = f"\n\n📋 **多步骤工作流规划** (共{total_steps}步):\n{steps_detail}"
                else:
                    workflow_info = f" (多步骤工作流 共{total_steps}步)"
            
            decision_msg = f"🔀 **路由决策**: {decision['reasoning']}{workflow_info}"
            state["messages"].append(AIMessage(content=decision_msg))
        
        logger.info("=== Supervisor 路由决策完成 ===")
        return state
        
    except Exception as e:
        logger.error(f"Supervisor决策过程异常: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 异常情况下默认路由到通用智能体
        state["route_to_a2a"] = None
        state["supervisor_decision"] = {
            "analysis": "决策过程出现异常",
            "recommended_agent": "通用智能体",
            "confidence": 0.5,
            "reasoning": f"决策异常，默认使用通用智能体: {str(e)}",
            "fallback": "通用智能体"
        }
        return state

def create_supervisor_llm_instance(state: AgentState, config: RunnableConfig) -> Optional[ChatOpenAI]:
    """创建Supervisor专用的LLM实例"""
    try:
        # 获取模型配置 - 优先级逻辑：state.get("model") > config.get("configurable", {}).get("model_name", llm_config.BASE_LLM)
        model_name = (
            state.get("model") 
            if "model" in state and state.get("model") is not None
            else config.get("configurable", {}).get("model_name", llm_config.BASE_LLM)
        )
        openai_api_key = config.get("configurable", {}).get("model_key", os.getenv("OPENAI_API_KEY"))
        
        if not model_name:
            logger.error("未配置模型名称")
            return None
        
        # 创建LLM实例
        llm_instance = ChatOpenAI(
            base_url=os.getenv("OPENAI_BASE_URL"),
            model=model_name,
            model_kwargs={
                "extra_headers": {
                    "Authorization": f"Bearer {openai_api_key}"
                }
            },
            temperature=0.1  # 设置较低的温度以获得更确定的决策
        )
        
        logger.info(f"Supervisor LLM实例创建成功: {model_name}")
        return llm_instance
        
    except Exception as e:
        logger.error(f"创建Supervisor LLM实例失败: {str(e)}")
        return None

async def make_llm_decision(state: AgentState, user_message: str, llm_instance: ChatOpenAI) -> Optional[Dict[str, Any]]:
    """使用LLM进行路由决策（带重试机制）"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            # 1. 创建决策提示词
            decision_prompt = create_supervisor_decision_prompt(state, user_message)
            
            # 2. 调用LLM
            messages = [HumanMessage(content=decision_prompt)]
            
            logger.info(f"调用LLM进行路由决策... (尝试 {attempt + 1}/{max_retries})")
            response = await llm_instance.ainvoke(messages)
            
            # 3. 解析决策结果
            decision = parse_supervisor_decision(response.content)
            
            if decision and decision.get("recommended_agent"):
                logger.info(f"LLM决策成功: {decision['recommended_agent']} (尝试 {attempt + 1}/{max_retries})")
                return decision
            else:
                logger.warning(f"LLM决策解析失败 (尝试 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    # 等待一下再重试
                    await asyncio.sleep(1)
                    continue
                
        except Exception as e:
            logger.error(f"LLM决策过程异常 (尝试 {attempt + 1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                # 对于可重试的错误，等待后重试
                if any(keyword in str(e).lower() for keyword in ["timeout", "connection", "network", "temporary"]):
                    logger.info(f"检测到可重试错误，等待后重试...")
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                    continue
            
    logger.error(f"LLM决策在 {max_retries} 次尝试后仍然失败")
    return None




def should_enable_supervisor_mode(state: AgentState) -> bool:
    """判断是否应该启用Supervisor模式"""
    # 检查是否有A2A智能体配置
    a2a_agents = state.get("a2a_agents", [])
    if len(a2a_agents) > 0:
        logger.info(f"检测到 {len(a2a_agents)} 个A2A智能体，启用Supervisor模式")
        return True
    
    # 检查是否在输入中有A2A智能体
    if "input" in state:
        input_section = state["input"]
        if isinstance(input_section, dict):
            input_a2a = input_section.get("a2a_agents", [])
            if len(input_a2a) > 0:
                logger.info(f"输入中检测到 {len(input_a2a)} 个A2A智能体，启用Supervisor模式")
                # 将A2A智能体复制到主状态中
                state["a2a_agents"] = input_a2a
                return True
    
    # 检查是否在input_data中有A2A智能体
    if "input_data" in state:
        input_data = state["input_data"]
        if isinstance(input_data, dict):
            input_data_a2a = input_data.get("a2a_agents", [])
            if len(input_data_a2a) > 0:
                logger.info(f"input_data中检测到 {len(input_data_a2a)} 个A2A智能体，启用Supervisor模式")
                # 将A2A智能体复制到主状态中
                state["a2a_agents"] = input_data_a2a
                return True
    
    logger.info("未检测到A2A智能体，跳过Supervisor模式")
    return False

# 使用示例和测试功能
if __name__ == "__main__":
    import asyncio
    from langgraph_agent.graph.state import create_initial_state
    
    async def test_supervisor_decision():
        """测试Supervisor决策功能"""
        print("=== 测试Supervisor决策功能 ===")
        
        # 创建测试状态
        test_state = create_initial_state({
            "messages": [],
            "a2a_agents": [
                {
                    "agent_id": "data_analyst",
                    "name": "数据分析师",
                    "description": "专业的数据分析和可视化智能体"
                },
                {
                    "agent_id": "document_writer",
                    "name": "文档助手",
                    "description": "专业的文档编写和格式化智能体"
                }
            ],
            "input": {
                "message": [{"type": "human", "content": "帮我分析这份销售数据"}]
            }
        })
        
        # 测试启用条件
        should_enable = should_enable_supervisor_mode(test_state)
        print(f"是否启用Supervisor模式: {should_enable}")
        
        print("Supervisor统计信息: 规则引擎已移除")
    
    # 运行测试
    # asyncio.run(test_supervisor_decision())
    print("Supervisor Agent模块加载成功")


def build_workflow_step_instruction(user_message: str, step_info: dict, execution_results: dict, step_number: int) -> str:
    """
    构建工作流步骤的任务指令，包含前面所有步骤的执行结果
    
    Args:
        user_message: 原始用户消息
        step_info: 当前步骤信息
        execution_results: 前面步骤的执行结果
        step_number: 当前步骤编号
        
    Returns:
        str: 完整的任务指令
    """
    step_description = step_info.get("description", "")
    agent_type = step_info.get("agent_type", "通用智能体")
    
    # 构建基础指令
    instruction = f"""**多步骤工作流 - 第{step_number}步**

**原始用户请求**: {user_message}

**当前步骤任务**: {step_description}

**您的角色**: {agent_type}"""
    
    # 🔥 修复：显示前面所有已完成步骤的结果，而不是只看dependencies
    if execution_results:
        instruction += "\n\n**前置步骤结果**:"
        
        # 按步骤编号排序，确保顺序正确
        sorted_results = []
        for agent_id, result in execution_results.items():
            result_step_id = result.get("step_id", 0)
            # 只包含当前步骤之前的结果
            if result_step_id < step_number:
                sorted_results.append((result_step_id, result))
        
        # 按步骤编号排序
        sorted_results.sort(key=lambda x: x[0])
        
        # 添加所有前置步骤的结果
        for step_id, result in sorted_results:
            agent_name = result.get("agent_name", "前面的智能体")
            result_content = result.get("result", "")
            timestamp = result.get("timestamp", "")
            success = result.get("success", False)
            
            status_icon = "✅" if success else "❌"
            instruction += f"\n\n- {status_icon} **{agent_name}的执行结果** (步骤{step_id}):"
            
            # 🔥 确保结果内容完整，提高长度限制
            if len(result_content) > 2000:
                # 保留前1500字符和后300字符，确保关键信息不丢失
                result_content = result_content[:1500] + "\n...(中间部分省略)...\n" + result_content[-300:]
            
            instruction += f"\n  ```\n  {result_content}\n  ```"
            if timestamp:
                instruction += f"\n  时间: {timestamp[:19]}"  # 只显示到秒
        
        # 如果没有找到任何前置结果，提供说明
        if not sorted_results:
            instruction += "\n\n- ℹ️ **前置步骤**: 这是工作流的第一步，没有前置步骤结果。"
    
    # 添加步骤要求
    instruction += f"""

**执行要求**:
- 基于上述前置结果（如有）完成当前步骤
- 确保输出质量和专业性
- 为后续步骤提供清晰的结果数据

**期望输出**: {', '.join(step_info.get('outputs', ['专业的执行结果']))}
"""
    
    return instruction


def create_workflow_completion_message(execution_results: dict, workflow_plan: dict) -> str:
    """
    创建工作流完成的总结消息
    
    Args:
        execution_results: 所有步骤的执行结果
        workflow_plan: 工作流计划
        
    Returns:
        str: 完成消息
    """
    total_steps = workflow_plan.get("total_steps", 1)
    steps = workflow_plan.get("steps", [])
    
    message = f"""🎉 **多步骤工作流执行完成**

**总步数**: {total_steps}
**完成状态**: 所有步骤已成功执行

**执行历程**:"""
    
    for i, step in enumerate(steps, 1):
        step_desc = step.get("description", f"步骤{i}")
        agent_type = step.get("agent_type", "智能体")
        
        # 查找对应的执行结果
        step_result = None
        for agent_id, result in execution_results.items():
            result_step_id = result.get("step_id", 1)
            if result_step_id == i or (i == 1 and not result.get("step_id")):
                step_result = result
                break
        
        if step_result:
            success = step_result.get("success", False)
            status_icon = "✅" if success else "❌"
            agent_name = step_result.get("agent_name", agent_type)
        else:
            status_icon = "❓"
            agent_name = agent_type
        
        message += f"\n{i}. {status_icon} **{step_desc}** (执行者: {agent_name})"
    
    message += f"""

✨ **任务成功完成！** 所有{total_steps}个步骤均已按照工作流计划执行完毕。"""
    
    return message
    
'''