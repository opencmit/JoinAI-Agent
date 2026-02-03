
from langgraph_agent.graph.state import AgentState
from langgraph_agent.utils.tool_utils import has_attachment_tools

def should_process_attachments(state: AgentState) -> bool:
    """统一判断是否需要处理attachment工具"""
    # 检查是否有attachment工具
    if not has_attachment_tools(state):
        return False

    # 检查是否已处理
    if state.get("attachment_processed", False):
        return False

    # 检查是否是首次对话（第一轮）
    if state.get("conversation_round", 0) == 1:
        return True

    # 检查强制标志
    if state.get("force_attachment_call", False):
        return True

    # 其他情况不处理
    return False


def should_process_enhanced_markdown_request(state: AgentState) -> bool:
    """
    增强版：检测包含数据分析的markdown请求
    """
    # 获取最新的用户消息
    user_query = ""
    for message in reversed(state.get("messages", [])):
        if hasattr(message, 'type') and message.type == "human":
            user_query = message.content.lower()
            break

    # 检查是否已处理
    if state.get("markdown_processed", False):
        return False

    # 原有的markdown关键词
    markdown_keywords = [
        "生成.md", "生成markdown", "创建markdown",
        "创建.md", "写一个markdown", "帮我生成markdown",
        "markdown文件", ".md文件", "生成md文件"
    ]

    # 数据分析相关关键词
    data_keywords = [
        "分析数据", "生成报告", "统计图", "图表",
        "数据可视化", "分析上述数据", "生成图表"
    ]

    # 检查是否包含markdown关键词
    has_markdown = any(keyword in user_query for keyword in markdown_keywords)
    # 检查是否包含数据分析关键词
    has_data = any(keyword in user_query for keyword in data_keywords)

    # 如果包含数据表格（rpm, tpm等）也触发
    has_table_data = "rpm" in user_query and "tpm" in user_query

    if has_markdown or (has_data and has_table_data):
        print(f"[Markdown检测] 检测到{'数据分析' if has_data else '普通'}markdown生成请求")
        return True

    return False


def should_process_html_generation_request(state: AgentState) -> bool:
    """
    检测是否是HTML生成请求 - 修复版本
    """
    # 获取最新的用户消息
    user_query = ""
    for message in reversed(state.get("messages", [])):
        if hasattr(message, 'type') and message.type == "human":
            user_query = message.content.lower()
            break

    # 检查是否已处理
    if state.get("html_generation_processed", False):
        return False

    # HTML生成相关关键词
    html_keywords = [
        "生成html", "创建html", "生成一个html", "创建一个html",
        "写一个html", "帮我生成html", "html文件", "生成html文件",
        "创建html页面", "html页面", "web页面", "webpage", "生成html代码",
        "生成网页", "创建网页", "制作网页"
    ]

    # 排除markdown相关请求（避免冲突）
    markdown_keywords = ["markdown", ".md", "md文件"]
    has_markdown = any(keyword in user_query for keyword in markdown_keywords)

    # 排除数据分析报告请求（这些应该走enhanced_markdown路径）
    data_report_keywords = [
        "数据报告", "分析报告", "统计报告", "生成报告并", "报告和图表",
        "分析数据", "数据可视化", "生成图表", "统计图"
    ]
    has_data_report = any(keyword in user_query for keyword in data_report_keywords)

    # 检查是否包含HTML关键词
    has_html = any(keyword in user_query for keyword in html_keywords)

    # 只有纯HTML请求才走HTML生成器，排除markdown和数据报告
    if has_html and not has_markdown and not has_data_report:
        print(f"[HTML检测] 检测到纯HTML生成请求")
        return True

    return False


