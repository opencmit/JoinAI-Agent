from typing import Dict, Any, Type
from .base_search_provider import BaseSearchProvider
from .bocha_provider import BochaSearchProvider
from .tavily_provider import TavilySearchProvider


class SearchProviderFactory:
    """搜索提供商工厂类"""

    # 注册的提供商映射
    _providers: Dict[str, Type[BaseSearchProvider]] = {
        "tavily": TavilySearchProvider,
        "bocha": BochaSearchProvider,
    }

    # 默认配置
    _default_configs: Dict[str, Dict[str, Any]] = {
        "tavily": {
            "min_score": 0.45,
            "max_results": 3,
        }
    }

    @classmethod
    def register_provider(
            cls,
            name: str,
            provider_class: Type[BaseSearchProvider],
            default_config: Dict[str, Any] = None
    ) -> None:
        """
        注册新的搜索提供商

        Args:
            name: 提供商名称
            provider_class: 提供商类
            default_config: 默认配置
        """
        cls._providers[name] = provider_class
        if default_config:
            cls._default_configs[name] = default_config

    @classmethod
    def create_provider(
            cls,
            provider_name: str,
            config: Dict[str, Any] = None
    ) -> BaseSearchProvider:
        """
        创建搜索提供商实例

        Args:
            provider_name: 提供商名称
            config: 自定义配置，会与默认配置合并

        Returns:
            搜索提供商实例

        Raises:
            ValueError: 当提供商未注册时
        """
        if provider_name not in cls._providers:
            available_providers = list(cls._providers.keys())
            raise ValueError(
                f"未知的搜索提供商: {provider_name}。"
                f"可用的提供商: {available_providers}"
            )

        # 合并默认配置和自定义配置
        default_config = cls._default_configs.get(provider_name, {})
        final_config = {**default_config, **(config or {})}

        provider_class = cls._providers[provider_name]
        return provider_class(final_config)

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """获取所有可用的提供商名称"""
        return list(cls._providers.keys())

    @classmethod
    def get_default_config(cls, provider_name: str) -> Dict[str, Any]:
        """获取指定提供商的默认配置"""
        return cls._default_configs.get(provider_name, {}).copy() 