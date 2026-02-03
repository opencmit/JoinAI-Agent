import json
import traceback

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from pydantic import BaseModel
from langgraph_agent.prompts import REPORTER_PROMPT
from langgraph_agent.graph.state import AgentState
from langgraph_agent.graph.llm import get_llm_client, safe_llm_invoke
from langgraph_agent.utils.json_utils import sanitize_string_for_json, json_repair
from langgraph_agent.config import logger

class ReporterSchema(BaseModel):
    path: str
    content: str

async def generate_reporter(state: AgentState, config: RunnableConfig):
    # 获取messages
    messages = state["messages"]

    # 首先进行思考，用于向用户输出思考过程
    llm, model_name = get_llm_client(state, config)

    # 获取子任务，生成系统prompt
    sub_task = state["sub_task"]
    prompt = REPORTER_PROMPT.format(task=sub_task)

    system_message = SystemMessage(content=prompt)
    if isinstance(messages[0], SystemMessage):
        messages[0] = system_message
    else:
        messages.insert(0, system_message)

    # messages.append(HumanMessage(content="请根据任务需求，生成一份报告"))
    # messages.append(HumanMessage(content="请根据任务需求生成报告，并仅返回包含path与content字段的JSON对象"))
    messages.append(HumanMessage(content="请根据任务需求生成报告，不要加任何额外输出，仅返回不带```markdown ```标签的markdown内容"))

    try:
        # structured_llm = llm.with_structured_output(ReporterSchema)
        # payload = await safe_llm_invoke(structured_llm, model_name, messages)
        # state["report_meta"] = {"path": payload.path, "content": payload.content}
        # response = AIMessage(content=payload.content, name="reporter")

        response = await safe_llm_invoke(llm, config, model_name, messages)
        logger.info(f"generate_reporter response: {str(response)}")
        response.name="reporter"

        # 清理SystemMessage
        if isinstance(state["messages"][0], SystemMessage):
            state["messages"].pop(0)

        # 清理HumanMessage
        if isinstance(state["messages"][-1], HumanMessage):
            state["messages"].pop(-1)

        return response
    except Exception as e:
        logger.error(f"❌ reporter 生成报告失败: {str(e)}")
        raise e

async def reporter_summary(
        state: AgentState,
        config: RunnableConfig
):
    """
    reporter 总结 llm 调用
    """

    llm, model_name = get_llm_client(state, config)

    messages = state["messages"]
    
    system_message = SystemMessage(content="""
    你是一个专业的工具执行结果总结专家，请仅对工具执行的结果做一个简要的总结陈述，不超过50字。
    """)

    if isinstance(messages[0], SystemMessage):
        messages[0] = system_message
    else:
        messages.insert(0, system_message)

    try:
        response = await safe_llm_invoke(llm, config, model_name, messages)
        logger.info(f"Reporter summery response: {response}")

        # 清理SystemMessage
        if isinstance(state["messages"][0], SystemMessage):
            state["messages"].pop(0)

        return response
    except Exception as e:
        logger.error(f"❌ Reporter 总结失败: {str(e)}")
        raise e

async def generate_reporter_result(
        state: AgentState,
        config: RunnableConfig
):
    """
    生成对子任务完成的描述
    """

    llm, model_name = get_llm_client(state, config)

    messages = [
        SystemMessage(content="你是一个专业的AI助手。"),
        AIMessage(content="任务：" + state["sub_task"], name="reporter"),
        HumanMessage(content="请写出对任务完成的表述")
    ]
    
    try:
        response = await safe_llm_invoke(llm, config, model_name, messages)
        logger.info(f"Reporter summery response: {response}")

        return response
    except Exception as e:
        logger.error(f"❌ Reporter 总结失败: {str(e)}")
        raise e
