import asyncio
import json
import logging
import os
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph_agent.graph.graph import agent_graph

def setup_logging():

    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    
    # Set basic logging level
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s - %(name)s - %(message)s'
    )
    
    # Disable debug output for specific components
    debug_loggers = [
        'httpcore', 'openai', 'httpx', 'http11',
        'langsmith', 'urllib3', 'httpcore.http11'
    ]
    
    for logger_name in debug_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.WARNING)
        logger.propagate = False

# Initialize logging
setup_logging()

app = FastAPI(title="Juzhigongfang Agent API")

class ChatRequest(BaseModel):
    content: str

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint that accepts a content string, invokes the agent graph,
    and returns the last message content via SSE to avoid timeouts.
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        # Initialize state with the user's message
        state = {
            "messages": [HumanMessage(content=request.content)],
        }
        
        # 为避免容器环境中 LangGraph 节点调用缺少 config 参数的问题，这里显式传入 config
        task = asyncio.create_task(
            agent_graph.ainvoke(
                state
            )
        )
        
        try:
            # Loop while the task is running
            while not task.done():

                yield ": keep-alive\n\n"

                try:
                    await asyncio.wait_for(asyncio.shield(task), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

            result = await task
            
            messages = result.get("messages", [])
            final_content = ""
            if messages:
                final_content = messages[-1].content
            
            payload = json.dumps({"content": final_content}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
            
        except Exception as e:
            logging.error(f"Error executing agent: {e}")
            error_payload = json.dumps({"error": str(e)}, ensure_ascii=False)
            yield f"event: error\ndata: {error_payload}\n\n"

    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Disable buffering for Nginx/proxies
        }
    )

if __name__ == "__main__":
    import uvicorn
    # Run the server
    uvicorn.run("api:app", host="0.0.0.0", port=18100, reload=True)

## curl -N -X POST http://localhost:18100/chat -H "Content-Type: application/json" -d '{"content": "你好"}'
