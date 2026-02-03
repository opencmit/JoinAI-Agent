"""
这是一个 JoinAI 结合网络搜索工具进行回答的示例。

JoinAI 中整合了多种检索工具，包括：tavily(function call)、bocha(function call)、serper(MCP)等，这些检索工具都可以简单的配置后使用。

配置方法：
 -1、从各个检索工具官网获取 api_key
 -2、将 api_key 配置到 backed/.env 文件中

例如，在 .env 文件中添加如下配置（可任选其一、其二，或全部配置）：
    TAVILY_API_KEY=your_tavily_api_key
    BOCHA_API_KEY=your_bocha_api_key
    SERPER_API_KEY=your_serper_api_key

"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from langgraph_agent.graph.graph import agent_graph
from langchain_core.messages import HumanMessage
import asyncio
import logging
import os

def setup_logging():
    # 禁用 LangSmith 跟踪（减少网络请求日志）
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    
    # 设置基础日志级别
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s - %(name)s - %(message)s'
    )

    # 特别禁用这些组件的 DEBUG 输出
    debug_loggers = [
        'httpcore', 'openai', 'httpx', 'http11',
        'langsmith', 'urllib3', 'httpcore.http11'
    ]
    
    for logger_name in debug_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
        # 防止日志传播到根日志器
        logger.propagate = False

setup_logging()

async def main():
    result = await agent_graph.ainvoke(state)
    print("-----------------------------------------------------------")
    messages = result.get("messages", [])
    if messages:
        print(messages[-1].content)
        
state = {
    "messages": [HumanMessage(content="明天北京天气怎么样")],
}
# Run the async function
asyncio.run(main())