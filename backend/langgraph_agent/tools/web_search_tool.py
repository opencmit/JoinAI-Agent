import asyncio
from copilotkit.langchain import copilotkit_emit_state
from datetime import datetime
from dotenv import load_dotenv
import json
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated
from urllib.parse import unquote
from langgraph_agent.utils.message_utils import get_last_show_message_id

# 导入新的搜索提供商抽象层
from langgraph_agent.tools.providers.base_search_provider import SearchQuery
from langgraph_agent.tools.providers.search_provider_factory import SearchProviderFactory
from langgraph_agent.tools.providers.search_config import SearchConfig

load_dotenv('.env')

# 全局提供商实例池
_provider_pool = {}

def initialize_all_providers():
    """初始化所有已注册的搜索提供商"""
    global _provider_pool
    if not _provider_pool:
        for provider_name in SearchProviderFactory.get_available_providers():
            try:
                provider_config = SearchConfig.get_provider_config(provider_name)
                provider = SearchProviderFactory.create_provider(provider_name, provider_config)
                _provider_pool[provider_name] = provider
                print(f"[OK] 初始化搜索提供商: {provider_name}")
            except Exception as e:
                print(f"[FAIL] 初始化搜索提供商 {provider_name} 失败: {e}")
    return _provider_pool

def get_enabled_providers(config: RunnableConfig) -> List[str]:
    """
    从配置中获取要启用的提供商列表
    
    Args:
        config: 运行时配置
        
    Returns:
        要启用的提供商名称列表
    """
    # 从config中获取providers配置
    providers = config.get("configurable", {}).get("providers")
    
    if providers:
        # 如果config中有providers配置，使用它
        if isinstance(providers, str):
            # 如果是字符串，按逗号分割
            return [p.strip() for p in providers.split(",") if p.strip()]
        elif isinstance(providers, list):
            # 如果是列表，直接使用
            return [p for p in providers if p]
    
    # 如果config中没有配置，从环境变量获取默认提供商
    default_provider = SearchConfig.get_current_provider()
    return [default_provider]

def get_provider_instances(provider_names: List[str]) -> List:
    """
    根据提供商名称列表获取提供商实例
    
    Args:
        provider_names: 提供商名称列表
        
    Returns:
        提供商实例列表
    """
    # 确保所有提供商已初始化
    initialize_all_providers()
    
    providers = []
    for name in provider_names:
        if name in _provider_pool:
            providers.append(_provider_pool[name])
        else:
            print(f"⚠️ 警告: 未找到提供商 {name}，跳过")
    
    if not providers:
        # 如果没有有效的提供商，使用默认的
        default_name = SearchConfig.get_current_provider()
        if default_name in _provider_pool:
            providers = [_provider_pool[default_name]]
        else:
            raise ValueError(f"无法找到任何有效的搜索提供商")
    
    return providers

# 为了保持向后兼容，保留原有的TavilyQuery模型
class TavilyQuery(BaseModel):
    """单个Tavily搜索查询的模型（保持向后兼容）"""
    query: str = Field(description="网络搜索查询")
    topic: str = Field(
        description="搜索类型，必须是'general'或'news'。仅当搜索的公司是上市公司且可能出现在热门新闻中时才选择'news'"
    )
    days: int = Field(default=3, description="'news'搜索时向前查找的天数")
    domains: Optional[List[str]] = Field(
        default=None,
        description="要包含在搜索中的域名列表，用于从可信和相关的域名获取信息"
    )

class WebToolInput(BaseModel):
    """统一的Web工具输入模型"""
    operation: str = Field(description="Web操作类型，可选值: search, scrape")
    sub_queries: Optional[List[TavilyQuery]] = Field(None, description="搜索查询列表，适用于search操作")
    urls: Optional[List[str]] = Field(None, description="要提取内容的URL列表，适用于scrape操作")
    state: Annotated[Optional[Dict], InjectedToolArg] = Field(description="状态，由系统提供")
    special_config_param: Annotated[RunnableConfig, InjectedToolArg] = Field(description="特殊配置参数，由系统提供")

