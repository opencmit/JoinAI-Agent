"""
应用配置
"""
import os
from pathlib import Path
from typing import Optional
from functools import lru_cache
from dotenv import load_dotenv

# 加载.env文件
# 从项目根目录查找.env文件
env_path = Path(__file__).parent.parent / ".env"
print("env_path", env_path)
print("env_path exists", env_path.exists())
load_dotenv()


class Settings:
    """应用设置"""
    
    # OpenAI配置
    openai_api_key: str
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4o"
    
    # A2A配置
    agent_name: str = "multimodal-recognizer"
    agent_port: int = 8001
    agent_host: str = "0.0.0.0"
    
    # 日志配置
    log_level: str = "INFO"
    
    def __init__(self):
        # 从环境变量读取配置
        print("aaaaaaaaa")
        print("openai_api_key", os.getenv("OPENAI_API_KEY", ""))
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", None)
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        self.agent_name = os.getenv("AGENT_NAME", "multimodal-recognizer")
        self.agent_port = int(os.getenv("AGENT_PORT", "8001"))
        self.agent_host = os.getenv("AGENT_HOST", "0.0.0.0")
        
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        
        # 验证必需配置
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY环境变量未设置")


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例）"""
    return Settings()

