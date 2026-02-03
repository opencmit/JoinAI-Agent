import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class SearchConfig:
    """搜索配置管理类"""

    # 默认搜索提供商
    DEFAULT_PROVIDER = "bocha"

    # 搜索提供商配置
    PROVIDER_CONFIGS: Dict[str, Dict[str, Any]] = {
        "tavily": {
            "api_key": os.getenv("TAVILY_API_KEY"),
            "min_score": 0.45,
            "max_results": 3,
        },
        "bocha": {
            "api_key": os.getenv("BOCHA_API_KEY"),
            "base_url": os.getenv("BOCHA_BASE_URL"),
            "min_score": 0.45,
            "max_results": 3,
        },
        # 可以在这里添加其他提供商的配置
        # "google": {
        #     "api_key": os.getenv("GOOGLE_API_KEY"),
        #     "cx": os.getenv("GOOGLE_CX"),
        #     "min_score": 0.5,
        # },
        # "bing": {
        #     "api_key": os.getenv("BING_API_KEY"),
        #     "min_score": 0.4,
        # }
    }

    @classmethod
    def get_provider_config(cls, provider_name: str) -> Dict[str, Any]:
        """
        获取指定提供商的配置

        Args:
            provider_name: 提供商名称

        Returns:
            提供商配置字典
        """
        return cls.PROVIDER_CONFIGS.get(provider_name, {}).copy()

    @classmethod
    def get_current_provider(cls) -> str:
        """
        获取当前使用的搜索提供商
        可以通过环境变量SEARCH_PROVIDER覆盖

        Returns:
            当前提供商名称
        """
        return os.getenv("SEARCH_PROVIDER", cls.DEFAULT_PROVIDER)

    @classmethod
    def set_provider_config(
            cls,
            provider_name: str,
            config: Dict[str, Any]
    ) -> None:
        """
        设置提供商配置

        Args:
            provider_name: 提供商名称
            config: 配置字典
        """
        cls.PROVIDER_CONFIGS[provider_name] = config

    @classmethod
    def update_provider_config(
            cls,
            provider_name: str,
            updates: Dict[str, Any]
    ) -> None:
        """
        更新提供商配置

        Args:
            provider_name: 提供商名称
            updates: 要更新的配置项
        """
        if provider_name not in cls.PROVIDER_CONFIGS:
            cls.PROVIDER_CONFIGS[provider_name] = {}

        cls.PROVIDER_CONFIGS[provider_name].update(updates) 