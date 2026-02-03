import copy
import uuid
from typing import Tuple

from langchain_core.callbacks.manager import adispatch_custom_event
from langchain_core.messages import (
    ToolCall,
)
from langgraph.graph import StateGraph, START

from langgraph_agent.graph.a2a_agent import create_a2a_agent_info_from_config, a2a_agent_node, A2AHttpClient2
from langgraph_agent.graph.mcp_client import MCPConnectionManager
from langgraph_agent.graph.nodes import *
from langgraph_agent.graph.reporter_node import generate_reporter, generate_reporter_result
from langgraph_agent.graph.state import AgentState, create_initial_state
from langgraph_agent.prompts import *
from langgraph_agent.graph.utils import send_temp_tool_call_to_frontend, send_temp_message_to_frontend

# from langgraph_agent.sample_responses.formatter import format_sample
# 导入工具
from langgraph_agent.tools import (
    # 消息工具
    message_tool,
    # 网页搜索工具
    web_tool,
    # 沙箱工具 - Shell
    execute_command,
    # 沙箱工具 - 文件操作
    files_tool,
    # 沙箱工具 - 电脑操作
    computer_use_mouse_tool,
    computer_use_keyboard_tool,
    # 沙箱工具 - 端口暴露
    expose_port_tool
)
from langgraph_agent.tools.sandbox.manager import sbx_manager
from langgraph_agent.utils.json_utils import json_repair
from langgraph_agent.utils.message_utils import get_last_show_message_id

# Optional dependency for token counting
try:
    from litellm.utils import token_counter  # type: ignore
except Exception:  # pragma: no cover
    def token_counter(model: str, messages: Optional[List[Dict[str, Any]]] = None, text: Optional[str] = None) -> int:
        if text is not None:
            return len(str(text).split())
        messages = messages or []
        total = 0
        for msg in messages:
            total += len(str(msg.get("content", "")).split())
        return total

logger = logging.getLogger(__name__)


def create_ai_message(content: str, name: str = None) -> AIMessage:
    """创建带有唯一ID的AIMessage"""
    return AIMessage(content=content, name=name, id=str(uuid.uuid4()))


