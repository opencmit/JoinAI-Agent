from langgraph.graph import add_messages
from typing import TypedDict, List, Optional, Annotated, Dict, Any, Union, Literal
from langchain_core.messages import BaseMessage, AnyMessage
from copilotkit import CopilotKitState
from langgraph_agent.constant import TEAM_MEMBERS

# Define routing options


#

class AgentState(CopilotKitState):

    # Messages 相关字段
    logs: List[dict]  # list of dicts logs to be sent to frontend with 'message', 'status'
    inner_messages: Annotated[list[AnyMessage], add_messages]   # 用于内部存储图运行的消息

    e2b_sandbox_id: str
    temporary_message_content_list: List[Dict[str, Any]] = []
    iteration_count: int = 0
    max_iterations: int = 150
    temporary_images: List[Dict] = []
    structure_tool_results: Dict[str, Any] = {}
    completed: bool = False
    # 新增字段用于存储 MCP 工具信息
    mcp_tools: List[Dict[str, Any]] = []
    input_data: Dict[str, Any] = {}  # 存储完整的输入数据
    model: Optional[str] = None # 模型名称，非必填,默认为None
    mcp_tool_executor_data: List[Dict[str, Any]] = [] # MCP工具执行数据
    mcp_tool_execution_results: List[Dict[str, Any]] = [] # MCP工具执行结果
    # A2A 智能体相关字段
    a2a_agents: List[Dict[str, Any]] = []  # 存储 A2A 智能体配置
    a2a_sessions: Dict[str, str] = {}  # 管理每个 A2A 智能体的 sessionId
    route_to_a2a: Optional[str] = None  # Supervisor 的路由决策
    last_a2a_result: Optional[str] = None  # 最后一次 A2A 执行结果
    a2a_failure_count: int = 0  # A2A 智能体连续失败次数
    a2a_fallback_to_general: bool = True  # A2A失败时是否fallback到通用智能体
    failed_a2a_agents: List[str] = []  # 记录失败的A2A智能体ID列表
    supervisor_retry_count: int = 0  # Supervisor重试决策的次数
    supervisor_decision: Dict[str, Any] = {}  # 存储supervisor的决策信息
    browser_use_steps: Optional[Dict[str, Any]] = None  # browser-use monitor_task 返回的步骤JSON

    # 🔥 新增：多步骤工作流控制字段
    current_step_completed: bool = False  # 当前步骤是否完成
    workflow_steps: List[Dict[str, Any]] = []  # 工作流步骤队列
    current_step_index: int = 0  # 当前执行步骤索引
    execution_results: Dict[str, Any] = {}  # 存储各步骤执行结果
    workflow_plan: Optional[Dict[str, Any]] = None  # 工作流整体规划
    
    # 补充字段
    session_id: str = ""    # 会话ID
    conversation_round: int = 0  # 对话轮数
    attachment_processed: bool = False  # 附件处理完成标志
    last_node: str = ""     # 在图运行过程中，记录上一个节点

    sub_task: str = ""  # 子任务

    # 附件
    files: List[Dict[str, Any]] = []

    # log
    log_index: int = -1  # 日志索引

def create_initial_state(state: AgentState):

    return AgentState(
        messages=state.get("messages", []),
        inner_messages=state.get("inner_messages", []),
        iteration_count=state.get("iteration_count", 0),
        max_iterations=state.get("max_iterations", 150),
        e2b_sandbox_id=state.get("e2b_sandbox_id", ""),
        copilotkit=state.get("copilotkit", {"actions": []}),
        logs=state.get("logs", []),
        temporary_message_content_list=state.get("temporary_message_content_list", []),
        temporary_images=state.get("temporary_images", []),
        structure_tool_results=state.get("structure_tool_results", {}),
        completed=False,
        model=state.get("model", None),
        mcp_tools=state.get("mcp_tools", []),
        mcp_tool_executor_data=state.get("mcp_tool_executor_data", []),
        input_data=state.get("input_data", {}),
        # 初始化 A2A 相关字段
        a2a_agents=state.get("a2a_agents", []),
        a2a_sessions=state.get("a2a_sessions", {}),
        route_to_a2a=None,
        last_a2a_result=None,
        a2a_failure_count=0,
        a2a_fallback_to_general=state.get("a2a_fallback_to_general", True),
        # 修复：添加缺失的字段
        failed_a2a_agents=state.get("failed_a2a_agents", []),
        supervisor_retry_count=state.get("supervisor_retry_count", 0),
        supervisor_decision=state.get("supervisor_decision", {}),
        # 🔥 初始化多步骤工作流字段
        current_step_completed=False,
        workflow_steps=state.get("workflow_steps", []),
        current_step_index=0,
        execution_results=state.get("execution_results", {}),
        workflow_plan=state.get("workflow_plan", None),
        # 添加其他可能缺失的字段
        session_id=state.get("session_id", "default_session"),
        conversation_round=state.get("conversation_round", 0),
        attachment_processed=state.get("attachment_processed", True),
        last_node=state.get("last_node", ""),
        files=state.get("files", []),
        log_index=state.get("log_index", -1),
        browser_use_steps=state.get("browser_use_steps", None)
    )
