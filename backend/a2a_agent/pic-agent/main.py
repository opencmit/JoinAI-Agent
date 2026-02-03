"""
多模态识别A2A智能体入口
"""
import logging

from python_a2a import run_server

from app.agent import MultimodalAgent
from config.settings import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """启动A2A智能体服务"""
    try:
        settings = get_settings()
        logger.info(f"正在启动多模态识别智能体: {settings.agent_name}")

        # 创建智能体实例
        agent = MultimodalAgent(name=settings.agent_name)

        # 启动智能体服务
        logger.info(f"智能体服务启动在 {settings.agent_host}:{settings.agent_port}")
        run_server(
            agent,
            host=settings.agent_host,
            port=settings.agent_port,
            debug=False
        )

    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭智能体...")
    except Exception as e:
        logger.error(f"启动智能体时发生错误: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