def _route_after_supervisor(self, state: AgentState) -> str:
    """
    Supervisor节点后的路由决策

    Args:
        state: 当前状态

    Returns:
        str: 下一个节点名称
    """
    route_decision = state.get("route_to_a2a")

    print(f"[Supervisor路由] 决策结果: {route_decision}")

    if route_decision and route_decision != "通用智能体":
        # 验证A2A智能体节点是否存在
        if route_decision in self.a2a_agent_nodes:
            print(f"[Supervisor路由] 路由到A2A智能体: {route_decision}")
            return route_decision
        else:
            print(f"[Supervisor路由] A2A智能体节点不存在: {route_decision}，回退到通用智能体")
            state["route_to_a2a"] = None
            return "general_agent"
    else:
        print(f"[Supervisor路由] 路由到通用智能体")
        return "general_agent"


def _route_after_prepare_temp_messages(self, state: AgentState) -> str:
    """
    准备临时消息节点后的路由决策 - 添加HTML生成检测
    """
    # 首先检查是否是HTML生成请求
    if should_process_html_generation_request(state):
        print("[路由决策] 检测到HTML生成请求，路由到HTML生成器")
        return "html_generator"

    # 然后检查是否是markdown生成请求
    if should_process_enhanced_markdown_request(state):
        print("[路由决策] 检测到markdown生成请求，路由到markdown处理器")
        return "markdown_processor"

    # 使用统一的attachment处理判断
    if should_process_attachments(state):
        print("[路由决策] 检测到需要处理的attachment工具，路由到attachment处理器")
        return "attachment_processor"

    # 如果启用了Supervisor模式
    if should_enable_supervisor_mode(state):
        print("[路由决策] 启用Supervisor模式")
        self.supervisor_mode = True
        self._preload_a2a_agents(state)
        return "supervisor_agent"
    else:
        print("[路由决策] 使用传统单智能体模式")
        self.supervisor_mode = False
        return "general_agent"


def _route_after_html_generator(self, state: AgentState) -> str:
    """
    HTML生成器节点后的路由决策 - 修复版本
    """
    # 🔥 优先检查是否已完成 - 这个检查应该最优先
    if state.get("completed", False):
        print("[HTML生成器路由] 任务已完成，直接结束")
        return END

    if state.get("html_generation_processed", False):
        print("[HTML生成器路由] HTML已处理完成，直接结束")
        state["completed"] = True  # 标记任务完成
        return END
    # HTML生成完成后，不再检查markdown（避免重复生成）
    print("[HTML生成器路由] HTML生成完成，跳过markdown检查")

    # 检查attachment
    if should_process_attachments(state):
        print("[HTML生成器路由] 继续到附件处理器")
        return "attachment_processor"

    # 检查Supervisor模式
    if should_enable_supervisor_mode(state):
        print("[HTML生成器路由] 继续到Supervisor模式")
        self.supervisor_mode = True
        self._preload_a2a_agents(state)
        return "supervisor_agent"
    else:
        print("[HTML生成器路由] 继续到通用智能体")
        self.supervisor_mode = False
        return "general_agent"


def _route_after_markdown_processor(self, state: AgentState) -> str:
    """
    Markdown处理器节点后的路由决策

    Args:
        state: 当前状态

    Returns:
        str: 下一个节点名称
    """
    # Markdown处理完成后，检查是否还需要处理其他内容

    # 检查attachment
    if should_process_attachments(state):
        print("[Markdown处理器路由] 继续到附件处理器")
        return "attachment_processor"

    # 检查Supervisor模式
    if should_enable_supervisor_mode(state):
        print("[Markdown处理器路由] 继续到Supervisor模式")
        self.supervisor_mode = True
        self._preload_a2a_agents(state)
        return "supervisor_agent"
    else:
        print("[Markdown处理器路由] 继续到通用智能体")
        self.supervisor_mode = False
        return "general_agent"


def _route_after_attachment_processor(self, state: AgentState) -> str:
    """
    附件处理器节点后的路由决策

    Args:
        state: 当前状态

    Returns:
        str: 下一个节点名称
    """
    # 附件处理完成后，继续正常流程
    if should_enable_supervisor_mode(state):
        print("[附件处理器路由] 继续到Supervisor模式")
        self.supervisor_mode = True
        self._preload_a2a_agents(state)
        return "supervisor_agent"
    else:
        print("[附件处理器路由] 继续到通用智能体")
        self.supervisor_mode = False
        return "general_agent"