class ContextManager:
    """Lightweight inlined context manager with basic compression + token counting."""

    def __init__(self, token_threshold: int = 60000):
        self.token_threshold = token_threshold
        self.compression_target_ratio = 0.6
        self.min_keep_messages = 6

    async def count_tokens(
            self,
            model: str,
            messages: List[Dict[str, Any]],
            system_prompt: Optional[Dict[str, Any]] = None,
            apply_caching: bool = True,
    ) -> int:
        payload = []
        if system_prompt:
            payload.append(system_prompt)
        payload.extend(messages)
        try:
            return token_counter(model=model, messages=payload)
        except Exception:
            total = 0
            for msg in payload:
                total += len(str(msg.get("content", "")).split())
            return total

    def _flatten_content(self, msg: Dict[str, Any]) -> str:
        content = msg.get("content", "")
        if isinstance(content, str):
            return content
        return json.dumps(content, ensure_ascii=False)

    async def compress_messages(
            self,
            messages: List[Dict[str, Any]],
            llm_model: str,
            max_tokens: Optional[int] = 41000,
            token_threshold: int = 4096,
            max_iterations: int = 3,
            actual_total_tokens: Optional[int] = None,
            system_prompt: Optional[Dict[str, Any]] = None,
            thread_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not messages:
            return messages

        limit = max_tokens or self.token_threshold
        current_tokens = (
            actual_total_tokens
            if actual_total_tokens is not None
            else await self.count_tokens(llm_model, messages, system_prompt)
        )
        if current_tokens <= limit:
            return messages

        target_tokens = int(limit * self.compression_target_ratio)
        result = list(messages)

        for _ in range(max_iterations):
            if len(result) <= self.min_keep_messages:
                break

            drop_count = max(1, len(result) // 8)
            start = len(result) // 2 - drop_count // 2
            removed = result[start: start + drop_count]
            summary_text = f"[context compressed: removed {len(removed)} messages for token control]"
            summary_msg = {"role": "assistant", "content": summary_text, "name": "context_compression"}
            result = result[:start] + [summary_msg] + result[start + drop_count:]

            current_tokens = await self.count_tokens(llm_model, result, system_prompt)
            if current_tokens <= target_tokens:
                break

        return result


class A2AManager:
    def __init__(self):
        self.a2a_agent_nodes = {}  # 存储动态创建的A2A智能体节点

    async def create_a2a_executor_node(self, state: AgentState, config: RunnableConfig) -> AgentState:
        """
        创建通用的 A2A 智能体执行器节点
        该节点根据状态中的路由决策调用相应的 A2A 智能体

        Args:
            state: 智能体状态
            config: 运行配置

        Returns:
            AgentState: 更新后的状态
        """
        print("=== A2A 智能体执行器节点开始 ===")

        # 获取路由决策
        route_decision = state.get("route_to_a2a")
        if not route_decision or route_decision == "通用智能体":
            print("❌ A2A执行器收到无效的路由决策，直接返回")
            return state

        # 从已预加载的 A2A 智能体中找到对应的节点信息
        node_info = self.a2a_agent_nodes.get(route_decision)
        if not node_info:
            print(f"❌ 未找到 A2A 智能体: {route_decision}")

            # 添加详细的错误消息
            available_agents = []
            for node_name, info in self.a2a_agent_nodes.items():
                agent_name = info["agent_info"].get("name", "Unknown")
                available_agents.append(f"{agent_name} ({node_name})")

            available_str = "、".join(available_agents) if available_agents else "无"

            # 🔥 检查是否已经添加过相同的错误消息，避免重复
            error_content = f"""❌ **A2A智能体执行失败**

**问题**: 无法找到或连接到智能体 `{route_decision}`

**可用智能体**: {available_str}

**建议**: 请稍后重试或使用通用智能体服务。

正在重新进行智能体选择..."""

            # 检查是否已经存在相同的错误消息
            existing_error = False
            for msg in state.get("messages", []):
                if hasattr(msg, 'content') and error_content in msg.content:
                    existing_error = True
                    break

            if not existing_error:
                error_message = AIMessage(content=error_content)
                state["messages"].append(error_message)

            # 记录失败的智能体
            failed_agents = state.get("failed_a2a_agents", [])
            if route_decision not in failed_agents:
                failed_agents.append(route_decision)
            state["failed_a2a_agents"] = failed_agents

            # 重新回到supervisor
            state["route_to_a2a"] = None
            state["supervisor_retry_count"] = state.get("supervisor_retry_count", 0) + 1

            return state

        # 获取 A2A 智能体信息
        agent_info = create_a2a_agent_info_from_config(node_info["agent_info"])

        # # 创建并执行 A2A 智能体节点
        # a2a_node_func = create_a2a_agent_node(agent_info)

        print(f"🚀 执行 A2A 智能体: {agent_info.name}")

        # 调用真正的 A2A 智能体节点函数
        # 注意：这里需要使用 Command 的结果来更新状态
        try:
            command_result = await a2a_agent_node(state, config, agent_info)

            # 处理 Command 对象的结果
            if hasattr(command_result, 'update') and command_result.update:
                # 更新状态
                for key, value in command_result.update.items():
                    state[key] = value
                print(f"✅ A2A 智能体 {agent_info.name} 执行完成，状态已更新")
            else:
                print(f"⚠️ A2A 智能体 {agent_info.name} 返回的不是有效的 Command 对象")

        except Exception as e:
            print(f"❌ A2A 智能体 {agent_info.name} 执行异常: {str(e)}")
            import traceback
            traceback.print_exc()

            # 🔥 检查是否已经添加过相同的错误消息，避免重复
            error_content = f"A2A 智能体 {agent_info.name} 执行异常: {str(e)}"

            # 检查是否已经存在相同的错误消息
            existing_error = False
            for msg in state.get("messages", []):
                if hasattr(msg, 'content') and error_content in msg.content:
                    existing_error = True
                    break

            if not existing_error:
                error_message = AIMessage(content=error_content)
                state["messages"].append(error_message)

            state["completed"] = True

        print("=== A2A 智能体执行器节点完成 ===")
        return state

    def preload_a2a_agents_from_objects(self, a2a_agents_objects: List):
        """
        从A2AAgentInfo对象列表预加载A2A智能体信息

        Args:
            a2a_agents_objects: A2AAgentInfo对象列表
        """
        print("=== 预加载A2A智能体对象信息 ===")

        # 清理之前的A2A节点信息
        self.a2a_agent_nodes.clear()

        # 为每个A2A智能体准备节点信息
        for agent_obj in a2a_agents_objects:
            node_name = f"a2a_{agent_obj.agent_id}"

            # 转换为字典格式以便后续使用
            agent_dict = {
                "agent_id": agent_obj.agent_id,
                "name": agent_obj.name,
                "base_url": agent_obj.base_url,
                "desc": agent_obj.description,
                "user_id": agent_obj.user_id  # 🔥 修复：保留user_id字段
            }

            # 存储节点信息
            self.a2a_agent_nodes[node_name] = {
                "agent_id": agent_obj.agent_id,
                "agent_info": agent_dict
            }

            print(f"✅ 预加载A2A智能体: {node_name} ({agent_obj.name})")

        print(f"📋 总共预加载了 {len(self.a2a_agent_nodes)} 个A2A智能体")

    def preload_a2a_agents(self, state: AgentState):
        """
        预加载 A2A 智能体信息（不添加节点，只存储信息）

        Args:
            state: 当前状态
        """
        print("=== 预加载 A2A 智能体信息 ===")

        # 从状态中获取 A2A 智能体信息
        a2a_agents = get_a2a_agents_from_state(state)
        if not a2a_agents:
            print("没有发现 A2A 智能体，跳过预加载")
            return

        # 清理之前的 A2A 节点信息
        self.a2a_agent_nodes.clear()

        # 为每个 A2A 智能体准备节点信息
        for agent in a2a_agents:
            agent_id = agent.agent_id
            node_name = f"a2a_{agent.name}"

            # 存储智能体信息（转换为字典格式以便后续使用）
            agent_dict = {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "base_url": agent.base_url,
                "desc": agent.description,
                "user_id": agent.user_id  # 🔥 修复：保留user_id字段
            }

            # 存储节点信息
            self.a2a_agent_nodes[node_name] = {
                "agent_id": agent_id,
                "agent_info": agent_dict
            }

            print(f"✅ 预加载 A2A 智能体: {node_name} ({agent.name})")

        print(f"📋 总共预加载了 {len(self.a2a_agent_nodes)} 个 A2A 智能体")


class AgentGraph:
    """Agent 图构建类，负责创建和编译代理计算图 - 优化版本"""

    def __init__(self, llm: Optional[ChatOpenAI] = None):
        """
        Initialize the ResearchAgent.
        Args:
            llm: An optional pre-configured ChatOpenAI instance.
        """
        self.llm_instance = llm  # Store the provided LLM instance

        # Supervisor模式相关属性
        self.supervisor_mode = False
        """Initialize the available tools and create a name-to-tool mapping.
        """
        self.tools = [
            message_tool,  # 消息工具
            web_tool,  # 网页搜索工具
            execute_command,  # 沙箱工具 - Shell
            files_tool,  # 沙箱工具 - 文件操作
            computer_use_mouse_tool, computer_use_keyboard_tool,  # 沙箱工具 - 电脑操作
            expose_port_tool,  # 沙箱工具 - 端口暴露
        ]

        self.coder_tools = [execute_command, files_tool]

        self.researcher_tools = [web_tool]

        self.browser_tools = []

        self.reporter_tools = [files_tool]

        self.tools_by_name = {tool.name: tool for tool in self.tools}  # for easy lookup
        # LLM客户端缓存
        self._llm_clients_cache = {}
        # 上下文压缩管理器
        self.context_manager = ContextManager()
        self._build_workflow()

        # MCP相关
        self.mcp_client = MCPConnectionManager.get_instance()

        # A2A相关
        self.a2a_manager = A2AManager()
        self.a2a_config = global_config.load_a2a_config()

    def _message_to_context_dict(self, message: BaseMessage) -> Dict[str, Any]:
        role_map = {"ai": "assistant", "human": "user", "system": "system", "tool": "tool"}
        role = role_map.get(getattr(message, "type", ""), "user")

        msg_dict: Dict[str, Any] = {
            "role": role,
            "content": getattr(message, "content", "")
        }

        if getattr(message, "name", None):
            msg_dict["name"] = getattr(message, "name")
        if getattr(message, "id", None):
            msg_dict["message_id"] = getattr(message, "id")

        tool_calls = getattr(message, "tool_calls", None)
        if tool_calls:
            msg_dict["tool_calls"] = tool_calls

        tool_call_id = getattr(message, "tool_call_id", None)
        if tool_call_id:
            msg_dict["tool_call_id"] = tool_call_id

        additional_kwargs = getattr(message, "additional_kwargs", None)
        if additional_kwargs:
            msg_dict["additional_kwargs"] = additional_kwargs

        return msg_dict

    def _context_dict_to_message(self, payload: Dict[str, Any]) -> BaseMessage:
        role = payload.get("role")
        content = payload.get("content", "")

        common_kwargs: Dict[str, Any] = {}
        if payload.get("name") is not None:
            common_kwargs["name"] = payload.get("name")
        if payload.get("message_id") is not None:
            common_kwargs["id"] = payload.get("message_id")

        additional_kwargs = payload.get("additional_kwargs") or {}
        tool_calls_raw = payload.get("tool_calls")
        if tool_calls_raw is None and isinstance(additional_kwargs, dict):
            tool_calls_raw = additional_kwargs.get("tool_calls")
        tool_calls = tool_calls_raw if isinstance(tool_calls_raw, list) else []
        # 防止 None 混入 AIMessage 的 tool_calls
        additional_kwargs.pop("tool_calls", None)

        if role == "system":
            return SystemMessage(content=content, additional_kwargs=additional_kwargs, **common_kwargs)
        if role == "assistant":
            return AIMessage(
                content=content,
                tool_calls=tool_calls,
                additional_kwargs=additional_kwargs,
                **common_kwargs
            )
        if role == "tool":
            return ToolMessage(
                content=content,
                tool_call_id=payload.get("tool_call_id"),
                additional_kwargs=additional_kwargs,
                **common_kwargs
            )
        return HumanMessage(content=content, additional_kwargs=additional_kwargs, **common_kwargs)

    def _sanitize_messages(self, raw_messages: List[Any]) -> List[BaseMessage]:
        """Ensure messages are proper BaseMessage objects with role/content."""
        cleaned: List[BaseMessage] = []
        for msg in raw_messages or []:
            if isinstance(msg, BaseMessage):
                cleaned.append(msg)
                continue

            if isinstance(msg, dict):
                # Already in role/content dict form
                if msg.get("role") and "content" in msg:
                    try:
                        cleaned.append(self._context_dict_to_message(msg))
                        continue
                    except Exception:
                        pass

                # Handle LC serialized constructor dicts (missing role/content)
                kwargs = msg.get("kwargs", {})
                content = kwargs.get("content") or msg.get("content")
                if content is not None:
                    payload = {
                        "role": kwargs.get("role", "assistant"),
                        "content": content,
                        "name": kwargs.get("name") or msg.get("name"),
                        "message_id": kwargs.get("id") or msg.get("id"),
                        "tool_calls": kwargs.get("tool_calls"),
                        "tool_call_id": kwargs.get("tool_call_id"),
                        "additional_kwargs": kwargs.get("additional_kwargs", {}),
                    }
                    try:
                        cleaned.append(self._context_dict_to_message(payload))
                        continue
                    except Exception:
                        pass
            # Skip any malformed entry silently
        return cleaned

    async def _compress_conversation_for_llm(
            self,
            state: AgentState,
            model_name: str,
            system_message: Optional[BaseMessage] = None,
    ) -> Tuple[List[BaseMessage], Optional[Dict[str, Any]]]:
        """Apply context compression before invoking the LLM."""
        base_messages = self._sanitize_messages(copy.deepcopy(state.get("inner_messages", [])))
        if not base_messages:
            return base_messages, None

        system_prompt = self._message_to_context_dict(system_message) if system_message else None
        conversation_dicts = [self._message_to_context_dict(msg) for msg in base_messages]

        try:
            original_tokens = await self.context_manager.count_tokens(
                model_name, conversation_dicts, system_prompt, apply_caching=True
            )
        except Exception as err:
            logger.warning(f"Context token count failed: {err}")
            return base_messages, None

        try:
            compressed_conversation = await self.context_manager.compress_messages(
                conversation_dicts,
                model_name,
                system_prompt=system_prompt,
                thread_id=state.get("session_id"),
            )
        except Exception as err:
            logger.warning(f"Context compression failed: {err}")
            return base_messages, None

        try:
            compressed_tokens = await self.context_manager.count_tokens(
                model_name, compressed_conversation, system_prompt, apply_caching=True
            )
        except Exception as err:
            logger.warning(f"Compressed token count failed: {err}")
            compressed_tokens = original_tokens

        ratio = round(compressed_tokens / original_tokens, 4) if original_tokens else 1.0
        stats = {
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "compression_ratio": ratio,
        }

        compressed_messages = [self._context_dict_to_message(msg) for msg in compressed_conversation]
        state["context_compression"] = stats
        state["inner_messages"] = copy.deepcopy(compressed_messages)
        state["messages"] = copy.deepcopy(compressed_messages)

        logger.info(f"Context compression applied: {original_tokens} -> {compressed_tokens} tokens (ratio {ratio})")
        return compressed_messages, stats

    async def initial_setup_node(self, state: AgentState, config: Dict[str, Any]) -> Command[Literal["coordinator"]]:
        """初始化设置节点 - 优化版本"""
        state = create_initial_state(state)
        input_data = state.get("input", {})

        # 初始化A2A的配置
        state["a2a_agents"] = []
        for key, value in self.a2a_config.items():
            if not value.get("enabled", False):
                continue

            if any(agent["agent_id"] == key for agent in state["a2a_agents"]):
                continue

            client = A2AHttpClient2(value["base_url"])
            name = await client.get_a2a_name()
            desc = await client.get_a2a_desc()
            state["a2a_agents"].append(
                {
                    "name": name,
                    "agent_id": key,
                    "desc": desc,
                    "base_url": value["base_url"]
                }
            )

        # # 新增：初始化 e2b 沙箱
        # try:
        #     timeout_str = os.getenv("E2B_SANDBOX_TIMEOUT", "3600")
        #     try:
        #         sandbox_timeout = int(timeout_str)
        #     except Exception:
        #         sandbox_timeout = 3600

        #     current_sandbox_id = state.get("e2b_sandbox_id")
        #     if not current_sandbox_id:
        #         logger.info(f"初始化 e2b 沙箱，timeout={sandbox_timeout}s")
        #         sandbox = Sandbox.create(timeout=sandbox_timeout)
        #         state["e2b_sandbox_id"] = getattr(sandbox, "sandbox_id", "")
        #         logger.info(f"e2b 沙箱初始化完成: {state['e2b_sandbox_id']}")
        #     else:
        #         logger.info(f"检测到已有 e2b 沙箱，跳过初始化: {current_sandbox_id}")
        # except ImportError as e:
        #     logger.warning(f"未找到 e2b SDK 或配置，跳过沙箱初始化: {str(e)}")
        # except Exception as e:
        #     logger.warning(f"e2b 沙箱初始化失败: {str(e)}")

        # 使用 SandboxManager 初始化 e2b 沙箱
        try:
            current_sandbox_id = state.get("e2b_sandbox_id")

            if not current_sandbox_id or current_sandbox_id == "your_sandbox_id_here":
                try:
                    state, async_sbx = await sbx_manager.get_sandbox_async(state)
                    sandbox_id = getattr(async_sbx, "sandbox_id", state.get("e2b_sandbox_id", ""))
                except Exception as e_async:
                    logger.warning(f"异步沙箱创建失败，尝试同步方式: {str(e_async)}")
                    state, desktop_sbx = sbx_manager.get_sandbox(state)
                    sandbox_id = getattr(desktop_sbx, "sandbox_id", state.get("e2b_sandbox_id", ""))
                state["e2b_sandbox_id"] = sandbox_id
                logger.info(f"e2b 沙箱初始化完成（manager）: {state['e2b_sandbox_id']}")
            else:
                logger.info(f"检测到已有 e2b 沙箱（manager 跳过）: {current_sandbox_id}")
        except Exception as e:
            logger.warning(f"e2b 沙箱通过 manager 初始化失败: {str(e)}")

        # 处理消息
        import uuid
        message_id = str(uuid.uuid4())
        messages = state.get("messages", [])
        if input_data and "message" in input_data:
            # 如果 input_data 中有 message，将其添加到 messages 中
            for msg in input_data["message"]:
                if msg.get("type") == "human":
                    messages.append(HumanMessage(id=message_id, content=msg.get("content", ""), name="user"))
                elif msg.get("type") == "ai":
                    messages.append(AIMessage(id=message_id, content=msg.get("content", ""), name="user"))

        messages = self._sanitize_messages(messages)
        state["messages"] = copy.deepcopy(messages)
        state["inner_messages"] = copy.deepcopy(messages)

        logger.info(f"初始Messages：{state['inner_messages']}")

        # 处理A2A智能体信息
        state = await process_a2a_agents(state)
        await self.add_dynamic_a2a_nodes(state, config)
        # 预加载A2A智能体到管理器，确保后续a2a节点可用
        try:
            self.a2a_manager.preload_a2a_agents(state)
        except Exception as e:
            print(f"预加载A2A智能体失败: {str(e)}")

        # 处理MCP工具信息
        # ✅ 修复 BlockingError：load_mcp_config 现在是异步方法，需要 await
        mcp_config = await global_config.load_mcp_config()
        await self.mcp_client.start(mcp_config)

        # 处理附件信息
        state = await process_attachment(state, config)

        logger.info(f"附件处理后的Messages：{state['inner_messages']}")

        # # 处理知识库信息
        # state = await process_knowledge(state, config)

        # 确保必需的字段存在且正确设置
        if "conversation_round" not in state:
            state["conversation_round"] = 0
        if "session_id" not in state:
            # 从config中获取session_id，如果没有则生成一个
            session_id = config.get("configurable", {}).get("session_id")
            if not session_id:
                import uuid
                session_id = f"session_{uuid.uuid4().hex[:8]}"
            state["session_id"] = session_id
            print(f"[initial_setup_node] 设置会话ID: {session_id}")

        state_update = dict(state)

        logger.info(f"After Attchment Messages:\n{state['messages']}")
        logger.info(f"After Attchment Inner Messages:\n{state['inner_messages']}")

        return Command(update=state_update, goto="coordinator")

    async def coordinator_node(self, state: AgentState, config: RunnableConfig) -> Command[
        Literal["supervisor", "__end__"]]:
        """Coordinator node that communicate with customers."""
        print("Coordinator talking.")
        node_name = "coordinator"

        logger.info(f"🔄 执行标准协调流程，agent_type: {state.get('agent_type', 'None')}")

        llm, model_name = get_llm_client(state, config)
        prompt = COORDINATOR_PROMPT

        # 创建系统消息 - 清理系统prompt
        try:
            system_prompt = sanitize_string_for_json(prompt, context="api")
            system_message = SystemMessage(content=system_prompt)
        except Exception as e:
            print(f"⚠️ 系统prompt创建失败: {str(e)}")
            # 使用简化的系统消息
            simple_system_prompt = "你是一个有用的AI助手。"
            system_message = SystemMessage(content=simple_system_prompt)

        state_update: Dict[str, Any] = {}
        compressed_messages, compression_stats = await self._compress_conversation_for_llm(
            state, model_name, system_message
        )
        messages = [system_message] + copy.deepcopy(compressed_messages)
        if compression_stats:
            state_update["context_compression"] = compression_stats
        try:
            # 在调用LLM之前，验证和清理所有消息
            # cleaned_messages = clean_messages(messages)
            cleaned_messages = messages
            # 调用 LLM (使用安全调用函数)
            response = await safe_llm_invoke(llm, config, model_name, cleaned_messages, hidden=True)
            response_content = response.content

            # 尝试修复可能的JSON输出
            response_content = repair_json_output(response_content)

            logger.debug(f"Coordinator response: {response_content}")
            new_message = create_ai_message(response_content, node_name)

            if "handoff_to_planner" in response_content:
                goto = "supervisor"
            else:
                state_update.update({
                    "messages": new_message,
                    "inner_messages": new_message
                })
                goto = "__end__"
            if state.get("context_compression"):
                state_update["context_compression"] = state["context_compression"]
            logger.info(f"coordinator_node goto{goto}")


        except Exception as e:
            logger.error(str(e))
            new_message = create_ai_message(str(e), node_name)
            state_update.update({
                "messages": new_message,
                "inner_messages": new_message
            })
            if state.get("context_compression"):
                state_update["context_compression"] = state["context_compression"]
            goto = "__end__"

        logger.info(f"state_update in coord: {state_update}")
        return Command(update=state_update, goto=goto)

    async def supervisor_node(self, state: AgentState, config: RunnableConfig) \
            -> Command[Literal["coder", "researcher", "reporter", "mcp_tool", "a2a_agent", "__end__"]]:
        """Supervisor node that decides which agent should act next."""
        node_name = "supervisor"
        print("------------------supervisor_node---------------------")

        # logger.info(f"Supervisor start")
        # logger.info(f"Supervisor Messages:\n{state['messages']}")
        # logger.info(f"Supervisor Inner Messages:\n{state['inner_messages']}")

        state["logs"].append({
            "message": "思考中",
            "done": False,
            "messageId": get_last_show_message_id(state["messages"])
        })
        await copilotkit_emit_state(config, state)

        # 🔥 增强日志记录：详细记录supervisor的路由决策过程
        agent_type = state.get("agent_type")
        logger.info("=" * 50)
        logger.info("Supervisor节点开始执行")
        logger.info(f"当前agent_type: {agent_type}")

        # 🔥 初始化 state_update 变量，避免 UnboundLocalError
        state_update = {}
        goto = "__end__"  # 默认值

        # 🔥 新增：检查是否已完成
        if state.get("completed", False):
            logger.info("✅ 检测到completed标志，工作流已完成")
            logger.info("Supervisor节点结束 - 工作流完成")
            logger.info("=" * 50)

            state["logs"][-1]["done"] = True
            state["logs"][-1]["message"] = "思考完成"
            # state_update["logs"] = state["logs"]
            return Command(update=state, goto="__end__")

        # 获取A2A智能体列表
        a2a_agents = state.get("a2a_agents", [])

        # 获取MCP工具列表 - 简化处理
        mcp_tools = await self.mcp_client.get_tools()
        # print(mcp_tools)

        mcp_tools_info = [{"name": tool.name, "description": tool.description} for tool in mcp_tools]
        # print(mcp_tools_info)

        for item in mcp_tools_info:
            if item['name'] == "jina_reader":
                item[
                    'description'] = "Extract and process content from a specific web page. Requires a complete URL as input (e.g., https://example.com/page), not a search query or keywords."

        # 动态生成supervisor prompt和解析器
        # generate_supervisor_prompt 等已通过顶部 from langgraph_agent.prompts import * 导入

        prompt = await generate_supervisor_prompt(a2a_agents, mcp_tools_info)

        # logger.info(f"Supervisor Prompt:\n{prompt}")

        llm, model_name = get_llm_client(state, config)

        messages = copy.deepcopy(state["inner_messages"])

        # logger.info(f"supervisor_node messages:{messages}")
        # 去除中间过程无效的ai消息，避免干扰
        if isinstance(messages, list):
            messages = [msg for msg in messages
                        if not (hasattr(msg, 'content') and
                                (msg.content == 'handoff_to_planner()' or
                                 msg.content == '""') or
                                (hasattr(msg, 'name') and msg.name == 'supervisor'))]

        # 获取所有可能的团队成员（包括动态A2A智能体）
        all_team_members = list(TEAM_MEMBERS)
        if a2a_agents:
            a2a_names = [f"a2a_{agent.get('name', '')}" for agent in a2a_agents if agent.get('name')]
            all_team_members.extend(a2a_names)
        if mcp_tools_info:
            mcp_names = [f"mcp_{tool.get('name', '')}" for tool in mcp_tools_info if tool.get('name')]
            all_team_members.extend(mcp_names)

        # for message in messages:
        #     if isinstance(message, BaseMessage) and message.name in all_team_members:
        #         message.content = RESPONSE_FORMAT.format(message.name, message.content)

        # 创建系统消息（不进行JSON转义，避免影响模型对格式要求的理解）
        try:
            system_message = SystemMessage(content=prompt)
        except Exception as e:
            print(f"⚠️ 系统prompt创建失败: {str(e)}")
            # 使用简化的系统消息
            simple_system_prompt = "你是一个有用的AI助手。"
            system_message = SystemMessage(content=simple_system_prompt)

        compressed_messages, compression_stats = await self._compress_conversation_for_llm(
            state, model_name, system_message
        )
        messages = [system_message] + copy.deepcopy(compressed_messages)
        if compression_stats:
            state["context_compression"] = compression_stats

        try:
            # 在调用LLM之前，验证和清理所有消息
            # cleaned_messages = clean_messages(messages)
            cleaned_messages = messages
            # 使用结构化输出强制返回JSON，避免非JSON内容
            dynamic_router = create_dynamic_router(a2a_agents, mcp_tools_info)
            structured_llm = llm.with_structured_output(dynamic_router)

            # structured_llm = llm
            response = await safe_llm_invoke(structured_llm, config, model_name, cleaned_messages, hidden=True)
            # print("supervisor:{}".format(response))

            # tought_message = [AIMessage(content=f"正在思考中...")]

            logger.info(f"Supervisor response: {response}")

            goto = response.next
            # print("----------------------------------------------")
            # print("goto:{}".format(goto))

            if response.sub_task:
                state["sub_task"] = response.sub_task

            # if response.sub_task:
            #     state_update.update({
            #         "sub_task": response.sub_task
            #     })
            #     new_message = create_ai_message(f"next:{goto}  sub_task:{response.sub_task}", node_name)
            # else:
            #     new_message = create_ai_message(f"next:{goto}", node_name)

            # state_update.update({
            #     "messages": new_message,
            #     "inner_messages": new_message
            # })

            if goto == "FINISH":
                goto = "__end__"

                # avoid duplicate reporter message
                if state["messages"][-1].name != "reporter":
                    # 先临时提交消息，用于向用户快速展示结果
                    temp_message_id = str(uuid.uuid4())
                    await send_temp_message_to_frontend(response.final_answer, temp_message_id, "assistant", config)
                    aimessage = AIMessage(content=response.final_answer, name=node_name, id=temp_message_id)

                    state["messages"].append(aimessage)
                    state["inner_messages"].append(aimessage)
                
                temp_message_id = str(uuid.uuid4())
                await send_temp_message_to_frontend("任务已完成", temp_message_id, "assistant", config)
                aimessage = AIMessage(content="任务已完成", name=node_name, id=temp_message_id)
                
                state["messages"].append(aimessage)
                state["inner_messages"].append(aimessage)

                logger.info("Workflow completed")

            # MCP工具节点路由
            elif goto.startswith("mcp_"):
                goto = "mcp_tool"

            # 🔧 当选择的是具体的 A2A 智能体（例如: a2a_dialog@123）时，
            # 实际应路由到通用的 `a2a_agent` 节点，并通过 state.route_to_a2a 传递具体路由ID。
            elif goto.startswith("a2a_"):
                state["route_to_a2a"] = goto
                goto = "a2a_agent"

        except Exception as e:
            logger.error(f"❌ Supervisor执行异常: {str(e.with_traceback)}")

            aimessage = AIMessage(content=str(e), name=node_name, id=str(uuid.uuid4()))
            state["messages"].append(aimessage)
            state["inner_messages"].append(aimessage)

            goto = "__end__"
            logger.info("Supervisor节点结束 - 执行异常")

        # state_update = {"messages": [AIMessage(content=f"正在思考中...")]}
        logger.info(f"✅ Supervisor决策完成，goto: {goto}")
        logger.info("Supervisor节点结束 - 成功")
        logger.info("=" * 50)

        state["logs"][-1]["done"] = True
        state["logs"][-1]["message"] = "思考完成"
        await copilotkit_emit_state(config, state)

        if state.get("context_compression"):
            state["context_compression"] = state["context_compression"]

        # logger.info(f"Supervisor Messages:\n{state['messages']}")
        # logger.info(f"Supervisor Inner Messages:\n{state['inner_messages']}")

        logger.info(f"state messages: {state["messages"]}")
        logger.info(f"state logs: {state["logs"]}")

        return Command(update=state, goto=goto)

    async def code_node(self, state: AgentState, config: RunnableConfig) -> Command[
        Literal["supervisor", "tool_executor"]]:
        """Node for the coder agent that executes Python code."""
        node_name = "coder"
        logger.info("Code agent starting task")
        state["logs"].append({
            "message": "代码智能体执行中",
            "done": False,
            "messageId": get_last_show_message_id(state["messages"])
        })
        await copilotkit_emit_state(config, state)
        # 使用统一的LLM客户端获取方法
        llm, model_name = get_llm_client(state, config)
        prompt = CODER_PROMPT
        # 绑定所有工具到LLM实例
        try:
            llm = llm.bind_tools(self.coder_tools)
            print(f"成功绑定 {len(self.coder_tools)} 个工具到LLM")
        except Exception as e:
            print(f"绑定工具失败: {str(e)}")

        await self._compress_conversation_for_llm(state, model_name)

        state_update = await agent_node(state, config, llm, prompt, node_name)
        if state.get("context_compression"):
            state_update["context_compression"] = state["context_compression"]

        logger.info("Code agent completed task")

        # 确保last_node字段被正确设置
        state_update["last_node"] = node_name
        state["logs"][-1]["done"] = True
        state["logs"][-1]["message"] = "代码智能体执行完成"
        state_update["logs"] = state["logs"]  # 用于整体对话结束后的logs状态保存 # 用于整体对话结束后的logs状态保存

        return Command(
            update=state_update,
            goto=route_after_agent_node(last_message=state_update["inner_messages"][-1]),
        )

    async def research_node(self, state: AgentState, config: RunnableConfig) -> Command[
        Literal["supervisor", "tool_executor"]]:
        """Node for the researcher agent that performs research tasks."""

        logger.info(f"Researcher Messages:\n{state['messages']}")
        logger.info(f"Researcher Inner Messages:\n{state['inner_messages']}")

        node_name = "researcher"
        logger.info("Research agent starting task")
        print("-----------------------researcher-------------------------")

        state["logs"].append({
            "message": "研究智能体执行中",
            "done": False,
            "messageId": get_last_show_message_id(state["messages"])
        })
        # await copilotkit_emit_state(config, state)
        # 使用统一的LLM客户端获取方法
        llm, model_name = get_llm_client(state, config)
        prompt = RESEARCHER_PROMPT

        # 绑定所有工具到LLM实例
        try:
            llm = llm.bind_tools(self.researcher_tools)
            print(f"成功绑定 {len(self.researcher_tools)} 个工具到LLM")
        except Exception as e:
            print(f"绑定工具失败: {str(e)}")

        await self._compress_conversation_for_llm(state, model_name)

        state_update = await agent_node(state, config, llm, prompt, node_name)
        if state.get("context_compression"):
            state_update["context_compression"] = state["context_compression"]

        logger.info("Research agent completed task")

        # 确保last_node字段被正确设置
        state_update["last_node"] = node_name
        state["logs"][-1]["done"] = True
        state["logs"][-1]["message"] = "研究智能体执行完成"
        state_update["logs"] = state["logs"]  # 用于整体对话结束后的logs状态保存

        logger.info(f"Researcher last message: {state_update['inner_messages'][-1]}")
        return Command(
            update=state_update,
            goto=route_after_agent_node(last_message=state_update["inner_messages"][-1])
        )

    async def browser_node(self, state: AgentState, config: RunnableConfig) -> Command[
        Literal["supervisor", "tool_executor"]]:
        """Node for the browser agent that performs web browsing tasks."""
        node_name = "browser"
        logger.info("Browser agent starting task")
        state["logs"].append({
            "message": "浏览器智能体执行中",
            "done": False,
            "messageId": get_last_show_message_id(state["messages"])
        })
        await copilotkit_emit_state(config, state)
        # 使用统一的LLM客户端获取方法
        llm, model_name = get_llm_client(state, config)
        prompt = BROWSER_PROMPT
        # 绑定所有工具到LLM实例
        try:
            llm = llm.bind_tools(self.browser_tools)
            print(f"成功绑定 {len(self.browser_tools)} 个工具到LLM")
        except Exception as e:
            print(f"绑定工具失败: {str(e)}")

        await self._compress_conversation_for_llm(state, model_name)

        state_update = await agent_node(state, config, llm, prompt, node_name)
        if state.get("context_compression"):
            state_update["context_compression"] = state["context_compression"]

        logger.info("Browser agent completed task")

        # 确保last_node字段被正确设置
        if "last_node" not in state_update:
            state_update["last_node"] = "browser"

        state["logs"][-1]["done"] = True
        state["logs"][-1]["message"] = "浏览器智能体执行完成"
        state_update["logs"] = state["logs"]  # 用于整体对话结束后的logs状态保存

        return Command(
            update=state_update,
            goto=route_after_agent_node(last_message=state_update["inner_messages"][-1]),
        )

    async def reporter_node(self, state: AgentState, config: RunnableConfig) -> Command[Literal["supervisor"]]:
        """Reporter node that write a final report."""
        node_name = "reporter"
        logger.info("Reporter write final report")
        log_index = len(state["logs"])
        state["logs"].append({
            "message": "报告智能体执行中",
            "done": False,
            "messageId": get_last_show_message_id(state["messages"]),
            "sub_logs": [{
                "message": "✍️ 生成报告中",
                "done": False,
            }]
        })
        await copilotkit_emit_state(config, state)

        # 第一步：生成报告
        try:
            reporter_reponse = await generate_reporter(state, config)
            # state["messages"].append(reporter_reponse)
            state["logs"][log_index]["sub_logs"][0]["message"] = "✍️ 生成完成"
            state["logs"][log_index]["sub_logs"][0]["done"] = True
            state["log_index"] = log_index
            await copilotkit_emit_state(config, state)
        except Exception as e:
            print(f"reporter智能体生成报告失败: {str(e)}")
            traceback.print_exc()

            message_id = str(uuid.uuid4())
            message_content = "reporter智能体生成报告失败，reporter智能体不可用"
            # 运行时消息临时提交
            await send_temp_message_to_frontend(message_content, message_id, "assistant", config)

            new_message = AIMessage(id=message_id, content=message_content, name="reporter")
            state["messages"].append(new_message)
            state["inner_messages"].append(new_message)

            state["logs"][log_index]["sub_logs"][0]["message"] = "✍️ 生成失败"
            state["logs"][log_index]["sub_logs"][0]["done"] = True
            state["logs"][log_index]["done"] = True
            state["logs"][log_index]["message"] = "报告智能体执行异常"
            state["log_index"] = -1  # 重置log_index
            await copilotkit_emit_state(config, state)
            return Command(update=state, goto="supervisor")

        # 第二步，使用files工具写入
        final_path = None
        final_content = None
        if isinstance(state.get("report_meta"), dict):
            final_path = state["report_meta"].get("path")
            final_content = state["report_meta"].get("content")
        try:
            raw = reporter_reponse.content if hasattr(reporter_reponse, "content") else ""
            data = None
            try:
                data = json.loads(raw)
            except Exception:
                blocks = re.findall(r"\{[\s\S]*?\}", raw)
                parsed = None
                for blk in blocks:
                    try:
                        obj = json_repair.loads(blk)
                        if isinstance(obj, dict) and ("path" in obj or "content" in obj):
                            parsed = obj
                            break
                    except Exception:
                        continue
                if parsed is not None:
                    data = parsed
            if isinstance(data, dict):
                final_path = data.get("path")
                final_content = data.get("content")
        except Exception:
            pass

        if not final_content:
            final_content = reporter_reponse.content

        if not final_path:
            final_path = os.path.join(global_config.SANDBOX_WORKING_DIR, "报告-" + str(uuid.uuid4()) + ".md")
        else:
            if not final_path.startswith("/"):
                final_path = os.path.join(global_config.SANDBOX_WORKING_DIR, final_path)

        arguments = {
            "operation": "create",
            "path": final_path,
            "content": final_content
        }
        tool_name = "files"
        tool_call_id = f"tool-{uuid.uuid4()}"
        await send_temp_tool_call_to_frontend(tool_name, arguments, tool_call_id, config)   

        tool_call = ToolCall(name=tool_name, args=arguments, id=tool_call_id)
        state["messages"].append(AIMessage(name=tool_name, content="", tool_calls=[tool_call]))
        state["inner_messages"].append(AIMessage(name=tool_name, content="", tool_calls=[tool_call]))

        try:
            arguments["state"] = state
            arguments["special_config_param"] = {}
            state, tool_msg = await files_tool.ainvoke(arguments, config=config)

            tool_message = ToolMessage(
                content=tool_msg,
                name=tool_name,
                tool_call_id=tool_call_id
            )
            state["messages"].append(tool_message)
            state["inner_messages"].append(tool_message)
        except Exception as e:
            print(f"files工具执行失败: {str(e)}")
            traceback.print_exc()

            message_id = str(uuid.uuid4())
            message_content = "files工具执行失败，reporter智能体不可用"
            tool_message = ToolMessage(
                content=message_content,
                name=tool_name,
                tool_call_id=tool_call_id
            )
            state["messages"].append(tool_message)
            state["inner_messages"].append(tool_message)

            state["logs"][log_index]["done"] = True
            state["logs"][log_index]["message"] = "报告智能体执行异常"
            state["log_index"] = -1  # 重置log_index
            await copilotkit_emit_state(config, state)
            return Command(update=state, goto="supervisor")

        # 此处需100%保证不会重复执行，鉴于大模型不确定性，故不再由大模型自行进行总结，而是直接生成完成相应子任务的语句，供supervisor判断。
        # 第三步，生成任务完成的表述
        sub_logs_index = len(state["logs"][log_index]["sub_logs"])
        state["logs"][log_index]["sub_logs"].append({
            "message": "📋 总结执行过程中",
            "done": False,
        })
        await copilotkit_emit_state(config, state)
        try:
            result_response = await generate_reporter_result(state, config)
            result_response.name = "reporter"  # 此处一定要设置为reporter，让supervisor知道reporter已执行完成
            state["messages"].append(result_response)
            state["inner_messages"].append(result_response)
        except Exception as e:
            # 此处虽然报出异常，但reporter已执行完成，故改为用简单回复代替
            print(f"reporter智能体总结失败: {str(e)}")
            traceback.print_exc()

            message_id = str(uuid.uuid4())
            message_content = "已完成任务需求，达到预期目标"
            # 运行时消息临时提交
            await send_temp_message_to_frontend(message_content, message_id, "assistant", config)

            new_message = AIMessage(id=message_id, content=message_content, name="reporter")
            state["messages"].append(new_message)
            state["inner_messages"].append(new_message)

        state["logs"][log_index]["sub_logs"][sub_logs_index]["message"] = "📋 总结完成"
        state["logs"][log_index]["sub_logs"][sub_logs_index]["done"] = True
        await copilotkit_emit_state(config, state)
        # 设置执行过程完成
        state["logs"][log_index]["done"] = True
        state["logs"][log_index]["message"] = "报告智能体执行完成"
        state["log_index"] = -1  # 重置log_index
        await copilotkit_emit_state(config, state)

        return Command(
            update=state,
            goto="supervisor",
        )

    async def tool_executor_node(self, state: AgentState, config: RunnableConfig) -> Command[
        Literal["coder", "researcher", "reporter"]]:
        """工具执行节点 - 优化版本"""

        logger.info(f"Tool_EX Messages:\n{state['messages']}")
        logger.info(f"Tool_EX Inner Messages:\n{state['inner_messages']}")

        node_name = "tool_executor"

        # 检查last_node字段
        last_node = state.get("last_node", "")
        logger.info(f"tool_executor_node: 当前last_node = {last_node}")

        if not last_node:
            logger.warning("tool_executor_node: last_node字段为空，这可能导致路由问题")

        # 获取最后一条消息（应该是 LLM 的响应）
        # 在进入子智能体时，先向对话中追加提示语
        log_index = len(state["logs"])
        state["logs"].append({
            "message": "执行工具调用",
            "done": False,
            "messageId": get_last_show_message_id(state["messages"])
        })

        # if not state.get("messages"):
        #     logger.error("tool_executor_node: 消息列表为空")
        #     error_message = AIMessage(content="工具节点消息列表为空", name=node_name)
        #     return Command(
        #         update={
        #             "messages": error_message,
        #             "inner_messages": error_message
        #         },
        #         goto=state["last_node"]
        #     )

        error_msg = None
        last_message = state["inner_messages"][-1]
        logger.info(f"enter tool_executor_node: {last_message} state:{state}")

        # 如果消息中包含工具调用
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info("tool_executor_node hasattr tool_calls")
            for tool_call in last_message.tool_calls:
                try:
                    tool_call_copy = deepcopy(tool_call)
                    tool_call_copy["args"]["state"] = state
                    tool_call_copy["args"]["special_config_param"] = {}
                    # 解析工具调用参数
                    tool_name = tool_call_copy["name"]
                    logger.info(f"tool_executor_node tool_name {tool_name}")
                    # 获取工具
                    if tool_name not in self.tools_by_name:
                        error_msg = f"工具 {tool_name} 不存在"
                        print(error_msg)
                        error_message = ToolMessage(content=error_msg, name=tool_name,
                                                    tool_call_id=tool_call_copy.get("id") or "")
                        state["messages"].append(error_message)
                        state["inner_messages"].append(error_message)
                        continue

                    tool = self.tools_by_name[tool_name]

                    # 如果调用了attachment工具，清除强制调用标志
                    if hasattr(tool, 'tool_type') and getattr(tool, 'tool_type') == 'attachment':
                        state["force_attachment_call"] = False
                        print(f"[tool_executor_node] 已调用附件工具 {tool_name}，清除强制调用标志")

                    # 执行工具调用
                    config['configurable']['tool_call_id'] = tool_call_copy.get("id", "")
                    state, tool_msg = await tool.ainvoke(tool_call_copy["args"], config=config)
                    # 文件URL改造
                    if hasattr(state["messages"][-1], "additional_kwargs"):
                        tool_calls = getattr(state["messages"][-1], 'additional_kwargs', {}).get('tool_calls', [])
                        for tool_call in tool_calls:
                            func = tool_call.get('function', {})
                            if func.get('name') == 'files':
                                try:
                                    args = json.loads(func['arguments'])
                                    if 'path' in args:
                                        # 从路径提取文件名
                                        args['name'] = os.path.basename(args['path'])
                                        args['date'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
                                        if 'content' in args:
                                            del args['content']
                                        func['arguments'] = json.dumps(args)
                                except (json.JSONDecodeError, KeyError) as e:
                                    print(f"参数处理错误: {e}")

                    # 使用统一的结果标准化方法
                    tool_msg = normalize_tool_result(tool_msg, tool_name)

                    # 增强调试信息：打印工具执行结果
                    print(f"\n========== 工具执行结果 ==========")
                    print(f"工具名称: {tool_name}")
                    print(f"执行状态: 成功")
                    print(f"结果长度: {len(tool_msg)} 字符")
                    print(f"结果预览 (前500字符):")
                    print(f"{tool_msg[:500]}...")
                    print("==================================\n")

                except GraphInterrupt:
                    # 捕捉GraphInterrupt但不处理，直接重新抛出
                    raise
                except Exception as e:
                    # 记录工具执行错误
                    traceback.print_exc()
                    error_msg = f"工具 {tool_call_copy['name']} 执行出错: {str(e)}"
                    print(error_msg)  # 日志记录
                    tool_msg = error_msg
                    # Remove the state key since we don't need to commit it into the saved state
                    tool_call_copy["args"]["state"] = None

                    # 增强调试信息：打印错误详情
                    print(f"\n========== 工具执行错误 ==========")
                    print(f"工具名称: {tool_call_copy['name']}")
                    print(f"错误类型: {type(e).__name__}")
                    print(f"错误信息: {str(e)}")
                    print("==================================\n")

                # 添加工具执行结果到消息列表
                tool_message = ToolMessage(
                    content=tool_msg,
                    name=tool_call_copy["name"],
                    tool_call_id=tool_call_copy.get("id") or ""
                )
                state["messages"].append(tool_message)
                state["inner_messages"].append(tool_message)

                # 记录工具执行状态
                if "tool_execution_history" not in state:
                    state["tool_execution_history"] = []

                state["tool_execution_history"].append({
                    "tool_name": tool_call_copy["name"],
                    "status": "success" if not error_msg else "error",
                    "timestamp": datetime.datetime.now().isoformat(),
                    "result_length": len(str(tool_msg))
                })

        # 设置执行过程完成
        state["logs"][log_index]["done"] = True
        state["logs"][log_index]["message"] = "工具智能体执行完成"

        # 正确设置状态更新，包含所有必要的字段
        state_update = {
            "messages": state["messages"],
            "inner_messages": state["inner_messages"],
            "last_node": state.get("last_node", ""),
            "iteration_count": state.get("iteration_count", 0),
            "completed": state.get("completed", False),
            "temporary_message_content_list": state.get("temporary_message_content_list", []),
            "current_step_completed": state.get("current_step_completed", False),
            "current_step_index": state.get("current_step_index", 0),
            "execution_results": state.get("execution_results", []),
            "logs": state.get("logs", []),
            "e2b_sandbox_id": state.get("e2b_sandbox_id", ""),
            "max_iterations": state.get("max_iterations", 50),
            "temporary_images": state.get("temporary_images", []),
            "structure_tool_results": state.get("structure_tool_results", []),
            "input_data": state.get("input_data", {}),
            "model": state.get("model", ""),
            "a2a_agents": state.get("a2a_agents", []),
            "a2a_sessions": state.get("a2a_sessions", {}),
            "route_to_a2a": state.get("route_to_a2a", ""),
            "last_a2a_result": state.get("last_a2a_result", ""),
            "a2a_failure_count": state.get("a2a_failure_count", 0),
            "a2a_fallback_to_general": state.get("a2a_fallback_to_general", False),
            "failed_a2a_agents": state.get("failed_a2a_agents", []),
            "supervisor_retry_count": state.get("supervisor_retry_count", 0),
            "supervisor_decision": state.get("supervisor_decision", ""),
            "workflow_steps": state.get("workflow_steps", []),
            "workflow_plan": state.get("workflow_plan", {}),
            "tool_execution_history": state.get("tool_execution_history", [])
        }

        # 修复路由逻辑，防止调用链中断
        last_node = state.get("last_node", "")

        logger.info(f"last_node in tool_ex node: {last_node}")

        if not last_node:
            logger.warning("last_node字段为空，使用默认路由到supervisor")
            return Command(update=state_update, goto="supervisor")

        # 根据last_node决定下一步，确保调用链完整
        # if last_node in ["coder", "researcher",  "reporter"]:
        #     logger.info(f"工具执行完成，返回到智能体节点: {last_node}")
        #     return Command(update=state_update, goto=last_node)
        # else:
        #     # 未知节点，回到supervisor进行决策
        #     logger.warning(f"未知的last_node: {last_node}，回到supervisor")
        return Command(update=state_update, goto="supervisor")

    async def a2a_node(self, state: AgentState, config: RunnableConfig) -> Command[Literal["supervisor"]]:
        """
        创建通用的 A2A 智能体执行器节点
        该节点根据状态中的路由决策调用相应的 A2A 智能体

        Args:
            state: 智能体状态
            config: 运行配置

        Returns:
            AgentState: 更新后的状态
        """
        node_name = "a2a_agent"
        state_update = {}

        print("=== A2A 智能体执行器节点开始 ===")
        log_index = len(state["logs"])
        state["logs"].append({
            "message": "A2A智能体执行中",
            "done": False,
            "messageId": get_last_show_message_id(state["messages"])
        })
        await copilotkit_emit_state(config, state)

        # # 获取路由决策
        route_decision = state.get("route_to_a2a")
        # if not route_decision or route_decision == "通用智能体":
        #     print("❌ A2A执行器收到无效的路由决策，直接返回")
        #     return state

        # 从已预加载的 A2A 智能体中找到对应的节点信息
        node_info = self.a2a_manager.a2a_agent_nodes.get(route_decision)

        if not node_info:
            print(f"❌ 未找到 A2A 智能体: {route_decision}")

            # 添加详细的错误消息
            available_agents = []
            for node_name, info in self.a2a_manager.a2a_agent_nodes.items():
                agent_name = info["agent_info"].get("name", "Unknown")
                available_agents.append(f"{agent_name} ({node_name})")

            available_str = "、".join(available_agents) if available_agents else "无"

            error_message = AIMessage(content=f"""❌ **A2A智能体执行失败**

    **问题**: 无法找到或连接到智能体 `{route_decision}`

    **可用智能体**: {available_str}

    **建议**: 请稍后重试或使用通用智能体服务。

    正在重新进行智能体选择...""", name=node_name)

            state["messages"].append(error_message)
            state["inner_messages"].append(error_message)

            # 记录失败的智能体
            failed_agents = state.get("failed_a2a_agents", [])
            if route_decision not in failed_agents:
                failed_agents.append(route_decision)
            state["failed_a2a_agents"] = failed_agents

            # 重新回到supervisor
            state["route_to_a2a"] = None
            state["supervisor_retry_count"] = state.get("supervisor_retry_count", 0) + 1

            state["logs"][-1]["done"] = True
            state["logs"][-1]["message"] = "A2A智能体执行失败"

            return Command(
                update={
                    "messages": state["messages"],
                    "inner_messages": state["inner_messages"],
                    "failed_a2a_agents": state["failed_a2a_agents"],
                    "route_to_a2a": state["route_to_a2a"],
                    "supervisor_retry_count": state["supervisor_retry_count"],
                    "logs": state["logs"]
                },
                goto="supervisor",
            )

        # 获取 A2A 智能体信息
        agent_info = create_a2a_agent_info_from_config(node_info["agent_info"])

        print(f"🚀 执行 A2A 智能体: {agent_info.name}")

        # 调用真正的 A2A 智能体节点函数
        # 注意：这里需要使用 Command 的结果来更新状态
        try:
            state_update = await a2a_agent_node(state, config, agent_info=agent_info)
        except Exception as e:
            print(f"❌ A2A 智能体 {agent_info.name} 执行异常: {str(e)}")
            import traceback
            traceback.print_exc()

            # 🔥 检查是否已经添加过相同的错误消息，避免重复
            error_content = f"A2A 智能体 {agent_info.name} 执行异常: {str(e)}"

            # 检查是否已经存在相同的错误消息
            existing_error = False
            for msg in state.get("messages", []):
                if hasattr(msg, 'content') and error_content in msg.content:
                    existing_error = True
                    break

            if not existing_error:
                error_message = AIMessage(content=error_content, name=node_name)
                state_update = {
                    "messages": error_message,
                    "inner_messages": error_message,
                    "completed": True
                }
            else:
                state_update = {
                    "completed": True
                }

            state["logs"][-1]["done"] = True
            state["logs"][-1]["message"] = "A2A智能体执行异常"
            state_update["logs"] = state["logs"]  # 用于整体对话结束后的logs状态保存

            return Command(update=state_update, goto="supervisor")

        state["logs"][log_index]["done"] = True
        state["logs"][log_index]["message"] = "A2A智能体执行完成"
        state_update["logs"] = state["logs"]  # 用于整体对话结束后的logs状态保存

        print("=== A2A 智能体执行器节点完成 ===")

        return Command(update=state_update, goto="supervisor")

    async def mcp_node(self, state: AgentState, config: RunnableConfig) -> Command[
        Literal["supervisor", "mcp_tool_executor"]]:

        logger.info("=== MCP 智能体数据准备节点开始 ===")
        log_index = len(state["logs"])
        state["log_index"] = log_index
        message_id = get_last_show_message_id(state["messages"])
        state["logs"].append({
            "message": "MCP智能体运行中",
            "done": False,
            "messageId": message_id,
            "sub_logs": [{
                "message": "🔧 工具准备中",
                "done": False,
            }]
        })
        await copilotkit_emit_state(config, state)

        # 获取 MCP 工具
        mcp_tools = await self.mcp_client.get_tools()

        mcp_tools_for_copilotkit: List[Dict[str, Any]] = state.get("copilotkit", {}).get("actions", [])
        # 调试输出
        print(f"从状态中获取的 MCP 工具数量: {len(mcp_tools)}")

        # 所有MCP工具
        all_tools = [*mcp_tools]

        # 绑定工具到LLM实例
        llm, model_name = get_llm_client(state, config)
        try:
            llm = llm.bind_tools(all_tools)
            print(f"成功绑定 {len(mcp_tools)} 个工具到LLM")
        except Exception as e:
            print(f"绑定工具失败: {str(e)}")

        def enhance_mcp_tool_description(name: str, description: str) -> str:
            base_desc = (description or "").strip()
            lowered_name = (name or "").lower()

            is_browser_task = lowered_name == "browser_task"

            if not is_browser_task:
                return base_desc

            extra = (
                " This tool should be preferred whenever the user asks to open a website,"
                " browse or extract content from web pages, or fill/submit web forms."
                " Use it to create a browser automation task for these web interactions"
                " instead of relying only on static search or reasoning."
            )

            if not base_desc:
                return extra.strip()

            return base_desc + " " + extra

        # 从原始状态数据获取字典格式的 MCP 工具用于生成 prompt
        mcp_tools_dict_for_prompt = []
        for tool in mcp_tools:
            parameters = {}
            if hasattr(tool, "args"):
                parameters = tool.args
            elif hasattr(tool, "args_schema") and tool.args_schema:
                try:
                    parameters = tool.args_schema.schema()
                except Exception:
                    pass

            enhanced_description = enhance_mcp_tool_description(
                getattr(tool, "name", ""),
                getattr(tool, "description", ""),
            )

            tool_dict = {
                'name': tool.name,
                'description': enhanced_description,
                'parameters': parameters
            }
            mcp_tools_dict_for_prompt.append(tool_dict)

        all_mcp_tools_for_prompt = mcp_tools_for_copilotkit + mcp_tools_dict_for_prompt

        # 清理 MCP 工具 prompt
        # format_mcp_tools_for_prompt_english 已通过顶部 from langgraph_agent.prompts import * 导入
        try:
            mcp_tools_prompt = format_mcp_tools_for_prompt_english(all_mcp_tools_for_prompt)
            mcp_tools_prompt = sanitize_string_for_json(mcp_tools_prompt, context="api")
            mcp_tools_prompt = (
                    "\n\n <mcp_tools_mounted_status>" + mcp_tools_prompt + "</mcp_tools_mounted_status>") if mcp_tools_prompt else ""
        except Exception as e:
            print(f"⚠️ MCP工具prompt生成失败: {str(e)}")
            mcp_tools_prompt = ""

        # 使用llm判断需要使用哪些工具
        await self._compress_conversation_for_llm(state, model_name)

        state_update = await agent_node(state, config, llm, mcp_tools_prompt, "mcp_tools")
        if state.get("context_compression"):
            state_update["context_compression"] = state["context_compression"]

        # 确保last_node字段被正确设置
        if "last_node" not in state_update:
            state_update["last_node"] = "mcp_tools"

        # 检查最后一条消息是否有工具调用
        last_message = state_update.get("messages")[-1] if state_update.get("messages") else None
        if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info(f"[MCP智能体数据准备] 检测到工具调用: {[tc['name'] for tc in last_message.tool_calls]}")

            state["logs"][log_index]["sub_logs"][0]["message"] = "🔧 工具准备完成"
            state["logs"][log_index]["sub_logs"][0]["done"] = True
            state["logs"][log_index]["sub_logs"].append({
                "message": "🔍 参数检查完成",
                "done": True,
            })
            await copilotkit_emit_state(config, state)

            # 储存mcp_tool数据
            all_tools_by_name = {}
            for mcp_tool in mcp_tools:
                all_tools_by_name[mcp_tool.name] = mcp_tool

            tools = []
            for tool_call in last_message.tool_calls:
                tool_call_copy = deepcopy(tool_call)
                tool_name = tool_call_copy["name"]

                # 简化工具数据准备，直接使用工具调用参数
                # add message unique id, guarantee the command state can be merged correctly
                # TODO: if there are two tool_call in one message, the message unique id will be the same, this will cause the command state can not be merged correctly
                tools.append({
                    "id": last_message.id,
                    "name": tool_name,
                    "arguments": tool_call_copy["args"],
                    "tool_call_id": tool_call_copy.get("id", "")
                })

            # delete last tool_call message, avoid duplicate AIMessage which contain tool_call
            state_update["messages"] = state_update["messages"][:-1]
            state_update["inner_messages"] = copy.deepcopy(state_update["messages"])
            state_update["logs"] = state["logs"]  # 用于整体对话结束后的logs状态保存
            state_update["mcp_tool_executor_data"] = tools

            logger.info("=== MCP 智能体数据准备节点完成 ===")

            return Command(update=state_update, goto="mcp_tool_executor")
        else:
            # 没有工具调用，直接返回到supervisor
            state["logs"][log_index]["sub_logs"][0]["message"] = "🔧 工具准备完成，没有工具调用"
            state["logs"][log_index]["sub_logs"][0]["done"] = True
            state["logs"][log_index]["done"] = True
            state["logs"][log_index]["message"] = "MCP智能体运行完成"
            await copilotkit_emit_state(config, state)

            state_update["logs"] = state["logs"]  # 用于整体对话结束后的logs状态保存

            logger.info("=== MCP 智能体数据准备节点完成 ===")

            return Command(update=state_update, goto="supervisor")

    async def mcp_executor_node(self, state: AgentState, config: RunnableConfig) -> Command[
        Literal["supervisor", "mcp_tool"]]:
        """MCP工具执行节点 - 委托给MCP工具管理器处理"""
        logger.info("=== MCP 智能体执行器节点开始 ===")

        # 从state中获取数据准备节点保存的数据
        tools = state.get("mcp_tool_executor_data", [])
        logger.info(f"待执行工具数量: {len(tools)}")

        # 某些异常分支可能未设置 log_index，这里兜底防止 KeyError
        log_index = state.get("log_index", -1)
        logs_list = state.get("logs", [])
        has_log_slot = isinstance(logs_list, list) and 0 <= log_index < len(logs_list)

        state_update = {
            "messages": [],
            "inner_messages": [],
            "logs": [],
            "last_node": "mcp_tool_executor",
            "mcp_tool_executor_data": state.get("mcp_tool_executor_data", []),
            "mcp_tool_execution_results": state.get("mcp_tool_execution_results", []),
        }

        for tool_call in tools:
            logger.info(f"=== MCP 智能体执行器节点开始执行工具: {tool_call['name']} ===")
            logger.info(f"工具: {tool_call}")

            tool_name = tool_call["name"]
            # 原始参数用于实际工具调用，保持 schema 兼容
            arguments = deepcopy(tool_call["arguments"])

            tool_call_id = tool_call.get("tool_call_id", f"tool-{uuid.uuid4()}")
            # 带 id 的副本仅用于前端事件/消息传递
            temp_arguments = deepcopy(arguments)
            temp_arguments["id"] = tool_call_id

            if has_log_slot:
                sub_log_index_for_tool = len(state["logs"][log_index].get("sub_logs", []))
                state["logs"][log_index].setdefault("sub_logs", []).append({
                    "message": f"{tool_name} 工具执行中",
                    "done": False,
                })
                await copilotkit_emit_state(config, state)
            else:
                sub_log_index_for_tool = -1

            # 临时提交tool_call信息，并保存在messages中
            await send_temp_tool_call_to_frontend(tool_name, temp_arguments, tool_call_id, config)
           
            tool_call_obj = ToolCall(name=tool_name, args=temp_arguments, id=tool_call_id)
            state_update["messages"].append(AIMessage(name=tool_name, id=tool_call["id"], content="", tool_calls=[tool_call_obj]))
            state_update["inner_messages"].append(AIMessage(name=tool_name, id=tool_call["id"], content="", tool_calls=[tool_call_obj]))

            try:
                # 获取工具实例并执行
                tool = await self.mcp_client.get_tool_by_name(tool_name)
                if not tool:
                    raise ValueError(f"工具 {tool_name} 未找到")

                # 执行工具调用
                tool_result = await tool.ainvoke(arguments)
                print("tool_result:{}".format(tool_result))

                # 处理工具执行结果
                if hasattr(tool_result, 'content'):
                    tool_msg = tool_result.content
                else:
                    tool_msg = str(tool_result)

                # 提交MCP工具运行结果的ToolMessage
                tool_message = ToolMessage(name=tool_name, content=tool_msg, tool_call_id=tool_call_id)
                state_update["inner_messages"].append(tool_message)
                state_update["messages"].append(tool_message)

                state_update["mcp_tool_execution_results"].append({
                    "id": tool_call_id,
                    "result": tool_message.content,
                    "status": "success"
                })

                # 对 browser-use 的 monitor_task 工具，保存步骤信息到状态中
                if tool_name == "monitor_task":
                    parsed_steps = None
                    try:
                        import json as _json
                        parsed = _json.loads(tool_msg)
                        if isinstance(parsed, dict):
                            parsed_steps = parsed
                        else:
                            parsed_steps = {"raw": parsed}
                    except Exception:
                        parsed_steps = {"raw": tool_msg}

                    state["browser_use_steps"] = parsed_steps
                    state_update["browser_use_steps"] = parsed_steps

                # 增强调试信息：打印工具执行结果
                print(f"\n========== 工具执行结果 ==========")
                print(f"工具名称: {tool_name}")
                print(f"执行状态: 成功")
                print(f"结果长度: {len(tool_msg)} 字符")
                print(f"结果预览 (前500字符):")
                print(f"{tool_msg[:500]}...")
                print("==================================\n")

                state["logs"][log_index]["sub_logs"][sub_log_index_for_tool]["message"] = f"⚙️ {tool_name} 工具执行成功"
                state["logs"][log_index]["sub_logs"][sub_log_index_for_tool]["done"] = True
                await copilotkit_emit_state(config, state)
            except Exception as e:
                # 记录工具执行错误
                traceback.print_exc()
                raw_error = str(e)
                # 清理异常内容，避免把整段 HTML 或超长文本塞进对话，导致上下文暴涨
                cleaned_error = re.sub(r"<[^>]+>", "", raw_error)
                max_len = 800
                if len(cleaned_error) > max_len:
                    cleaned_error = cleaned_error[:max_len] + "...(truncated)"
                error_msg = f"工具 {tool_name} 执行出错: {cleaned_error}"
                print(error_msg)  # 日志记录
                tool_msg = error_msg

                # 提交错误结果的ToolMessage
                tool_message = ToolMessage(name=tool_name, content=tool_msg, tool_call_id=tool_call_id)
                state_update["inner_messages"].append(tool_message)
                state_update["messages"].append(tool_message)
                state_update["mcp_tool_execution_results"].append({
                    "id": tool_call_id,
                    "result": "未获取到工具结果",
                    "status": "failed"
                })

                # 增强调试信息：打印错误详情
                print(f"\n========== 工具执行错误 ==========")
                print(f"工具名称: {tool_name}")
                print(f"错误类型: {type(e).__name__}")
                print(f"错误信息: {cleaned_error}")
                print("==================================\n")

                state["logs"][log_index]["sub_logs"][sub_log_index_for_tool]["message"] = f"⚙️ {tool_name} 工具执行异常"
                state["logs"][log_index]["sub_logs"][sub_log_index_for_tool]["done"] = True
                await copilotkit_emit_state(config, state)

        logger.info("=== MCP 智能体执行器节点完成 ===")

        state["logs"][log_index]["done"] = True
        state["logs"][log_index]["message"] = "MCP智能体运行完成"
        state["log_index"] = -1  # 重置log_index
        await copilotkit_emit_state(config, state)

        state_update["logs"] = state["logs"]  # 用于整体对话结束后的logs状态保存

        return Command(update=state_update, goto="supervisor")

    def _build_workflow(self):
        """
        构建工作流图，并存储编译后的结果 - 支持Supervisor模式
        """
        # 这个方法会在初始化时调用，此时还没有状态信息
        # 所以我们构建一个能够动态适应的工作流
        self._build_adaptive_workflow()

    def _build_adaptive_workflow(self):
        """
        构建支持真正 A2A 智能体节点的自适应工作流 - 添加HTML生成支持
        """
        # 创建图
        workflow = StateGraph(AgentState)

        # 初始化节点
        workflow.add_edge(START, "initial_setup")
        workflow.add_node("initial_setup", self.initial_setup_node)

        # 对话节点（在该节点进行判断，如果用户意图是进行简单对话，调用大模型回复并直接结束）
        workflow.add_node("coordinator", self.coordinator_node)

        # supervisor
        workflow.add_node("supervisor", self.supervisor_node)

        # 智能体节点
        workflow.add_node("coder", self.code_node)
        workflow.add_node("researcher", self.research_node)
        # workflow.add_node("browser", self.browser_node)
        workflow.add_node("reporter", self.reporter_node)

        # 工具执行节点
        workflow.add_node("tool_executor", self.tool_executor_node)

        # 添加通用的 A2A 智能体节点
        workflow.add_node("a2a_agent", self.a2a_node)
        # 添加mcp工具节点
        workflow.add_node("mcp_tool", self.mcp_node)
        workflow.add_node("mcp_tool_executor", self.mcp_executor_node)

        # 编译图并保存
        self.graph = workflow.compile(
            # 设置递归限制，避免无限循环
            checkpointer=None,  # 不使用检查点
        )

        print("图构建完成")

    async def add_dynamic_a2a_nodes(self, state: AgentState, config: RunnableConfig):
        """
        # 由于工作流已经编译，我们不能直接添加新节点
        # 但我们可以记录A2A智能体信息，供路由决策使用
        """
        # 从状态中获取A2A智能体信息
        a2a_agents = get_a2a_agents_from_state(state)
        if not a2a_agents:
            print("没有发现A2A智能体，跳过动态添加")
            return

        for agent in a2a_agents:
            agent_id = agent.agent_id
            node_name = f"a2a_{agent.name}"

            # 创建A2A智能体节点函数
            # agent_node_func = await a2a_agent_node(state, config, agent)

            # 存储节点信息
            self.a2a_manager.a2a_agent_nodes[node_name] = {
                "agent_id": agent_id,
                "agent_info": agent,
                # "node_func": agent_node_func
            }

            print(f"已准备A2A智能体: {node_name} ({agent.name})")

        print(f"总共准备了 {len(self.a2a_manager.a2a_agent_nodes)} 个A2A智能体")

    # 公开的方法，支持运行时配置递归限制
    async def ainvoke(self, state: AgentState, config: Optional[Dict[str, Any]] = None) -> AgentState:
        """
        异步调用智能体图 - 支持递归限制配置

        Args:
            state: 智能体状态
            config: 运行时配置，可包含 recursion_limit

        Returns:
            AgentState: 更新后的状态
        """
        # 设置默认配置
        if config is None:
            config = {}

        # 设置递归限制，避免无限循环
        if 'recursion_limit' not in config:
            config['recursion_limit'] = 30  # 降低递归限制

        # 确保 configurable 存在
        if 'configurable' not in config:
            config['configurable'] = {}

        print(f"开始执行智能体图，递归限制: {config.get('recursion_limit', 30)}")

        try:
            result = await self.graph.ainvoke(state, config)
            return result
        except Exception as e:
            print(f"智能体图执行异常: {str(e)}")
            # 确保在异常情况下也能返回有效状态
            if 'completed' not in state:
                state['completed'] = True
            if 'messages' not in state:
                state['messages'] = []

            # 添加错误消息
            error_message = AIMessage(content=f"执行过程中发生异常: {str(e)}")
            state['messages'].append(error_message)

            return state


# 创建并导出编译好的图实例
agent_graph = AgentGraph().graph
