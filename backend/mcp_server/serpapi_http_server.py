from typing import List, Dict, Any
import logging
import os

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


mcp = FastMCP("JoinAI SerpAPI", json_response=True)


@mcp.tool(name="search", description="使用 SerpAPI（Google 搜索 API）进行搜索")
def search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    api_key = os.getenv("SERPAPI_API_KEY", "")
    if not api_key:
        raise ValueError("SerpAPI 需要 API Key，请在 .env 中配置 SERPAPI_API_KEY")

    try:
        try:
            from serpapi import GoogleSearch
        except ImportError as e:
            raise ImportError("请安装 SerpAPI 依赖: pip install serpapi") from e

        params: Dict[str, Any] = {
            "q": query,
            "hl": os.getenv("SERPAPI_HL", "en"),
            "gl": os.getenv("SERPAPI_GL", "us"),
            "google_domain": os.getenv("SERPAPI_GOOGLE_DOMAIN", "google.com"),
            "api_key": api_key,
        }
        location = os.getenv("SERPAPI_LOCATION", "")
        if location:
            params["location"] = location

        search_client = GoogleSearch(params)
        data = search_client.get_dict()

        results: List[Dict[str, Any]] = []

        if data.get("knowledge_graph"):
            kg = data["knowledge_graph"]
            metadata = {
                k: v
                for k, v in kg.items()
                if k not in {"title", "website", "description"}
            }
            if not metadata:
                metadata = None
            results.append(
                {
                    "title": f"📋 {kg.get('title', '知识面板')}",
                    "url": kg.get("website", ""),
                    "abstract": kg.get("description", ""),
                    "rank": 0,
                    "engine": "serpapi",
                    "result_type": "knowledge_panel",
                    "metadata": metadata,
                }
            )

        organic = data.get("organic_results") or data.get("organic") or []
        for idx, item in enumerate(organic[:max_results], 1):
            metadata = {
                k: item.get(k)
                for k in ("position", "date", "source")
                if item.get(k) is not None
            }
            if not metadata:
                metadata = None
            results.append(
                {
                    "title": item.get("title", "无标题"),
                    "url": item.get("link", ""),
                    "abstract": item.get("snippet", ""),
                    "rank": idx,
                    "engine": "serpapi",
                    "result_type": "search_result",
                    "metadata": metadata,
                }
            )

        return results
    except Exception as e:
        logger.error(f"SerpAPI 搜索失败: {e}")
        return [
            {
                "title": "[错误]",
                "url": "",
                "abstract": f"SerpAPI 搜索失败: {e}",
                "rank": 0,
                "engine": "serpapi",
                "result_type": "error",
                "metadata": {
                    "suggestion": "请检查 SERPAPI_API_KEY 是否有效，或网络连接是否正常"
                },
            }
        ]


@mcp.tool(name="get_engine_info", description="获取 SerpAPI 引擎信息")
def get_engine_info() -> Dict[str, Any]:
    return {
        "name": "serpapi",
        "description": "SerpAPI 搜索引擎（本地 HTTP MCP）",
        "requires_auth": True,
        "status": "ready",
    }


app = mcp.streamable_http_app()


def main() -> None:
    import uvicorn

    port = int(os.getenv("JOINAI_SERPAPI_MCP_PORT", "7802"))
    uvicorn.run(app, host=os.getenv("JOINAI_MCP_HOST", "127.0.0.1"), port=port)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"启动失败: {e}")
        import sys

        sys.exit(1)