def _route_after_general_agent(self, state: AgentState) -> str:
    """
    通用智能体节点后的路由决策 - 修复版本 (支持多步骤工作流)
    """
    # 检查是否已完成
    if state.get("completed", False):
        print("[通用智能体路由] 任务已完成，结束流程")
        return END

    # 检查最后一条消息是否有工具调用
    last_message = state["messages"][-1] if state["messages"] else None
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        print(f"[通用智能体路由] 检测到工具调用: {[tc['name'] for tc in last_message.tool_calls]}")
        return "tool_executor"

    # 🔥 关键修复：检查是否处于多步骤工作流中
    workflow_plan = state.get("workflow_plan") or {}
    workflow_type = workflow_plan.get("workflow_type", "single_step")
    current_step_index = state.get("current_step_index", 0)
    total_steps = workflow_plan.get("total_steps", 1)
    current_step_completed = state.get("current_step_completed", False)

    # 🔥 多步骤工作流：通用智能体完成后应该返回supervisor进行下一步规划
    if workflow_type == "multi_step":
        print(f"[通用智能体路由] 多步骤工作流中，当前步骤: {current_step_index + 1}/{total_steps}")

        # 检查是否完成了当前步骤
        if current_step_completed or (current_step_index < total_steps):
            print("[通用智能体路由] 多步骤工作流 - 返回supervisor进行下一步规划")
            return "supervisor_agent"
        elif current_step_index >= total_steps:
            print("[通用智能体路由] 多步骤工作流 - 所有步骤完成，返回supervisor进行最终确认")
            return "supervisor_agent"

    # 🔥 单步工作流：如果有工作流计划，也应该返回supervisor进行最终确认
    elif workflow_type == "single_step" and workflow_plan:
        # 检查是否有supervisor模式或A2A智能体配置
        has_supervisor_context = (
                self.supervisor_mode or
                state.get("a2a_agents") or
                state.get("supervisor_mode")
        )
        if has_supervisor_context:
            print("[通用智能体路由] 单步工作流 - 返回supervisor进行最终确认")
            return "supervisor_agent"

    # 增加迭代计数
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 50)

    if iteration_count >= max_iterations:
        print(f"[通用智能体路由] 达到最大迭代次数 {max_iterations}，结束流程")
        state["completed"] = True
        return END

    # 检查是否有明确的结束信号
    if last_message and hasattr(last_message, 'content'):
        content = last_message.content.lower()
        end_signals = ["谢谢", "再见", "结束对话", "goodbye", "bye", "thank you", "thanks"]
        if any(signal in content for signal in end_signals):
            print("[通用智能体路由] 检测到结束信号，结束对话")
            state["completed"] = True
            return END

    # 新增：检查 LLM 是否生成了描述但没有工具调用
    if last_message and hasattr(last_message, 'content'):
        content = last_message.content
        # 检查是否包含工具使用的意图词
        tool_intent_keywords = ["将使用", "我将", "首先", "接下来", "然后", "will use", "going to", "let me"]
        if any(keyword in content for keyword in tool_intent_keywords):
            print("[通用智能体路由] 检测到工具使用意图但没有工具调用，重新尝试")
            # 增加重试计数
            retry_count = state.get("tool_retry_count", 0)
            if retry_count < 3:  # 最多重试3次
                state["tool_retry_count"] = retry_count + 1
                state["iteration_count"] = iteration_count + 1
                # 添加提示消息
                from langchain_core.messages import SystemMessage
                retry_msg = SystemMessage(
                    content="请直接调用相应的工具来完成任务，不要只是描述。记住要生成实际的工具调用。")
                state["messages"].append(retry_msg)
                return "general_agent"  # 返回到 agent 重新生成
            else:
                print("[通用智能体路由] 多次重试后仍无工具调用，可能需要人工介入")

    # 默认等待用户输入（保持原有逻辑）
    print("[通用智能体路由] 等待用户输入...")
    state["waiting_for_user"] = True
    return END


