from typing import Callable, Dict, Any
from langgraph_agent.graph.state import AgentState

ToolProcessor = Callable[..., tuple[AgentState, str, Dict[str, Any]]]

def apply_processor(processor: ToolProcessor, *args, **kwargs) -> tuple[AgentState, str, Dict[str, Any]]:
    return processor(*args, **kwargs)