from copilotkit.langchain import copilotkit_emit_state
from langgraph.types import Command, interrupt
from pydantic import BaseModel, Field
from typing_extensions import List, Dict, Optional, Any, Union
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from langgraph_agent.utils.message_utils import get_last_show_message_id
from typing_extensions import Annotated
from typing_extensions import TypedDict
from langgraph_agent.graph.state import AgentState
import traceback
from langgraph.errors import GraphInterrupt

class MessageToolInput(BaseModel):
    """统一的消息工具输入模型"""
    operation: str = Field(description="消息操作类型，可选值: ask, web_browser_takeover, complete")
    text: Optional[str] = Field(None, description="消息文本，适用于ask和web_browser_takeover操作")
    attachments: Optional[List[str]] = Field(None, description="attachments: Optional file paths or URLs to attach to the question，适用于ask和web_browser_takeover操作")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class MessageTool:
    """统一的消息操作工具类"""
    
    def __init__(self):
        """初始化消息工具"""
        pass
    
    @staticmethod
    async def _add_log(state: AgentState, message: str, config: RunnableConfig) -> int:
        """添加日志并返回日志索引"""
        state["logs"] = state.get("logs", [])
        log_index = len(state["logs"])
        state["logs"].append({
            "message": message,
            "done": False,
            "messageId":  get_last_show_message_id(state["messages"])
        })
        await copilotkit_emit_state(config, state)
        return log_index
    
    @staticmethod
    async def _complete_log(state: AgentState, log_index: int, config: RunnableConfig):
        """完成日志"""
        state["logs"][log_index]["done"] = True
        await copilotkit_emit_state(config, state)

    @staticmethod
    async def ask(text: str, attachments: Optional[Union[str, List[str]]], state: AgentState, config: RunnableConfig) -> tuple[AgentState, str]:
        """向用户提问并等待回应"""
        log_index = await MessageTool._add_log(state, f"❓ 向用户提问: '{text}'", config)
        
        try:
            # 处理附件
            if attachments and isinstance(attachments, str):
                attachments = [attachments]
                
            # 构建问题数据结构
            question_data = {
                "question": text,
                "attachments": attachments if attachments else [],
                "type": "ask"
            }
            
            # 使用interrupt等待用户回应
            # response = interrupt(question_data)
            
            # 更新提问状态
            await MessageTool._complete_log(state, log_index, config)
            
            # 将用户回应添加到状态中
            # if "responses" not in state:
            #     state["responses"] = []
            # state["responses"].append({
            #     "question": text,
            #     "response": response
            # })
            
            # return state, {"status": "用户已回应", "response": response}
            state["completed"] = True
            return state, "已向用户提问，请等待用户回应"
        except GraphInterrupt:
            # 捕捉GraphInterrupt但不处理，直接重新抛出
            raise
        except Exception as e:
            await MessageTool._complete_log(state, log_index, config)
            traceback.print_exc()
            return state, f"提问失败: {str(e)}"

    @staticmethod
    async def web_browser_takeover(text: str, attachments: Optional[Union[str, List[str]]], state: AgentState, config: RunnableConfig) -> tuple[AgentState, str]:
        """请求用户接管浏览器交互"""
        log_index = await MessageTool._add_log(state, f"🌐 请求浏览器接管: '{text}'", config)
        
        try:
            # 处理附件
            if attachments and isinstance(attachments, str):
                attachments = [attachments]
                
            # 构建接管请求数据结构
            takeover_data = {
                "question": text,
                "attachments": attachments if attachments else [],
                "type": "web_browser_takeover"
            }
            
            # 使用interrupt等待用户完成浏览器操作
            # result = interrupt(takeover_data)
            
            # 更新接管状态
            await MessageTool._complete_log(state, log_index, config)
            
            # 将操作结果添加到状态中
            if "browser_actions" not in state:
                state["browser_actions"] = []
            # state["browser_actions"].append({
            #     "instructions": text,
            #     "result": result
            # })
            
            # return state, {"status": "浏览器操作已完成", "result": result}
            state["completed"] = True
            return state, "已请求浏览器接管，请等待用户完成操作"
        except GraphInterrupt:
            # 捕捉GraphInterrupt但不处理，直接重新抛出
            raise
        except Exception as e:
            traceback.print_exc()
            await MessageTool._complete_log(state, log_index, config)
            return state, f"请求浏览器接管失败: {str(e)}"

    @staticmethod
    async def complete(state: AgentState, config: RunnableConfig) -> tuple[AgentState, str]:
        """完成所有任务"""
        log_index = await MessageTool._add_log(state, "✅ 所有任务已完成", config)
        
        try:
            await MessageTool._complete_log(state, log_index, config)
            state["completed"] = True
            return state, {"status": "completed"}
                
        except Exception as e:
            traceback.print_exc()
            await MessageTool._complete_log(state, log_index, config)
            return state, f"进入完成状态失败: {str(e)}"

    @staticmethod
    @tool("message", args_schema=MessageToolInput)
    async def message_tool(
        operation: str,
        text: Optional[str] = None,
        attachments: Optional[Union[str, List[str]]] = None,
        state: Optional[AgentState] = None,
        special_config_param: Optional[RunnableConfig] = None
    ) -> tuple[AgentState, str]:
        """
        统一的消息操作工具，支持以下操作：
        - ask: 向用户提问并等待回应
        - web_browser_takeover: 请求用户接管浏览器交互
        - complete: 完成所有任务
        """
        config = special_config_param or RunnableConfig()
        
        if operation == "ask":
            if not text:
                return state, "提问操作需要提供text参数"
            return await MessageTool.ask(text, attachments, state, config)
        
        elif operation == "web_browser_takeover":
            if not text:
                return state, "浏览器接管操作需要提供text参数"
            return await MessageTool.web_browser_takeover(text, attachments, state, config)
        
        elif operation == "complete":
            return await MessageTool.complete(state, config)
        
        else:
            return state, f"不支持的消息操作: {operation}"