def _route_after_tool_executor(self, state: AgentState) -> str:
    """
    工具执行节点后的路由决策 - 修复版本

    Args:
        state: 当前状态

    Returns:
        str: 下一个节点名称
    """
    # 🔥 关键修复：工具执行器不应该直接决定流程结束
    # 应该根据当前模式决定回到哪个节点进行最终判断

    # 检查是否已完成
    if state.get("completed", False):
        print("[工具执行器路由] 检测到任务完成标志")

        # 🔥 检查是否处于 A2A 模式
        if self.supervisor_mode or state.get("workflow_plan") or state.get("a2a_agents"):
            print("[工具执行器路由] 处于 A2A 模式，回到 Supervisor 进行最终确认")
            return "supervisor_agent"
        else:
            print("[工具执行器路由] 处于通用智能体模式，回到通用智能体进行最终处理")
            return "general_agent"

    # 检查迭代次数
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 50)

    if iteration_count >= max_iterations:
        print(f"[工具执行器路由] 达到最大迭代次数 {max_iterations}")
        state["completed"] = True

        # 🔥 同样根据模式决定回到哪里
        if self.supervisor_mode or state.get("workflow_plan") or state.get("a2a_agents"):
            print("[工具执行器路由] 达到最大迭代次数，回到 Supervisor 进行最终确认")
            return "supervisor_agent"
        else:
            print("[工具执行器路由] 达到最大迭代次数，回到通用智能体进行最终处理")
            return "general_agent"

    # 🔥 正常情况：根据模式决定下一步
    # 增加迭代计数并返回到相应的智能体进行下一轮处理
    state["iteration_count"] = iteration_count + 1

    if self.supervisor_mode or state.get("workflow_plan") or state.get("a2a_agents"):
        print(f"[工具执行器路由] 返回到 Supervisor，当前迭代: {state['iteration_count']}")
        return "supervisor_agent"
    else:
        print(f"[工具执行器路由] 返回到通用智能体，当前迭代: {state['iteration_count']}")
        return "general_agent"


def _route_after_a2a_execution(self, state: AgentState) -> str:
    """
    A2A智能体执行后的路由决策

    Args:
        state: 当前状态

    Returns:
        str: 下一个节点名称
    """
    # A2A智能体完成后的决策逻辑
    if state.get("completed", False):
        print("[A2A执行路由] 任务已完成，结束流程")
        return END

    # 检查迭代次数
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    if state["iteration_count"] >= state.get("max_iterations", 50):
        print("[A2A执行路由] 达到最大迭代次数，结束流程")
        return END

    # 可以选择返回Supervisor进行下一轮决策，或者继续其他流程
    print("[A2A执行路由] 继续准备下一轮消息")
    return "prepare_temp_messages"


