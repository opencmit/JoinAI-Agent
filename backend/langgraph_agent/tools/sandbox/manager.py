from functools import lru_cache
from typing import Optional
from dotenv import load_dotenv
from langgraph_agent.graph.state import AgentState
import traceback
import os
from e2b_desktop import Sandbox as DesktopSandbox
from e2b_desktop import AsyncSandbox

load_dotenv()

class SandboxManager:
    """Sandbox管理器，负责创建和管理sandbox实例，使用LRU缓存以提高性能"""

    def __init__(self, api_key: Optional[str] = None):
        # 使用官方在线 E2B 沙箱
        self.api_key = api_key or os.getenv("E2B_API_KEY", "")
        timeout_str = os.getenv("E2B_SANDBOX_TIMEOUT", "3600")
        try:
            self.timeout = int(timeout_str)
        except Exception:
            self.timeout = 3600
        print("sandbox timeout:", self.timeout)
        if not self.api_key:
            print("未检测到 E2B_API_KEY，创建/连接沙箱可能会失败。")

    # @lru_cache(maxsize=10)  # 最多缓存10个sandbox实例
    async def get_sandbox_async(self, state: AgentState) -> tuple[AgentState, AsyncSandbox]:
        """
        获取一个异步sandbox实例。如果提供了sandbox_id，尝试连接到现有实例；
        否则创建新实例。

        Args:
            state: 包含sandbox_id的状态对象

        Returns:
            更新后的状态和Sandbox实例的元组
        """
        sbx = None
        if state["e2b_sandbox_id"]:
            try:
                sbx = await AsyncSandbox.connect(
                    sandbox_id=state["e2b_sandbox_id"],
                    api_key=self.api_key,
                )
            except Exception as e:
                print(f"连接到现有sandbox失败: {e}")
        if not sbx:
            print("------create sandbox---------")
            sbx = await self._create_new_sandbox()
        state["e2b_sandbox_id"] = sbx.sandbox_id
        return state, sbx

    def get_sandbox(self, state: AgentState) -> tuple[AgentState, DesktopSandbox]:
        """
        获取一个同步sandbox实例。如果提供了sandbox_id，尝试连接到现有实例；
        否则创建新实例。

        Args:
            state: 包含sandbox_id的状态对象

        Returns:
            更新后的状态和Sandbox实例的元组
        """
        sbx = None
        if state["e2b_sandbox_id"]:
            try:
                sbx = DesktopSandbox(
                    sandbox_id=state["e2b_sandbox_id"],
                    api_key=self.api_key,
                    display=":0",  # Custom display (defaults to :0)
                    resolution=(1280, 720),  # Custom resolution
                    dpi=96,  # Custom DPI
                )
            except Exception as e:
                print(f"连接到现有sandbox失败: {e}")
                traceback.print_exc()
        if not sbx:
            sbx = self._create_new_sandbox_sync()
        state["e2b_sandbox_id"] = sbx.sandbox_id
        return state, sbx

    async def _create_new_sandbox(self) -> AsyncSandbox:
        """创建新的异步sandbox实例"""
        try:
            return await AsyncSandbox.create(api_key=self.api_key, timeout=self.timeout)
        except TypeError:
            return await AsyncSandbox.create(api_key=self.api_key)

    def _create_new_sandbox_sync(self) -> DesktopSandbox:
        """创建新的同步sandbox实例"""
        try:
            return DesktopSandbox(
                api_key=self.api_key,
                timeout=self.timeout,
                display=":0",  # Custom display (defaults to :0)
                resolution=(1280, 720),  # Custom resolution
                dpi=96,  # Custom DPI
            )
        except TypeError:
            return DesktopSandbox(
                api_key=self.api_key,
                display=":0",  # Custom display (defaults to :0)
                resolution=(1280, 720),  # Custom resolution
                dpi=96,  # Custom DPI
            )

sbx_manager = SandboxManager()

async def test_sandbox_manager():
    state = AgentState(
        copilotkit={"actions": []},
        messages=[],
        logs=[],
        e2b_sandbox_id="e2b_sandbox_id"
    )
    _, desktop_sbx = sbx_manager.get_sandbox(state)
    print(type(desktop_sbx))
    print(desktop_sbx.sandbox_id)
    print(desktop_sbx.stream.get_url())
    desktop_sbx.screenshot()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_sandbox_manager())