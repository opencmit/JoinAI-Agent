from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import unquote
from tavily import AsyncTavilyClient

from .base_search_provider import BaseSearchProvider, SearchResult, SearchQuery


class TavilySearchProvider(BaseSearchProvider):
    """Tavily搜索提供商实现"""
    
    def _initialize(self) -> None:
        """初始化Tavily客户端"""
        self.client = AsyncTavilyClient(
            api_key=self.config.get('api_key'),  # 可以通过配置传入API密钥
        )
        self.min_score = self.config.get('min_score', 0.45)
    
    @property
    def provider_name(self) -> str:
        return "tavily"
    
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        使用Tavily执行搜索
        
        Args:
            query: 搜索查询对象
            
        Returns:
            标准化的搜索结果列表
        """
        try:
            # 添加时间信息到查询中
            query_with_date = f"{query.query} {datetime.now().strftime('%m-%Y')}"
            
            # 验证topic参数
            topic = query.topic if query.topic in ['general', 'news'] else "general"
            
            # 调用Tavily API
            tavily_response = await self.client.search(
                query=query_with_date,
                topic=topic,
                days=query.days,
                max_results=query.max_results,
                include_domains=query.domains,
                **query.additional_params  # 允许传递额外的Tavily特定参数
            )
            
            # 转换为标准化结果格式
            search_results = []
            for result in tavily_response.get('results', []):
                search_result = SearchResult(
                    url=result.get('url', ''),
                    title=result.get('title', '无标题'),
                    content=result.get('content', '')[:300],  # 限制内容长度
                    score=result.get('score', 0.0),
                    publish_date=result.get('published_date'),
                    source=self.provider_name
                )
                search_results.append(search_result)
            
            # 应用分数过滤
            return self.filter_results(search_results, self.min_score)
            
        except Exception as e:
            print(f"Tavily搜索查询'{query.query}'时发生错误: {str(e)}")
            return []
    
    async def extract_content(self, urls: List[str]) -> List[Dict[str, str]]:
        """
        使用Tavily提取URL内容
        
        Args:
            urls: URL列表
            
        Returns:
            提取的内容列表
        """
        try:
            urls = urls[:5]  # 限制最多5个URL
            response = await self.client.extract(urls=urls)
            results = response.get('results', [])
            
            extracted_content = []
            for item in results:
                content_data = {
                    'url': unquote(item['url']),
                    'title': item.get('title', '无标题'),
                    'content': item['raw_content'][:5000]  # 限制内容长度
                }
                extracted_content.append(content_data)
            
            return extracted_content
            
        except Exception as e:
            print(f"Tavily提取内容时发生错误: {str(e)}")
            return [] 