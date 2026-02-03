import os
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import unquote
import requests
import aiohttp

from .base_search_provider import BaseSearchProvider, SearchResult, SearchQuery


class BochaSearchProvider(BaseSearchProvider):
    """Bocha搜索提供商实现"""
    
    def _initialize(self) -> None:
        """初始化Bocha客户端"""
        api_key = self.config.get('api_key')
        base_url = self.config.get('base_url') or "https://api.bochaai.com/v1/web-search"

        if not api_key:
            raise ValueError("No API key provided. Please provide the api_key attribute or set the BOCHA_API_KEY environment variable.")
        if not base_url:
            raise ValueError("No base_url provided. Please set the BOCHA_BASE_URL environment variable.")

        self.api_key = api_key
        self.base_url = base_url
        self.min_score = self.config.get('min_score', 0.45)
    
    @property
    def provider_name(self) -> str:
        return "bocha"

    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        使用Bocha执行搜索

        Args:
            query: 搜索查询对象

        Returns:
            标准化的搜索结果列表
        """
        try:
            # 添加时间信息到查询中
            query_with_date = f"{query.query} {datetime.now().strftime('%m-%Y')}"
            # 调用Bocha API
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Host': 'api.bochaai.com'
            }

            data = {
                "query": query_with_date,
                "freshness": "noLimit",
                "summary": True,
                "count": query.max_results,
                **query.additional_params  # 允许传递额外的Bocha特定参数
            }

            # 转换为标准化结果格式
            search_results = []

            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=headers, json=data, ssl=False) as response:
                    if response.status == 200:
                        json_response = await response.json()
                        if json_response["code"] == 200 and json_response["data"] and json_response["data"]["webPages"][
                            "value"]:
                            webpages = json_response["data"]["webPages"]["value"]
                            for page in webpages:
                                search_result = SearchResult(
                                    url=page["url"],
                                    title=page["name"],
                                    content=page["summary"][:300],  # 限制内容长度
                                    publish_date=page["dateLastCrawled"],
                                    source=self.provider_name
                                )
                                search_results.append(search_result)
                            return search_results
                        else:
                            print(f"Bocha搜索查询'{query.query}'时发生错误: 未找到相关结果或结果解析失败")
                            return []
                    else:
                        print(f"Bocha搜索API请求失败，状态码: {response.status}, 错误信息: {response.text}")
                        return []
        except Exception as e:
            print(f"Bocha搜索查询'{query.query}'时发生错误: {str(e)}")
            return []



    async def extract_content(self, urls: List[str]) -> List[Dict[str, str]]:
        """
        使用bacha提取URL内容

        Args:
            urls: URL列表

        Returns:
            提取的内容列表
        """
        print(f"bocha没有scrape提取内容功能")
        return []
