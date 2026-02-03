import asyncio
import os
import sys
import logging
from typing import Dict, Any, List

# 确保可以 import langgraph_agent 包
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_PKG_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_PKG_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_PKG_ROOT)

from langgraph.types import Command
from langgraph_agent.graph.graph import AgentGraph
from langgraph_agent.graph.a2a_agent import A2AHttpClient, A2AExecutionResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_a2a_three_agents")


# 打桩 A2A 调用，避免真实网络请求
async def fake_call_a2a_agent(self, agent_id: str, session_id: str, messages, user_id: str = "") -> A2AExecutionResult:
    logger.info(f"[MOCK] A2A 被调用: agent_id={agent_id}, session_id={session_id}, user_id={user_id}")
    logger.info(f"[MOCK] messages count: {len(messages)}")
    preview = messages[0]["content"][:80] if messages and isinstance(messages[0], dict) else ""
    logger.info(f"[MOCK] first message: {preview}...")
    return A2AExecutionResult(
        type="text",
        content=f"mock-success for {agent_id}",
        final=True,
        status=True,
        session_id=session_id,
    )


def build_three_agents() -> List[Dict[str, Any]]:
    return [
        {
            "agent_id": "agent_alpha",
            "name": "结构化分析师",
            "desc": "负责对输入进行结构化抽取和解析",
            "user_id": "u_001",
            "type": "normal",
        },
        {
            "agent_id": "agent_beta",
            "name": "网页处理器",
            "desc": "进行网页抓取、清洗与内容提取",
            "user_id": "u_002",
            "type": "normal",
        },
        {
            "agent_id": "agent_gamma",
            "name": "报告撰写官",
            "desc": "将已有内容组织为专业报告",
            "user_id": "u_003",
            "type": "normal",
        },
    ]


async def main():
    # 避免真实网络请求
    os.environ.setdefault("A2A_BASE_URL", "http://mock.local")

    # 1) 构造初始 state，包含 3 个 a2a_agents
    a2a_agents = build_three_agents()
    initial_state: Dict[str, Any] = {
        "messages": [],
        "a2a_agents": a2a_agents,
        # 通过 input.message 注入一条人类消息
        "input": {
            "message": [
                {"type": "human", "content": "请根据需求自动选择并依次调用合适的外部专家。"}
            ]
        },
    }

    # 2) 实例化图对象
    agent = AgentGraph()

    # 3) 运行 initial_setup_node，完成状态初始化与 A2A 预加载
    cfg: Dict[str, Any] = {"configurable": {"session_id": "test_session_three"}}
    setup_cmd: Command = await agent.initial_setup_node(initial_state, cfg)

    # 合并初始和返回状态
    state: Dict[str, Any] = {**initial_state, **(setup_cmd.update or {})}

    # 4) 验证 A2A 是否被预加载
    print("\n=== 预加载的 A2A 智能体（应为3） ===")
    for k, v in agent.a2a_manager.a2a_agent_nodes.items():
        print(f"{k} -> {v['agent_info']}")
    if len(agent.a2a_manager.a2a_agent_nodes) != 3:
        print("❌ 预加载数量不符合预期")
        return

    # 5) 为每个智能体设置一次路由并执行 a2a_node
    # 打桩 A2A 客户端
    A2AHttpClient.call_a2a_agent = fake_call_a2a_agent

    print("\n=== 逐个路由到各 A2A 智能体并执行 ===")
    route_ids = [f"a2a_{a['agent_id']}" for a in a2a_agents]
    for idx, route_id in enumerate(route_ids, 1):
        print(f"\n--- 测试 {idx}: 路由 -> {route_id} ---")
        state["route_to_a2a"] = route_id
        cmd: Command = await agent.a2a_node(state, cfg)

        print(f"goto: {cmd.goto}")
        print(f"has update: {bool(cmd.update)}")

        # 合并状态
        state = {**state, **(cmd.update or {})}

        print("尾部消息预览:")
        tail_msgs = state.get("messages", [])[-2:]
        for i, m in enumerate(tail_msgs, 1):
            try:
                name = getattr(m, "name", "")
                content = getattr(m, "content", "")
                print(f"[{i}] {name} -> {content}")
            except Exception:
                print(f"[{i}] {m}")

        print("关键状态字段:")
        print(f"route_to_a2a: {state.get('route_to_a2a')}")
        print(f"last_a2a_result: {state.get('last_a2a_result')}")
        print(f"a2a_failure_count: {state.get('a2a_failure_count')}")

    print("\n=== 测试结束 ===")


if __name__ == "__main__":
    asyncio.run(main())