def _route_after_supervisor_v2(self, state: AgentState) -> str:
    """
    Supervisor 节点后的改进版路由决策
    使用真正的 A2A 智能体执行器节点

    Args:
        state: 当前状态

    Returns:
        str: 下一个节点名称
    """
    # 🔥 关键修复：优先检查任务是否已完成
    if state.get("completed", False):
        print("[Supervisor路由V2] 任务已完成，结束流程")
        return END

    # 🚨 新增：递归检测和强制退出机制
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 50)
    supervisor_retry_count = state.get("supervisor_retry_count", 0)

    # 如果迭代次数或supervisor重试次数过多，强制使用通用智能体
    if iteration_count >= max_iterations:
        print(f"[Supervisor路由V2] 🚨 达到最大迭代次数 {iteration_count}，强制路由到通用智能体")
        emergency_message = AIMessage(content=f"⚠️ 检测到可能的路由循环，系统已切换到通用智能体确保任务顺利完成。")
        state["messages"].append(emergency_message)
        state["route_to_a2a"] = None
        return "general_agent"

    if supervisor_retry_count >= 30:  # 更严格的重试限制
        print(f"[Supervisor路由V2] 🚨 Supervisor重试次数过多 {supervisor_retry_count}，强制路由到通用智能体")
        emergency_message = AIMessage(content=f"⚠️ 智能体路由重试次数过多，系统已切换到通用智能体确保任务顺利完成。")
        state["messages"].append(emergency_message)
        state["route_to_a2a"] = None
        state["supervisor_retry_count"] = 0  # 重置重试计数
        return "general_agent"

    route_decision = state.get("route_to_a2a")

    print(f"[Supervisor路由V2] 决策结果: {route_decision}")

    if route_decision and route_decision != "通用智能体":
        # 检查是否有对应的 A2A 智能体
        if route_decision in self.a2a_agent_nodes:
            print(f"[Supervisor路由V2] 路由到 A2A 执行器: {route_decision}")
            return "a2a_agent_executor"
        else:
            print(f"[Supervisor路由V2] A2A 智能体不存在: {route_decision}")

            # 添加错误消息到前端
            available_agents = []
            for node_name, node_info in self.a2a_agent_nodes.items():
                agent_name = node_info["agent_info"].get("name", "Unknown")
                available_agents.append(f"{agent_name} ({node_name})")

            available_agents_str = "、".join(available_agents) if available_agents else "无"

            error_message = AIMessage(content=f"""❌ **A2A智能体路由失败**

**问题**: 推荐的智能体 `{route_decision}` 不存在或不可用。

**可用的A2A智能体**: {available_agents_str}

**原因**: 可能是智能体ID不匹配或服务不可用。

正在重新进行路由决策...""")

            state["messages"].append(error_message)

            # 记录失败的智能体信息，供supervisor重新决策
            failed_agents = state.get("failed_a2a_agents", [])
            if route_decision not in failed_agents:
                failed_agents.append(route_decision)
            state["failed_a2a_agents"] = failed_agents

            # 重新回到supervisor进行决策
            state["route_to_a2a"] = None
            state["supervisor_retry_count"] = state.get("supervisor_retry_count", 0) + 1

            # 检查重试次数，避免无限循环
            if state["supervisor_retry_count"] >= 3:
                print(f"[Supervisor路由V2] 达到最大重试次数 {state['supervisor_retry_count']}，回退到通用智能体")
                fallback_message = AIMessage(
                    content=f"⚠️ 经过多次尝试仍无法找到合适的A2A智能体，现在使用通用智能体为您服务。")
                state["messages"].append(fallback_message)
                return "general_agent"

            print(f"[Supervisor路由V2] 重新回到supervisor进行决策 (重试次数: {state['supervisor_retry_count']})")
            return "supervisor_agent"
    else:
        print("[Supervisor路由V2] 路由到通用智能体")
        return "general_agent"


