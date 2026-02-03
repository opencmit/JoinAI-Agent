import json
import os
import re
from langchain_openai import ChatOpenAI
import functools
import asyncio
from typing import Callable, TypeVar, ParamSpec, cast, Dict, Any
from langchain_core.messages import AIMessage
# from langchain_core.output_parsers.openai_tools import parse_tool_call
import contextlib
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional

load_dotenv(override=False)

openai_base_url = os.getenv("OPENAI_BASE_URL")


# Description: Configuration file
class Config(BaseSettings):
    def __init__(self):
        """
        Initializes the configuration for the agent
        """
        print("openai_base_url", openai_base_url)
        super().__init__()

    # Base URL
    OPENAI_BASE_URL: str = Field(...)
    
    # 基础模型名称
    BASE_LLM: str = Field(...)
    
    # # 浏览器模型名称
    # BROWSER_LLM: str = Field(...)
    
    # # 浏览器规划模型名称
    # BROWSER_PLAN_LLM: Optional[str] = Field(None)

    # 调试模式
    # SANDBOX_DEBUG: bool = Field(...)

    # # 沙盒域名
    # SANDBOX_DOMAIN: str = Field(...)

    # 沙盒工作目录
    SANDBOX_WORKING_DIR: str = Field(...)

    # # 文件服务器地址
    # FILE_URL: str = Field(...)

    # # 文件服务器 APPID
    # FILE_APPID: str = Field(...)

    # # 文件服务器 APPKEY
    # FILE_APPKEY: str = Field(...)

    # chrome cdp 地址(使用Chrome调试协议默认端口9223)
    CHROME_CDP_URL: Optional[str] = None

    MCP_SERVERS_CONFIG: str = os.getenv("MCP_SERVERS_CONFIG", "config/mcp_server.json")
    
    A2A_SERVERS_CONFIG: str = os.getenv("A2A_SERVERS_CONFIG", "config/a2a_server.json")

    async def load_mcp_config(self) -> Dict[str, Any]:
        """
        加载并解析MCP服务器配置文件（异步版本）。

        Returns:
            Dict[str, Any]: 解析后的MCP服务器配置字典

        Raises:
            FileNotFoundError: 如果配置文件不存在
            json.JSONDecodeError: 如果JSON格式错误
            Exception: 其他文件读取错误
        """
        config_path = self.MCP_SERVERS_CONFIG

        # 如果路径是相对路径，则相对于项目根目录
        if not os.path.isabs(config_path):
            # 获取项目根目录（假设config.py在langgraph_agent目录下）
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            config_path = os.path.join(project_root, config_path)

        try:
            # ✅ 修复 BlockingError：使用 asyncio.to_thread 包装同步 I/O 操作
            # 原因：json.load() 是同步阻塞操作，会被 LangGraph 的 blockbuster 检测到
            # 解决：在独立线程中执行，避免阻塞事件循环
            def _load_config():
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # 在线程池中执行同步操作
            config_data = await asyncio.to_thread(_load_config)

            # 如果未配置 SERPER_API_KEY，则禁用本地 serper MCP 服务
            try:
                serper_api_key = os.getenv("SERPER_API_KEY", "")
                if (not serper_api_key) and ("joinai-serper" in config_data):
                    del config_data["joinai-serper"]
                    logger.info("未检测到 SERPER_API_KEY，已禁用 joinai-serper MCP 服务")
                
                jina_api_key = os.getenv("JINA_API_KEY", "")
                if (not jina_api_key) and ("joinai-jina" in config_data):
                    del config_data["joinai-jina"]
                    logger.info("未检测到 JINA_API_KEY，已禁用 joinai-jina MCP 服务")

                serpapi_api_key = os.getenv("SERPAPI_API_KEY", "")
                if (not serpapi_api_key) and ("joinai-serpapi" in config_data):
                    del config_data["joinai-serpapi"]
                    logger.info("未检测到 SERPAPI_API_KEY，已禁用 joinai-serpapi MCP 服务")


                # 处理 jina-mcp-server（远程 SSE）配置
                # jina_api_key = os.getenv("JINA_API_KEY", "")
                # if "jina-mcp-server" in config_data:
                #     if jina_api_key:
                #         # 确保 headers 存在并写入 Bearer token
                #         headers = config_data["jina-mcp-server"].setdefault("headers", {})
                #         headers["Authorization"] = f"Bearer {jina_api_key}"
                #     else:
                #         # 没有密钥则禁用，避免发送空 Bearer 导致协议错误
                #         del config_data["jina-mcp-server"]
                #         logger.info("未检测到 JINA_API_KEY，已禁用 jina-mcp-server MCP 服务")

            except Exception as e:
                logger.warning(f"处理 joinai-serper/joinai-serpapi/joinai-jina 配置失败: {e}")

            logger.info(f"成功加载MCP配置文件: {config_path}")
            return config_data
        except FileNotFoundError:
            logger.error(f"MCP配置文件不存在: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"MCP配置文件JSON格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"读取MCP配置文件时发生错误: {e}")
            raise

    def load_a2a_config(self) -> Dict[str, Any]:
        """
        加载并解析A2A服务器配置文件。

        Returns:
            Dict[str, Any]: 解析后的A2A服务器配置字典

        Raises:
            FileNotFoundError: 如果配置文件不存在
            json.JSONDecodeError: 如果JSON格式错误
            Exception: 其他文件读取错误
        """
        config_path = self.A2A_SERVERS_CONFIG

        # 如果路径是相对路径，则相对于项目根目录
        if not os.path.isabs(config_path):
            # 获取项目根目录（假设config.py在langgraph_agent目录下）
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            config_path = os.path.join(project_root, config_path)

        try:
            # 直接同步读取配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            logger.info(f"成功加载A2A配置文件: {config_path}")
            return config_data
        except FileNotFoundError:
            logger.error(f"A2A配置文件不存在: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"A2A配置文件JSON格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"读取A2A配置文件时发生错误: {e}")
            raise


    @field_validator('CHROME_CDP_URL', mode='before')
    @classmethod
    def set_chrome_cdp_url(cls, v, info):
        sandbox_domain = info.data.get('SANDBOX_DOMAIN')
        if sandbox_domain:
            return re.sub(r':\d+$', ':9223', sandbox_domain)
        return None

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        extra = 'ignore'
        
global_config = Config()

import logging
logger = logging.getLogger(__name__)
# logger.info(f"SANDBOX_DOMAIN:{global_config.SANDBOX_DOMAIN}")
# logger.info(f"BROWSER_LLM:{global_config.BROWSER_LLM}")
logger.info(f"BASE_LLM:{global_config.BASE_LLM}")
logger.info(f"SANDBOX_WORKING_DIR:{global_config.SANDBOX_WORKING_DIR}")
