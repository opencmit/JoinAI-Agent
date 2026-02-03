from typing import List, Dict, Any
import logging
import os

import requests
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP


load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


mcp = FastMCP("JoinAI Serper", json_response=True)


@mcp.tool(name="serper_search", description="使用 Serper（Google 搜索 API）进行搜索")
def search(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    api_key = os.getenv("SERPER_API_KEY", "")
    if not api_key:
        raise ValueError("Serper 需要 API Key，请在 .env 中配置 SERPER_API_KEY")

    try:
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "hl": os.getenv("SERPER_HL", "en"),
            "gl": os.getenv("SERPER_GL", "us"),
            "num": max_results,
        }
        resp = requests.post(
            "https://google.serper.dev/search",
            json=payload,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        results: List[Dict[str, Any]] = []
        rank_counter = 1

        kg = data.get("knowledgeGraph")
        if kg:
            results.append(
                {
                    "title": f"📋 {kg.get('title', '知识面板')}",
                    "url": kg.get("website", ""),
                    "abstract": kg.get("description", ""),
                    "rank": rank_counter,
                    "engine": "serper",
                    "score": 1.0,
                }
            )
            rank_counter += 1

        answer_box = data.get("answerBox")
        if answer_box:
            answer_text = answer_box.get("answer") or answer_box.get("snippet") or ""
            results.append(
                {
                    "title": "🤖 直接答案",
                    "url": answer_box.get("link", ""),
                    "abstract": answer_text,
                    "rank": rank_counter,
                    "engine": "serper",
                    "score": 1.0,
                }
            )
            rank_counter += 1

        organic = data.get("organic") or data.get("organic_results") or []
        for item in organic[:max_results]:
            score = item.get("score", 0.0)
            if not isinstance(score, (int, float)):
                score = 0.0
            results.append(
                {
                    "title": item.get("title", "无标题"),
                    "url": item.get("link", ""),
                    "abstract": item.get("snippet", ""),
                    "rank": rank_counter,
                    "engine": "serper",
                    "score": score,
                }
            )
            rank_counter += 1

        return results
    except Exception as e:
        logger.error(f"Serper 搜索失败: {e}")
        return [
            {
                "title": "[错误]",
                "url": "",
                "abstract": f"Serper 搜索失败: {e}",
                "rank": 0,
                "engine": "serper",
                "result_type": "error",
                "metadata": {
                    "suggestion": "请检查 SERPER_API_KEY、网络连接或重试查询"
                },
            }
        ]


@mcp.tool(name="serper_scholar", description="使用 Serper Scholar（Google Scholar 搜索 API）进行学术搜索")
def serper_scholar(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    api_key = os.getenv("SERPER_API_KEY", "")
    if not api_key:
        raise ValueError("Serper 需要 API Key，请在 .env 中配置 SERPER_API_KEY")

    try:
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "q": query,
            "hl": os.getenv("SERPER_HL", "en"),
            "gl": os.getenv("SERPER_GL", "us"),
            "num": max_results,
        }
        resp = requests.post(
            "https://google.serper.dev/scholar",
            json=payload,
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        results: List[Dict[str, Any]] = []
        rank_counter = 1

        organic = data.get("organic") or data.get("organic_results") or []
        for item in organic[:max_results]:
            results.append(
                {
                    "title": item.get("title", "无标题"),
                    "url": item.get("link", ""),
                    "abstract": item.get("snippet", "") or item.get("description", ""),
                    "rank": rank_counter,
                    "engine": "serper_scholar",
                }
            )
            rank_counter += 1

        if results:
            return results

        return [
            {
                "title": "[空结果]",
                "url": "",
                "abstract": "Serper Scholar 未返回可解析结果",
                "rank": 0,
                "engine": "serper_scholar",
                "result_type": "empty",
            }
        ]
    except Exception as e:
        logger.error(f"Serper Scholar 搜索失败: {e}")
        return [
            {
                "title": "[错误]",
                "url": "",
                "abstract": f"Serper Scholar 搜索失败: {e}",
                "rank": 0,
                "engine": "serper_scholar",
                "result_type": "error",
                "metadata": {
                    "suggestion": "请检查 SERPER_API_KEY、网络连接或重试查询"
                },
            }
        ]


@mcp.tool(name="get_engine_info", description="获取 Serper 引擎信息")
def get_engine_info() -> Dict[str, Any]:
    return {
        "name": "serper",
        "description": "Serper 搜索引擎（本地 HTTP MCP）",
        "requires_auth": True,
        "status": "ready",
    }


app = mcp.streamable_http_app()


def main() -> None:
    import uvicorn

    port = int(os.getenv("JOINAI_SERPER_MCP_PORT", "7801"))
    uvicorn.run(app, host=os.getenv("JOINAI_MCP_HOST", "127.0.0.1"), port=port)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"启动失败: {e}")
        import sys

        sys.exit(1)
