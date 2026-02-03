from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

class SearchResult(BaseModel):
    """搜索结果的标准化模型"""
    url: str
    title: str
    content: str
    score: float = 0.0
    publish_date: Optional[str] = None
    source: str = "unknown"

class SearchQuery(BaseModel):
    """搜索查询的标准化模型"""
    query: str
    topic: str = "general"  # general, news, etc.
    days: int = 3
    max_results: int = 3
    domains: Optional[List[str]] = None
    additional_params: Dict[str, Any] = {}

class BaseSearchProvider(ABC):
    """搜索提供商的抽象基类"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化搜索提供商
        
        Args:
            config: 提供商特定的配置参数
        """
        self.config = config or {}
        self._initialize()
    
    @abstractmethod
    def _initialize(self) -> None:
        """初始化提供商特定的设置"""
        pass
    
    @abstractmethod
    async def search(self, query: SearchQuery) -> List[SearchResult]:
        """
        执行搜索
        
        Args:
            query: 搜索查询对象
            
        Returns:
            搜索结果列表
        """
        pass
    
    @abstractmethod
    async def extract_content(self, urls: List[str]) -> List[Dict[str, str]]:
        """
        从URL列表提取内容
        
        Args:
            urls: URL列表
            
        Returns:
            包含提取内容的字典列表，格式: [{"url": str, "title": str, "content": str}]
        """
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """返回提供商名称"""
        pass
    
    def validate_query(self, query: SearchQuery) -> bool:
        """
        验证查询参数是否有效
        
        Args:
            query: 搜索查询对象
            
        Returns:
            是否有效
        """
        return bool(query.query.strip())
    
    def filter_results(self, results: List[SearchResult], min_score: float = 0.0) -> List[SearchResult]:
        """
        过滤搜索结果
        
        Args:
            results: 原始搜索结果
            min_score: 最小分数阈值
            
        Returns:
            过滤后的结果
        """
        return [result for result in results if result.score >= min_score] 