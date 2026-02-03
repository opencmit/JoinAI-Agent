import asyncio
import os
import sys
import logging
from typing import Dict, Any

# 确保可以 import langgraph_agent 包
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_PKG_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_PKG_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_PKG_ROOT)

from langgraph.types import Command

from langgraph_agent.graph.graph import AgentGraph
from langgraph_agent.graph.a2a_agent import A2AHttpClient, A2AExecutionResult


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_a2a")


# 打桩 A2A 调用，避免真实网络请求
async def fake_call_a2a_agent(self, agent_id: str, session_id: str, messages, user_id: str = "") -> A2AExecutionResult:
    logger.info(f"[MOCK] A2A 被调用: agent_id={agent_id}, session_id={session_id}, user_id={user_id}")
    logger.info(f"[MOCK] messages: {messages}")
    return A2AExecutionResult(
        type="text",
        content=f"mock-success for {agent_id}",
        final=True,
        status=True,
        session_id=session_id,
    )


async def main():
    # 确保不会访问真实A2A地址
    os.environ.setdefault("A2A_BASE_URL", "http://mock.local")

    # 1) 构造初始 state，包含 a2a_agents
    test_agent = {
        "agent_id": "agent_001",
        "name": "数据分析师",
        "desc": "擅长数据分析与可视化",
        "user_id": "user_abc",
        "type": "normal",
    }

    initial_state: Dict[str, Any] = {
        "messages": [],
        "a2a_agents": [test_agent],
        # 通过 input.message 注入一条人类消息
        "input": {
            "message": [
                {"type": "human", "content": "请用A2A专家帮我分析一组数据。"}
            ]
        },
    }

    # 2) 实例化图对象
    agent = AgentGraph()

    # 3) 运行 initial_setup_node，完成状态初始化与 A2A 预加载（用 dict 传递，避免Pydantic必填字段校验）
    cfg: Dict[str, Any] = {"configurable": {"session_id": "test_session"}}
    setup_cmd: Command = await agent.initial_setup_node(initial_state, cfg)

    # 合并初始和返回状态
    state: Dict[str, Any] = {**initial_state, **(setup_cmd.update or {})}

    # 4) 验证 A2A 是否被预加载
    print("\n=== 预加载的 A2A 智能体（应>=1） ===")
    for k, v in agent.a2a_manager.a2a_agent_nodes.items():
        print(f"{k} -> {v['agent_info']}")
    if not agent.a2a_manager.a2a_agent_nodes:
        print("❌ 未发现任何预加载的A2A智能体")
        return

    # 5) 设置 supervisor 决策（模拟），路由到特定 A2A（以 agent_id 为准）
    route_id = f"a2a_{test_agent['agent_id']}"
    state["route_to_a2a"] = route_id

    # 6) 打桩 A2A 客户端
    A2AHttpClient.call_a2a_agent = fake_call_a2a_agent

    # 7) 调用 a2a_node 验证是否真正走到 A2A
    cmd: Command = await agent.a2a_node(state, cfg)

    # 8) 打印结果
    print("\n=== a2a_node 返回 ===")
    print(f"goto: {cmd.goto}")
    print(f"has update: {bool(cmd.update)}")

    final_state: Dict[str, Any] = {**state, **(cmd.update or {})}

    print("\n=== 最终消息(尾部2条) ===")
    tail_msgs = final_state.get("messages", [])[-2:]
    for i, m in enumerate(tail_msgs, 1):
        try:
            name = getattr(m, "name", "")
            content = getattr(m, "content", "")
            print(f"[{i}] {name} -> {content}")
        except Exception:
            print(f"[{i}] {m}")

    print("\n=== 关键状态字段 ===")
    print(f"route_to_a2a: {final_state.get('route_to_a2a')}")
    print(f"last_a2a_result: {final_state.get('last_a2a_result')}")
    print(f"a2a_failure_count: {final_state.get('a2a_failure_count')}")


if __name__ == "__main__":
    asyncio.run(main())
