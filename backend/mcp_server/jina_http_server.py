from typing import List, Dict, Any, Optional
import logging
import os
from urllib.parse import quote

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


mcp = FastMCP("JoinAI Jina", json_response=True)


def _auth_headers(api_key: str) -> Dict[str, str]:
    return {
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}",
    }


def _normalize_search_results(data: Any) -> List[Dict[str, Any]]:
    items: Optional[list] = None
    if isinstance(data, dict):
        for k in ("data", "results", "items"):
            v = data.get(k)
            if isinstance(v, list):
                items = v
                break
    elif isinstance(data, list):
        items = data

    if not items:
        return [
            {
                "title": "[错误]",
                "url": "",
                "abstract": "Jina 搜索未返回可解析结果",
                "rank": 0,
                "engine": "jina",
                "result_type": "error",
            }
        ]

    results: List[Dict[str, Any]] = []
    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            continue
        url = item.get("url") or item.get("link") or ""
        title = item.get("title") or item.get("name") or "无标题"
        abstract = (
            item.get("snippet")
            or item.get("description")
            or item.get("content")
            or item.get("summary")
            or ""
        )
        results.append(
            {
                "title": title,
                "url": url,
                "abstract": abstract,
                "rank": idx,
                "engine": "jina",
            }
        )
    return results


@mcp.tool(name="jina_search", description="使用 Jina Search 进行搜索")
def jina_search(query: str, count: int = 5) -> List[Dict[str, Any]]:
    api_key = os.getenv("JINA_API_KEY", "")
    if not api_key:
        raise ValueError("Jina 需要 API Key，请在 .env 中配置 JINA_API_KEY")

    try:
        endpoint = os.getenv("JINA_SEARCH_ENDPOINT", "https://s.jina.ai/")
        url = endpoint.rstrip("/") + "/" + quote(query, safe="")
        resp = requests.get(url, headers=_auth_headers(api_key), timeout=60)
        resp.raise_for_status()
        data = resp.json()
        results = _normalize_search_results(data)
        if count > 0:
            return results[:count]
        return results
    except Exception as e:
        logger.error(f"Jina 搜索失败: {e}")
        return [
            {
                "title": "[错误]",
                "url": "",
                "abstract": f"Jina 搜索失败: {e}",
                "rank": 0,
                "engine": "jina",
                "result_type": "error",
                "metadata": {
                    "suggestion": "请检查 JINA_API_KEY、网络连接或重试查询"
                },
            }
        ]


@mcp.tool(name="jina_reader", description="使用 Jina Reader 读取网页内容")
def jina_reader(url: str, timeout_sec: int = 60) -> Dict[str, Any]:
    api_key = os.getenv("JINA_API_KEY", "")
    if not api_key:
        raise ValueError("Jina 需要 API Key，请在 .env 中配置 JINA_API_KEY")

    try:
        endpoint = os.getenv("JINA_READER_ENDPOINT", "https://r.jina.ai/")
        reader_url = endpoint.rstrip("/") + "/" + url
        resp = requests.get(reader_url, headers=_auth_headers(api_key), timeout=max(5, timeout_sec))
        resp.raise_for_status()
        data = resp.json()
        return {
            "url": url,
            "data": data,
        }
    except Exception as e:
        logger.error(f"Jina Reader 失败: {e}")
        return {
            "url": url,
            "error": str(e),
            "suggestion": "请检查 JINA_API_KEY、URL 是否可访问或稍后重试",
        }


@mcp.tool(name="get_engine_info", description="获取 Jina 引擎信息")
def get_engine_info() -> Dict[str, Any]:
    return {
        "name": "jina",
        "description": "Jina Search + Reader（本地 HTTP MCP）",
        "requires_auth": True,
        "status": "ready",
    }


app = mcp.streamable_http_app()


def main() -> None:
    import uvicorn

    port = int(os.getenv("JOINAI_JINA_MCP_PORT", "7803"))
    uvicorn.run(app, host=os.getenv("JOINAI_MCP_HOST", "127.0.0.1"), port=port)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"启动失败: {e}")
        import sys

        sys.exit(1)