message_tool = MessageTool.message_tool

async def test_tools_invoke():
    """使用工具调用API测试工具函数"""
    print("开始测试消息工具的工具调用API...")
    import traceback
    
    # 创建一个初始状态
    state = AgentState(
        input_data={},
        max_iterations=5,
        messages=[],
        temporary_message_content_list=[],
        iteration_count=0,
        logs=[],
        e2b_sandbox_id="test_sandbox",
        copilotkit={"actions": []},
        temporary_images=[],
        structure_tool_results={},
        completed=False,
        mcp_tools=[],
        model="test"
    )
    
    try:
        # 测试统一消息工具 - 提问
        print("\n1. 测试统一消息工具 - 提问:")
        ask_result = await MessageTool.message_tool.ainvoke({
            "operation": "ask",
            "text": "你喜欢什么颜色？\n1) 红色\n2) 蓝色\n3) 绿色",
            "attachments": ["colors.txt"],
            "state": state
        })
        print(f"结果: {ask_result}")
        
        # 测试统一消息工具 - 浏览器接管
        print("\n2. 测试统一消息工具 - 浏览器接管:")
        browser_result = await MessageTool.message_tool.ainvoke({
            "operation": "web_browser_takeover",
            "text": "请完成CAPTCHA验证",
            "attachments": ["screenshot.png"],
            "state": state
        })
        print(f"结果: {browser_result}")
        
        # 测试统一消息工具 - 完成
        print("\n3. 测试统一消息工具 - 完成:")
        complete_result = await MessageTool.message_tool.ainvoke({
            "operation": "complete",
            "state": state
        })
        print(f"结果: {complete_result}")
        
        print("\n所有工具调用API测试完成!")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        traceback.print_exc()
        
    # 打印最终状态
    print("\n最终状态:")
    if hasattr(state, 'logs') and state.logs:
        for i, log in enumerate(state.logs):
            print(f"Log {i+1}: {log['message']} - 完成状态: {log['done']}")
    else:
        print("没有日志记录")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tools_invoke())
