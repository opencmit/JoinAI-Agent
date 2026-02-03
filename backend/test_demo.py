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

# 在代码开头调用
setup_logging()
# If you're in an async function
async def main():
    result = await agent_graph.ainvoke(state)
    print("-----------------------------------------------------------")
    # print(type(result))
    # print(result.keys())
    messages = result.get("messages", [])
    # print(type(messages))
    if messages:
        print(messages[-1].content)
        

###添加附件
# files = [".TestFiles.docx"]
# state = {
#         "messages": [HumanMessage(content="总结一下附件的主要内容")],
#         "files":files,
#     }


state = {
    "messages": [HumanMessage(content="写一篇AI技术报告")],
}
# Run the async function
asyncio.run(main())