class WebTool:
    """统一的Web操作工具类（支持多提供商并发）"""
    
    @staticmethod
    async def _add_log(state: Dict, message: str, config: RunnableConfig) -> int:
        """添加日志并返回日志索引"""
        state["logs"] = state.get("logs", [])
        log_index = len(state["logs"])
        state["logs"].append({
            "message": message,
            "done": False,
            "messageId":  get_last_show_message_id(state["messages"])
        })
        await copilotkit_emit_state(config, state)
        return log_index
    
    @staticmethod
    async def _complete_log(state: Dict, log_index: int, config: RunnableConfig):
        """完成日志"""
        state["logs"][log_index]["done"] = True
        await copilotkit_emit_state(config, state)

    @staticmethod
    async def search(sub_queries: List[TavilyQuery], state: Dict, config: RunnableConfig) -> tuple[Dict, str]:
        """使用配置的搜索提供商列表并发执行每个子查询的搜索"""
        # 获取要启用的提供商列表
        enabled_provider_names = get_enabled_providers(config)
        search_providers = get_provider_instances(enabled_provider_names)
        
        print(f"启用的搜索提供商: {[p.provider_name for p in search_providers]}")
        print("special config param tool call id in web search tool", config["configurable"].get("tool_call_id"))
        
        logs_start_index = len(state.get("logs", []))
        sub_queries = sub_queries[:3]  # 限制sub_queries最多3个

        async def perform_search_with_provider(provider, query: TavilyQuery, provider_index: int, query_index: int):
            """使用特定提供商执行单个搜索的协程函数"""
            try:
                # 转换为标准化的SearchQuery格式
                search_query = SearchQuery(
                    query=query.query,
                    topic=query.topic,
                    days=query.days,
                    max_results=3,
                    domains=query.domains
                )
                
                # 使用搜索提供商执行搜索
                search_results = await provider.search(search_query)
                
                # 转换回原有格式以保持兼容性
                results = []
                for result in search_results:
                    results.append({
                        'url': result.url,
                        'title': result.title,
                        'content': result.content,
                        'score': result.score,
                        'provider': provider.provider_name  # 添加提供商标识
                    })
                
                return results
                
            except Exception as e:
                print(f"提供商 {provider.provider_name} 搜索查询'{query.query}'时发生错误: {str(e)}")
                return []

        # 记录搜索查询
        provider_names = [p.provider_name for p in search_providers]
        for query in sub_queries:
            if "logs" not in state:
                state["logs"] = []
            state["logs"].append({
                "message": f"🌐 正在搜索网络: '{query.query}' (使用提供商: {', '.join(provider_names)})",
                "done": False,
                "messageId":  get_last_show_message_id(state["messages"])
            })

        # 创建所有搜索任务（提供商 × 查询的笛卡尔积）
        search_tasks = []
        task_info = []  # 用于跟踪任务信息
        
        for query_idx, query in enumerate(sub_queries):
            for provider_idx, provider in enumerate(search_providers):
                task = perform_search_with_provider(provider, query, provider_idx, query_idx)
                search_tasks.append(task)
                task_info.append({
                    'query_idx': query_idx,
                    'provider_idx': provider_idx,
                    'provider_name': provider.provider_name,
                    'query': query.query
                })

        # 并行执行所有搜索任务
        search_responses = await asyncio.gather(*search_tasks)

        # 合并所有响应的结果
        tool_msg = "搜索发现以下新文档:\n"
        sources = {}
        search_is_empty = True

        # 按查询分组处理结果
        for response_idx, response in enumerate(search_responses):
            task_info_item = task_info[response_idx]
            query_idx = task_info_item['query_idx']
            provider_name = task_info_item['provider_name']
            
            for source in response:
                url = source.get('url', '无URL')
                title = source.get('title', '无标题')
                content_snippet = source.get('content', '无内容')[:300]
                provider = source.get('provider', provider_name)

                # 使用URL作为唯一键，但在标题中标注提供商
                unique_key = f"{url}#{provider}"
                if unique_key not in sources:
                    sources[unique_key] = {
                        "url": url,
                        "title": f"{title}",
                        "content": content_snippet,
                        "provider": provider,
                        "score": source.get('score', 0.0)
                    }
                    tool_msg += f"- [{title}]({url}): 简介: {content_snippet}...\n"
                    search_is_empty = False

        # 更新日志状态
        for i in range(len(sub_queries)):
            if logs_start_index + i < len(state["logs"]):
                state["logs"][logs_start_index + i]["done"] = True
        await copilotkit_emit_state(config, state)

        # 确保所有源都有标题
        for key, val in sources.items():
            if not sources[key].get('title', None):
                sources[key]['title'] = '无标题，无效链接'

        # 保存结构化结果
        if toolcall_id := config["configurable"].get("tool_call_id"):
            state['structure_tool_results'][toolcall_id] = sources
        
        if search_is_empty:
            tool_msg = "搜索未发现新文档。"
        await copilotkit_emit_state(config, state)

        return state, tool_msg

    @staticmethod
    async def scrape(urls: List[str], state: Dict, config: RunnableConfig) -> tuple[Dict, str]:
        """从提供的URL列表中提取完整内容（只使用第一个启用的提供商）"""
        # 获取要启用的提供商列表，但只使用第一个
        enabled_provider_names = get_enabled_providers(config)
        search_providers = get_provider_instances(enabled_provider_names)
        
        # scrape操作只使用第一个提供商
        search_provider = search_providers[0]
        
        print(f"内容提取使用提供商: {search_provider.provider_name}")
        
        log_index = await WebTool._add_log(state, f"🚀 从有价值的来源中提取额外内容 (使用{search_provider.provider_name})", config)
        sources = {}
        try:
            # 使用搜索提供商提取内容
            extracted_content = await search_provider.extract_content(urls)

            tool_msg = "从以下来源提取了额外信息:\n"
            for item in extracted_content:
                url = item['url']
                content = item['content']
                title = item['title']
                
                sources[url] = {
                    'content': content, 
                    'title': f"{title}", 
                    'url': url,
                    'provider': search_provider.provider_name
                }
                tool_msg += f"- [{title}]({url}): {content}...\n"

            # 添加结构化结果
            if toolcall_id := config["configurable"].get("tool_call_id"):
                state['structure_tool_results'][toolcall_id] = sources

            return state, tool_msg

        except Exception as e:
            print(f"提取内容时发生错误: {str(e)}")
            return state, f"提取内容时发生错误: {str(e)}"
        finally:
            await WebTool._complete_log(state, log_index, config)

    @staticmethod
    @tool("web", args_schema=WebToolInput)
    async def web_tool(
        operation: str,
        special_config_param: RunnableConfig,
        sub_queries: Optional[List[TavilyQuery]] = None,
        urls: Optional[List[str]] = None,
        state: Optional[Dict] = None,
        
    ) -> tuple[Dict, str]:
        """
        统一的Web操作工具，支持以下操作：
        - search: 使用配置的搜索提供商列表执行网络搜索
        - scrape: 从指定URL提取网页内容
        """
        print("special config param tool call id in web tool", special_config_param["configurable"].get("tool_call_id"))
        print("配置的提供商:", special_config_param.get("configurable", {}).get("providers"))
        
        config = special_config_param or RunnableConfig()
        
        if operation == "search":
            if not sub_queries:
                return state, "搜索操作需要提供sub_queries参数"
            return await WebTool.search(sub_queries, state, config)
        
        elif operation == "scrape":
            if not urls:
                return state, "内容提取操作需要提供urls参数"
            return await WebTool.scrape(urls, state, config)
        
        else:
            return state, f"不支持的Web操作: {operation}"