def _route_after_a2a_executor(self, state: AgentState) -> str:
    """
    A2A 智能体执行器节点后的路由决策 - 支持多步骤工作流

    Args:
        state: 当前状态

    Returns:
        str: 下一个节点名称
    """
    print("[A2A执行器路由] 开始路由决策")

    # 🔥 检查整体工作流是否完成
    if state.get("completed", False):
        print("[A2A执行器路由] 整体工作流已完成，结束流程")
        return END

    # 🔥 优先检查工作流类型
    workflow_plan = state.get("workflow_plan") or {}
    workflow_type = workflow_plan.get("workflow_type", "single_step")
    total_steps = workflow_plan.get("total_steps", 1)
    current_step_index = state.get("current_step_index", 0)
    current_step_completed = state.get("current_step_completed", False)

    print(
        f"[A2A执行器路由] 工作流类型: {workflow_type}, 总步骤: {total_steps}, 当前步骤索引: {current_step_index}, 当前步骤完成: {current_step_completed}")

    # 🔥 多步骤任务：检查当前步骤是否完成，如果完成则返回Supervisor规划下一步
    if workflow_type == "multi_step":
        if current_step_completed:
            print("[A2A执行器路由] 多步骤任务 - 当前步骤完成，返回Supervisor进行下一步规划")
        return "supervisor_agent"

    # 🔥 多步骤任务：检查是否已完成所有步骤
    if current_step_index >= total_steps:
        print(f"[A2A执行器路由] 多步骤任务所有步骤已完成，回到Supervisor进行最终确认")
        return "supervisor_agent"

    # 🔥 单步任务：执行完成后也回到supervisor，让supervisor决定是否真正完成
    if workflow_type == "single_step":
        print(f"[A2A执行器路由] 单步任务执行完成，回到Supervisor进行最终确认和总结")
        return "supervisor_agent"

    # 检查迭代次数
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 50)

    if iteration_count >= max_iterations:
        print(f"[A2A执行器路由] 达到最大迭代次数 {max_iterations}，结束流程")
        state["completed"] = True
        return END

    # 🔄 检查是否有失败的A2A智能体需要重新决策
    failed_agents = state.get("failed_a2a_agents", [])
    retry_count = state.get("supervisor_retry_count", 0)

    if failed_agents and retry_count > 0 and retry_count < 3:
        print(f"[A2A执行器路由] 检测到智能体失败，重新回到supervisor决策 (重试: {retry_count})")
        return "supervisor_agent"

    # 检查是否刚执行过A2A且失败了
    last_a2a_result = state.get("last_a2a_result", "")
    if "执行失败" in str(last_a2a_result) or "执行异常" in str(last_a2a_result):
        print("[A2A执行器路由] 检测到A2A执行失败")

        # 🔄 如果重试次数不多，回到supervisor重新决策
        if retry_count < 3:
            print(f"[A2A执行器路由] 重新回到supervisor进行决策 (重试: {retry_count + 1})")
            state["supervisor_retry_count"] = retry_count + 1
            return "supervisor_agent"
        else:
            print("[A2A执行器路由] 重试次数过多，fallback到通用智能体")
            state["route_to_a2a"] = None  # 清除A2A路由
            return "general_agent"

    # 检查最近的消息是否包含错误信息
    if state.get("messages"):
        last_message = state["messages"][-1]
        if hasattr(last_message, 'content') and (
                "执行失败" in last_message.content or "执行异常" in last_message.content or "路由失败" in last_message.content):
            print("[A2A执行器路由] 检测到错误消息")

            # 🔄 如果重试次数不多，回到supervisor重新决策
            if retry_count < 3:
                print(f"[A2A执行器路由] 重新回到supervisor进行决策 (重试: {retry_count + 1})")
                state["supervisor_retry_count"] = retry_count + 1
                return "supervisor_agent"
            else:
                print("[A2A执行器路由] 重试次数过多，fallback到通用智能体")
                state["route_to_a2a"] = None  # 清除A2A路由
                return "general_agent"

    # 增加迭代计数
    state["iteration_count"] = iteration_count + 1

    # 检查A2A连续失败次数（防止反复尝试同一个失败的A2A智能体）
    a2a_failure_count = state.get("a2a_failure_count", 0)
    if a2a_failure_count >= 3:
        print(f"[A2A执行器路由] A2A连续失败{a2a_failure_count}次，强制使用通用智能体")
        state["route_to_a2a"] = None
        state["a2a_failure_count"] = 0  # 重置失败计数
        return "general_agent"

    # 🔥 关键修复：移除默认的END逻辑，改为回到Supervisor
    # 让Supervisor来决定工作流的真正完成状态
    print("[A2A执行器路由] A2A执行完成，回到Supervisor进行状态确认")
    return "supervisor_agent"