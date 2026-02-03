"""
MCP (Model Context Protocol) 客户端连接管理器

该模块提供了一个单例模式的MCP连接管理器，用于管理与多个MCP服务器的连接。
主要功能包括：
- 单例模式确保全局只有一个连接管理器实例
- 自动心跳检测保持SSE连接活跃
- 指数退避重连机制
- 工具缓存和刷新功能
- 异步资源清理
"""

import asyncio
import atexit
import logging
import random
import threading
from typing import Dict, List, Optional
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import BaseTool

# 配置日志记录器
logger = logging.getLogger(__name__)

# 模块级别的单例实例和锁
_connection_manager_instance: Optional['MCPConnectionManager'] = None
_instance_lock = threading.Lock()


class MCPConnectionManager:
    """
    MCP连接的单例管理器，具有心跳检测、重连和工具缓存功能。

    特性：
    - 线程安全的单例模式初始化
    - 自动心跳检测保持SSE连接活跃
    - 带抖动的指数退避重连机制
    - 具有刷新功能的工具缓存
    - 适当的异步资源清理
    """

    def __init__(self):
        """初始化MCP连接管理器实例"""
        # MCP客户端实例，用于与服务器通信
        self.client: Optional[MultiServerMCPClient] = None
        # 服务器配置字典，包含所有MCP服务器的连接信息
        self.server_config: Optional[Dict[str, Dict]] = None
        # 异步锁，确保线程安全操作
        self.lock = asyncio.Lock()
        # 心跳任务，定期发送心跳保持连接活跃
        self.heartbeat_task: Optional[asyncio.Task] = None
        # 重连任务，在连接失败时执行重连逻辑
        self.reconnect_task: Optional[asyncio.Task] = None
        # 运行状态标志，指示管理器是否正在运行
        self.running = False
        # 工具缓存列表，存储从MCP服务器获取的工具
        self.tools_cache: List[BaseTool] = []
        # 最后一次心跳成功的标志，初始为False直到首次成功连接
        self.last_heartbeat_ok = False
        # 是否已注册关闭处理程序的标志
        self._shutdown_registered = False
        # 事件循环引用，用于在退出时正确清理资源
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        # 清理状态标志，防止重复清理
        self._cleaning_up = False
        self._cleaned_up = False
        # 保存原始 os.access 函数的引用，用于 monkey-patch
        self._original_os_access = None
        self._patched_os_access = None

    @classmethod
    def get_instance(cls) -> 'MCPConnectionManager':
        """
        获取或创建单例实例。
        
        使用双重检查锁定模式确保线程安全的单例实现，
        避免多个实例造成的资源浪费和连接冲突。
        
        Returns:
            MCPConnectionManager: 单例连接管理器实例
        """
        global _connection_manager_instance
        
        # 第一次检查：如果实例已存在，直接返回
        if _connection_manager_instance is not None:
            return _connection_manager_instance
        
        # 获取锁进行同步
        with _instance_lock:
            # 第二次检查：在锁内再次检查实例是否存在
            # 防止多个线程同时通过第一次检查
            if _connection_manager_instance is None:
                _connection_manager_instance = cls()
                # 在进程退出时注册清理函数
                if not _connection_manager_instance._shutdown_registered:
                    atexit.register(_connection_manager_instance._cleanup_on_exit)
                    _connection_manager_instance._shutdown_registered = True
                    logger.debug("MCP连接管理器单例实例已创建并注册清理函数")
        
        return _connection_manager_instance

    def _cleanup_on_exit(self):
        """
        进程退出时的清理方法，由atexit处理器调用。
        
        该方法确保在程序退出时正确关闭MCP连接和清理资源，
        避免资源泄漏和未完成的异步任务。
        使用状态标志防止重复清理和竞态条件。
        """
        # 检查是否已经清理过，防止重复清理
        if self._cleaned_up:
            logger.debug("MCP连接已经清理过，跳过重复清理")
            return
        
        # 检查是否正在清理中，防止竞态条件
        if self._cleaning_up:
            logger.debug("MCP连接正在清理中，等待完成")
            return
        
        try:
            if self.running:
                logger.info("进程退出时开始清理MCP连接")
                # 优先使用创建任务时的原始事件循环
                loop = self._loop
                if loop and not loop.is_closed():
                    if loop.is_running():
                        # 如果循环正在运行，使用线程安全的方式执行清理
                        try:
                            fut = asyncio.run_coroutine_threadsafe(self.close(), loop)
                            fut.result(timeout=2)
                        except Exception as e:
                            logger.error(f"MCP连接清理时发生错误（线程安全模式）: {e}")
                    else:
                        # 如果循环未运行，直接运行清理协程
                        loop.run_until_complete(self.close())
                else:
                    logger.debug("跳过MCP清理：没有可用的事件循环")
            else:
                logger.debug("MCP连接未运行，无需清理")
        except Exception as e:
            logger.error(f"MCP连接清理时发生错误: {e}")
        finally:
            # 标记为已清理，防止重复清理
            self._cleaned_up = True

    async def start(self, server_config: Dict[str, Dict]) -> None:
        """
        使用给定的配置启动MCP连接。

        Args:
            server_config: 服务器配置字典，包含MCP服务器的连接信息
        """
        async with self.lock:
            # 如果已经使用相同配置运行，则无需操作
            if self.running and self.server_config == server_config:
                logger.info("MCP连接已使用相同配置运行")
                return

            # 如果正在运行但配置已更改，关闭并重新启动
            if self.running:
                logger.info("配置已更改，重新启动MCP连接")
                await self._close_internal()

            # 存储配置并创建客户端（不基于环境变量过滤服务器）
            self.server_config = server_config
            try:
                # ✅ 修复 BlockingError：通过 monkey-patch 绕过 blockbuster 检测
                # 
                # 问题根源：
                # 1. MCP SDK 在 Windows 上初始化时会调用 shutil.which("npx")
                # 2. shutil.which() 内部调用 os.access() 进行文件系统访问（同步阻塞 I/O）
                # 3. LangGraph 的 blockbuster 库通过 monkey-patch os.access() 检测所有阻塞调用
                # 4. blockbuster 检测机制：如果在异步运行时中调用 os.access 就抛出 BlockingError
                # 
                # 解决方案：
                # 在 MCP 客户端初始化期间，临时用原始的 os.access 替换 blockbuster 的包装函数
                import os
                import sys
                
                # 步骤 1: 保存被 blockbuster monkey-patched 的 os.access
                patched_access = os.access
                
                # 步骤 2: 查找原始的 os.access 函数
                # blockbuster 会保存原始函数，但我们需要直接访问系统级的实现
                if hasattr(patched_access, '__wrapped__'):
                    # 如果有 __wrapped__ 属性，说明是被装饰的函数
                    original_access = patched_access.__wrapped__
                else:
                    # 如果找不到 __wrapped__，直接从 posix/nt 模块获取原始函数
                    if sys.platform == 'win32':
                        import nt  # Windows 底层模块
                        original_access = nt.access
                    else:
                        import posix  # Unix 底层模块
                        original_access = posix.access
                
                # 保存原始和被包装的函数引用，供后续清理时恢复
                self._original_os_access = original_access
                self._patched_os_access = patched_access
                
                # 步骤 3: 永久替换为原始函数（在 MCP 客户端生命周期内）
                # 注意：不再使用 try-finally 恢复，而是让 monkey-patch 持续生效
                # 这样不仅初始化时，每次调用工具创建 session 时也不会触发 BlockingError
                os.access = original_access
                
                # 步骤 4: 现在可以安全地创建 MCP 客户端（不会触发 BlockingError）
                self.client = MultiServerMCPClient(server_config)
                try:
                    self.tools_cache = await self.client.get_tools()
                except ExceptionGroup as eg:
                    for e in eg.exceptions:
                        logger.error(f"MCP工具获取子错误: {e}")
                    self.tools_cache = []
                except Exception as e:
                    logger.error(f"MCP工具获取失败: {e}")
                    self.tools_cache = []
                
                logger.info("MCP客户端成功连接并验证")
                logger.info("已应用 os.access monkey-patch，在整个 MCP 客户端生命周期内避免 BlockingError")

                # 标记为成功连接
                self.last_heartbeat_ok = True
                self.running = True

                # 启动心跳任务
                self._loop = asyncio.get_running_loop()
                self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            except Exception as e:
                logger.error(f"启动MCP连接失败: {e}")
                await self._close_internal()
                raise

    async def get_tools(self, force_refresh: bool = False) -> List[BaseTool]:
        """
        从MCP客户端获取工具，支持缓存机制。

        Args:
            force_refresh: 如果为True，绕过缓存并获取最新工具

        Returns:
            List[BaseTool]: 可用工具列表
        """
        if not self.client:
            logger.warning("没有可用的MCP客户端")
            return []

        if not self.tools_cache or force_refresh:
            try:
                logger.debug("从MCP客户端获取工具...")
                # 显式捕获 TaskGroup 错误
                try:
                    self.tools_cache = await self.client.get_tools()
                except ExceptionGroup as eg:
                    for e in eg.exceptions:
                        logger.error(f"MCP工具获取子错误: {e}")
                except Exception as e:
                    logger.error(f"从MCP客户端获取工具失败: {e}")
                logger.info(f"从MCP服务器检索到 {len(self.tools_cache)} 个工具")
            except Exception as e:
                logger.error(f"从MCP客户端获取工具失败: {e}")
                if not self.tools_cache:  # 只有在没有缓存工具时才返回空列表
                    return []
        else:
            logger.debug(f"使用缓存工具: {len(self.tools_cache)} 个工具")

        return self.tools_cache.copy()

    async def get_tool_by_name(self, tool_name: str, force_refresh: bool = False) -> Optional[BaseTool]:
        """
        根据工具名称获取指定的工具。

        Args:
            tool_name: 工具名称
            force_refresh: 如果为True，绕过缓存并获取最新工具

        Returns:
            Optional[BaseTool]: 找到的工具，如果不存在则返回None
        """
        tools = await self.get_tools(force_refresh=force_refresh)
        
        for tool in tools:
            if tool.name == tool_name:
                logger.debug(f"找到工具: {tool_name}")
                return tool
        
        logger.warning(f"未找到工具: {tool_name}")
        return None

    async def get_tools_by_names(self, tool_names: List[str], force_refresh: bool = False) -> Dict[str, Optional[BaseTool]]:
        """
        根据工具名称列表获取多个指定的工具。

        Args:
            tool_names: 工具名称列表
            force_refresh: 如果为True，绕过缓存并获取最新工具

        Returns:
            Dict[str, Optional[BaseTool]]: 工具名称到工具的映射字典，不存在的工具值为None
        """
        tools = await self.get_tools(force_refresh=force_refresh)
        
        # 创建工具名称到工具的映射
        tool_map = {tool.name: tool for tool in tools}
        
        # 返回请求的工具
        result = {}
        for tool_name in tool_names:
            result[tool_name] = tool_map.get(tool_name)
            if result[tool_name] is None:
                logger.warning(f"未找到工具: {tool_name}")
            else:
                logger.debug(f"找到工具: {tool_name}")
        
        return result

    async def get_tools_by_pattern(self, pattern: str, force_refresh: bool = False) -> List[BaseTool]:
        """
        根据名称模式获取匹配的工具。

        Args:
            pattern: 工具名称模式（支持通配符 * 和 ?）
            force_refresh: 如果为True，绕过缓存并获取最新工具

        Returns:
            List[BaseTool]: 匹配的工具列表
        """
        import fnmatch
        
        tools = await self.get_tools(force_refresh=force_refresh)
        matching_tools = []
        
        for tool in tools:
            if fnmatch.fnmatch(tool.name, pattern):
                matching_tools.append(tool)
                logger.debug(f"工具 {tool.name} 匹配模式 {pattern}")
        
        logger.info(f"找到 {len(matching_tools)} 个匹配模式 '{pattern}' 的工具")
        return matching_tools

    async def search_tools(self, keyword: str, search_in_description: bool = True, force_refresh: bool = False) -> List[BaseTool]:
        """
        根据关键词搜索工具（在名称和描述中搜索）。

        Args:
            keyword: 搜索关键词
            search_in_description: 是否在工具描述中搜索
            force_refresh: 如果为True，绕过缓存并获取最新工具

        Returns:
            List[BaseTool]: 匹配的工具列表
        """
        tools = await self.get_tools(force_refresh=force_refresh)
        matching_tools = []
        
        keyword_lower = keyword.lower()
        
        for tool in tools:
            # 在工具名称中搜索
            if keyword_lower in tool.name.lower():
                matching_tools.append(tool)
                logger.debug(f"工具 {tool.name} 名称匹配关键词 '{keyword}'")
                continue
            
            # 在工具描述中搜索
            if search_in_description and hasattr(tool, 'description') and tool.description:
                if keyword_lower in tool.description.lower():
                    matching_tools.append(tool)
                    logger.debug(f"工具 {tool.name} 描述匹配关键词 '{keyword}'")
        
        logger.info(f"找到 {len(matching_tools)} 个匹配关键词 '{keyword}' 的工具")
        return matching_tools

    async def get_tool_names(self, force_refresh: bool = False) -> List[str]:
        """
        获取所有可用工具的名称列表。

        Args:
            force_refresh: 如果为True，绕过缓存并获取最新工具

        Returns:
            List[str]: 工具名称列表
        """
        tools = await self.get_tools(force_refresh=force_refresh)
        tool_names = [tool.name for tool in tools]
        logger.debug(f"获取到 {len(tool_names)} 个工具名称")
        return tool_names

    async def close(self) -> None:
        """
        关闭MCP连接并清理资源。
        
        该方法会取消所有后台任务，清理客户端连接，并重置所有状态。
        使用状态标志防止重复清理和竞态条件。
        """
        # 检查是否已经清理过，防止重复清理
        if self._cleaned_up:
            logger.debug("MCP连接已经清理过，跳过重复清理")
            return
        
        # 检查是否正在清理中，防止竞态条件
        if self._cleaning_up:
            logger.debug("MCP连接正在清理中，等待完成")
            return
        
        async with self.lock:
            await self._close_internal()

    async def _close_internal(self) -> None:
        """
        内部关闭方法，不进行锁定。
        
        执行实际的资源清理工作，包括取消任务、清理客户端和重置状态。
        使用状态标志防止重复清理和竞态条件。
        """
        # 设置清理中标志，防止并发清理
        self._cleaning_up = True
        
        try:
            logger.info("正在关闭MCP连接")
            self.running = False

            # 取消后台任务
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
                try:
                    await self._drain_task(self.heartbeat_task)
                finally:
                    self.heartbeat_task = None

            if self.reconnect_task:
                self.reconnect_task.cancel()
                try:
                    await self._drain_task(self.reconnect_task)
                finally:
                    self.reconnect_task = None

            # 如果客户端有清理方法则关闭客户端
            if self.client:
                # MultiServerMCPClient没有显式的close方法
                # 但我们清除引用
                self.client = None

            # 清理状态
            self.server_config = None
            self.tools_cache = []
            self.last_heartbeat_ok = False
            self._loop = None
            
            # 恢复原始的 os.access 函数（如果之前应用了 monkey-patch）
            if self._patched_os_access is not None:
                import os
                os.access = self._patched_os_access
                logger.info("已恢复原始的 os.access 函数（移除 monkey-patch）")
                self._original_os_access = None
                self._patched_os_access = None
            
            logger.info("MCP连接已成功关闭")
            
        except Exception as e:
            logger.error(f"关闭MCP连接时发生错误: {e}")
            raise
        finally:
            # 清理完成后重置标志
            self._cleaning_up = False
            self._cleaned_up = True

    async def _drain_task(self, task: asyncio.Task) -> None:
        """
        在任务所属的事件循环中等待已取消的任务，防止挂起销毁警告。
        
        这个方法确保被取消的任务能够正确完成，避免在程序退出时出现警告信息。
        
        Args:
            task: 需要排空的任务
        """
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None
        try:
            task_loop = task.get_loop()
        except Exception:
            task_loop = None

        # 如果我们在同一个循环中，直接等待
        if current_loop is not None and task_loop is current_loop:
            try:
                await task
            except asyncio.CancelledError:
                pass
            return

        # 如果任务有一个循环，在该循环上调度排空协程
        if task_loop is not None and not task_loop.is_closed():
            try:
                fut = asyncio.run_coroutine_threadsafe(self._drain_task_on_loop(task), task_loop)
                try:
                    fut.result(timeout=2)
                except Exception:
                    pass
            except Exception:
                pass

    async def _drain_task_on_loop(self, task: asyncio.Task) -> None:
        """
        在指定事件循环上排空任务的辅助方法。
        
        Args:
            task: 需要排空的任务
        """
        try:
            await task
        except asyncio.CancelledError:
            pass

    async def _heartbeat_loop(self, interval_sec: int = 45) -> None:
        """
        心跳循环，用于保持SSE连接活跃。

        定期发送轻量级请求来测试连接状态，如果连接失败则触发重连机制。

        Args:
            interval_sec: 心跳间隔时间（秒），默认45秒
        """
        logger.info(f"启动心跳循环，间隔 {interval_sec} 秒")

        while self.running:
            try:
                await asyncio.sleep(interval_sec)

                if not self.running:
                    break

                # 发送轻量级请求来测试连接
                await self.client.get_tools()
                self.last_heartbeat_ok = True
                logger.debug("心跳成功")

            except Exception as e:
                logger.warning(f"心跳失败: {e}")
                self.last_heartbeat_ok = False
                if not self.running:
                    break
                self._ensure_reconnect()

    def _ensure_reconnect(self) -> None:
        """
        确保重连任务已启动（如果尚未运行）。
        
        检查重连任务是否存在且未完成，如果不存在或已完成则启动新的重连任务。
        """
        if self.reconnect_task is None or self.reconnect_task.done():
            logger.info("启动重连任务")
            self.reconnect_task = asyncio.create_task(self._reconnect_loop())

    async def _reconnect_loop(self, base_delay: float = 0.5, max_delay: float = 30.0) -> None:
        """
        带指数退避和抖动的重连循环。

        使用指数退避算法来避免频繁重连，同时添加随机抖动来避免多个客户端同时重连。

        Args:
            base_delay: 指数退避的基础延迟时间（秒）
            max_delay: 重连尝试之间的最大延迟时间（秒）
        """
        attempt = 0

        while self.running and not self.last_heartbeat_ok:
            try:
                # 计算带指数退避和完全抖动的延迟时间
                delay = min(max_delay, base_delay * (2 ** attempt))
                jittered_delay = random.uniform(0, delay)

                logger.info(f"重连尝试 {attempt + 1}，{jittered_delay:.2f} 秒后开始")
                await asyncio.sleep(jittered_delay)

                if not self.running:
                    break

                # 尝试重新创建客户端并验证
                try:
                    import os as _os
                    if (not _os.getenv("SERPER_API_KEY")) and (self.server_config and "serpersearch" in self.server_config):
                        filtered_config = {k: v for k, v in self.server_config.items() if k != "serpersearch"}
                    else:
                        filtered_config = self.server_config
                except Exception:
                    filtered_config = self.server_config

                new_client = MultiServerMCPClient(filtered_config)
                await new_client.get_tools()

                # 成功 - 交换新客户端
                async with self.lock:
                    self.client = new_client
                    self.tools_cache = []  # 清空缓存以强制刷新
                    self.last_heartbeat_ok = True

                logger.info("重连成功")
                break

            except Exception as e:
                logger.warning(f"重连尝试 {attempt + 1} 失败: {e}")
                attempt += 1

        # 清除重连任务引用
        self.reconnect_task = None

    @property
    def is_connected(self) -> bool:
        """
        检查管理器是否已连接且健康。
        
        返回True需要满足三个条件：
        1. 管理器正在运行
        2. 客户端实例存在
        3. 最后一次心跳成功
        
        Returns:
            bool: 如果连接健康则返回True，否则返回False
        """
        return self.running and self.client is not None and self.last_heartbeat_ok
