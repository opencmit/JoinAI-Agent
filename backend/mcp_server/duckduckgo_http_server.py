from typing import List, Dict, Any
import logging
import os
import warnings

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 忽略 duckduckgo_search 的重命名警告
warnings.filterwarnings('ignore', message='.*has been renamed to.*')


mcp = FastMCP("JoinAI DuckDuckGo", json_response=True)


@mcp.tool(name="duckduckgo_search", description="使用 DuckDuckGo 搜索引擎进行搜索")
def duckduckgo_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    使用 DuckDuckGo 搜索引擎进行搜索
    
    DuckDuckGo 是一个注重隐私保护的搜索引擎，不追踪用户行为。
    不需要 API Key，免费使用。
    
    特色功能:
        - 🔒 隐私保护，不追踪用户
        - 🌍 全球搜索，支持多语言
        - 🆓 完全免费，无需 API Key
    
    参数:
        query: 搜索查询关键词（支持多语言）
        max_results: 最大返回结果数量，默认10
    
    返回:
        搜索结果列表
    
    注意:
        在国内网络环境下可能不稳定，建议配合良好的网络连接使用
    """
    try:
        try:
            from duckduckgo_search import DDGS
        except ImportError as e:
            raise ImportError("请安装 DuckDuckGo 搜索依赖: pip install duckduckgo-search") from e

        # 初始化 DuckDuckGo 搜索客户端
        ddgs = DDGS()
        
        # 执行搜索
        search_results = ddgs.text(
            keywords=query,
            region='wt-wt',
            safesearch='moderate',
            timelimit=None,
            max_results=max_results
        )
        
        results: List[Dict[str, Any]] = []
        
        # 将生成器转换为列表
        search_results_list = list(search_results)
        
        if search_results_list:
            for idx, result in enumerate(search_results_list, 1):
                results.append(
                    {
                        "title": result.get("title", "无标题"),
                        "url": result.get("href", ""),
                        "abstract": result.get("body", ""),
                        "rank": idx,
                        "engine": "duckduckgo",
                        "result_type": "search_result",
                    }
                )

        if not results:
            return [
                {
                    "title": "[空结果]",
                    "url": "",
                    "abstract": f"未找到 '{query}' 的搜索结果（可能是网络问题或搜索词被过滤）",
                    "rank": 0,
                    "engine": "duckduckgo",
                    "result_type": "empty",
                    "metadata": {
                        "suggestion": "请尝试使用其他搜索引擎或修改搜索关键词"
                    },
                }
            ]

        return results

    except Exception as e:
        logger.error(f"DuckDuckGo 搜索失败: {e}")
        return [
            {
                "title": "[错误]",
                "url": "",
                "abstract": f"DuckDuckGo 搜索失败: {e}",
                "rank": 0,
                "engine": "duckduckgo",
                "result_type": "error",
                "metadata": {
                    "suggestion": "请检查网络连接或尝试使用其他搜索引擎"
                },
            }
        ]


@mcp.tool(name="get_engine_info", description="获取 DuckDuckGo 搜索引擎信息")
def get_engine_info() -> Dict[str, Any]:
    return {
        "name": "duckduckgo",
        "description": "DuckDuckGo 搜索引擎（本地 HTTP MCP）- 注重隐私的搜索引擎，无需 API Key",
        "requires_auth": False,
        "status": "ready",
    }


app = mcp.streamable_http_app()


def main() -> None:
    import uvicorn

    port = int(os.getenv("JOINAI_DUCKDUCKGO_MCP_PORT", "7806"))
    uvicorn.run(app, host=os.getenv("JOINAI_MCP_HOST", "127.0.0.1"), port=port)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"启动失败: {e}")
        import sys

        sys.exit(1)
