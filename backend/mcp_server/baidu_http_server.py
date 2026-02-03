from typing import List, Dict, Any
import logging
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


mcp = FastMCP("JoinAI Baidu", json_response=True)


@mcp.tool(name="baidu_search", description="使用百度搜索引擎进行搜索")
def baidu_search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    使用百度搜索引擎进行搜索
    
    百度是中国最大的搜索引擎，特别擅长中文内容搜索。
    不需要 API Key，免费使用。
    
    参数:
        query: 搜索查询关键词（支持中英文）
        max_results: 最大返回结果数量，默认10
    
    返回:
        搜索结果列表
    """
    try:
        try:
            from baidusearch.baidusearch import search as baidu_search
        except ImportError as e:
            raise ImportError("请安装百度搜索依赖: pip install baidusearch") from e

        # 执行搜索
        search_results = baidu_search(
            keyword=query,
            num_results=max_results,
            debug=0
        )

        results: List[Dict[str, Any]] = []
        
        if search_results:
            for result in search_results:
                results.append(
                    {
                        "title": result.get("title", "无标题"),
                        "url": result.get("url", ""),
                        "abstract": result.get("abstract", ""),
                        "rank": result.get("rank", len(results) + 1),
                        "engine": "baidu",
                        "result_type": "search_result",
                    }
                )

        if not results:
            return [
                {
                    "title": "[空结果]",
                    "url": "",
                    "abstract": "百度搜索未返回可解析结果",
                    "rank": 0,
                    "engine": "baidu",
                    "result_type": "empty",
                }
            ]

        return results

    except Exception as e:
        logger.error(f"百度搜索失败: {e}")
        return [
            {
                "title": "[错误]",
                "url": "",
                "abstract": f"百度搜索失败: {e}",
                "rank": 0,
                "engine": "baidu",
                "result_type": "error",
                "metadata": {
                    "suggestion": "请检查网络连接或稍后重试"
                },
            }
        ]


@mcp.tool(name="get_engine_info", description="获取百度搜索引擎信息")
def get_engine_info() -> Dict[str, Any]:
    return {
        "name": "baidu",
        "description": "百度搜索引擎（本地 HTTP MCP）- 中国最大的搜索引擎，无需 API Key",
        "requires_auth": False,
        "status": "ready",
    }


app = mcp.streamable_http_app()


def main() -> None:
    import uvicorn

    port = int(os.getenv("JOINAI_BAIDU_MCP_PORT", "7805"))
    uvicorn.run(app, host=os.getenv("JOINAI_MCP_HOST", "127.0.0.1"), port=port)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"启动失败: {e}")
        import sys

        sys.exit(1)