# 创建全局工具实例（保持向后兼容）
web_tool = WebTool.web_tool

# 初始化所有提供商
initialize_all_providers()

# 提供商管理函数
def get_available_providers() -> List[str]:
    """获取所有可用的提供商名称"""
    return list(_provider_pool.keys())

def get_provider_info(provider_name: str = None) -> Dict:
    """
    获取提供商信息
    
    Args:
        provider_name: 提供商名称，如果为None则返回所有提供商信息
        
    Returns:
        提供商信息字典
    """
    if provider_name:
        if provider_name in _provider_pool:
            provider = _provider_pool[provider_name]
            return {
                "name": provider.provider_name,
                "config": provider.config,
                "available": True
            }
        else:
            return {
                "name": provider_name,
                "available": False,
                "error": "提供商未初始化"
            }
    else:
        # 返回所有提供商信息
        info = {}
        for name, provider in _provider_pool.items():
            info[name] = {
                "name": provider.provider_name,
                "config": provider.config,
                "available": True
            }
        return info

async def test_tools_invoke():
    """使用工具调用API测试工具函数"""
    print("开始测试Web工具的工具调用API...")
    import traceback
    
    # 创建一个初始状态
    state = {
        "logs": [],
        "sources": {},
        "structure_tool_results": {}
    }
    
    try:
        print(f"可用提供商: {get_available_providers()}")
        
        # 测试1: 使用单个提供商
        print("\n1. 测试单个提供商搜索:")
        config1 = RunnableConfig(configurable={
            "tool_call_id": "test_001",
            "providers": "tavily"
        })
        
        search_result = await web_tool.ainvoke({
            "operation": "search",
            "sub_queries": [
                TavilyQuery(
                    query="Python 3.11新特性",
                    topic="general",
                    days=3
                )
            ],
            "special_config_param": {},
            "state": state}, config=config1)
        print(f"结果: 找到 {len(search_result[0].get('structure_tool_results', {}).get('test_001', {}))} 个结果")
        
        # 测试2: 使用多个提供商（如果可用）
        print("\n2. 测试多提供商搜索:")
        config2 = RunnableConfig(configurable={
            "tool_call_id": "test_002", 
            "providers": ["tavily"]  # 如果有其他提供商可以添加
        })
        
        search_result2 = await web_tool.ainvoke({
            "operation": "search",
            "sub_queries": [
                TavilyQuery(
                    query="FastAPI异步编程",
                    topic="general"
                )
            ],
            "special_config_param": {},
            "state": state}, config=config2)
        print(f"结果: 找到 {len(search_result2[0].get('structure_tool_results', {}).get('test_002', {}))} 个结果")
        
        # 测试3: 内容提取
        print("\n3. 测试内容提取:")
        config3 = RunnableConfig(configurable={
            "tool_call_id": "test_003",
            "providers": "tavily"
        })
        
        scrape_result = await web_tool.ainvoke({
            "operation": "scrape",
            "urls": ["https://python.org"],
            "special_config_param": {},
            "state": state}, config=config3)
        print(f"结果: 提取了 {len(scrape_result[0].get('structure_tool_results', {}).get('test_003', {}))} 个URL的内容")
        
        # 测试4: 不指定提供商（使用默认）
        print("\n4. 测试默认提供商:")
        config4 = RunnableConfig(configurable={"tool_call_id": "test_004"})
        
        search_result4 = await web_tool.ainvoke({
            "operation": "search",
            "sub_queries": [
                TavilyQuery(
                    query="机器学习最新进展",
                    topic="general"
                )
            ],
            "special_config_param": {},
            "state": state}, config=config4)
        print(f"结果: 找到 {len(search_result4[0].get('structure_tool_results', {}).get('test_004', {}))} 个结果")
        
        print("\n所有工具调用API测试完成!")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        traceback.print_exc()
        
    # 打印最终状态
    print("\n最终状态:")
    if state.get("logs"):
        for i, log in enumerate(state["logs"]):
            print(f"Log {i+1}: {log['message']} - 完成状态: {log['done']}")
    else:
        print("没有日志记录")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tools_invoke())

