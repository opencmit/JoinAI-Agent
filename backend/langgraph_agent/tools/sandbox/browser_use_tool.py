from langchain_openai import ChatOpenAI
from langgraph_agent.config import global_config
from browser_use import Agent

import asyncio
import os
import contextlib
from contextlib import asynccontextmanager

from copilotkit.langchain import copilotkit_emit_state

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union, Tuple, AsyncGenerator
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from typing_extensions import Annotated
from langgraph_agent.graph.state import AgentState
from langgraph_agent.tools.sandbox.manager import sbx_manager
from langgraph_agent.utils.message_utils import get_last_show_message_id
from browser_use import Browser, Agent

# 浏览器工具的输入模型
class BrowserTaskInput(BaseModel):
    task: str = Field(description="浏览器任务描述")
    use_vision: bool = Field(default=False, description="是否使用视觉功能")
    include_details: bool = Field(default=False, description="是否在结果中包含详细信息，如URL历史和截图路径")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

# 注释掉结构化输入模型
# class BrowserStructuredTaskInput(BaseModel):
#     task: str = Field(description="浏览器任务描述")
#     output_schema: Dict[str, Any] = Field(description="输出结构模式，用于结构化数据抓取")
#     use_vision: bool = Field(default=False, description="是否使用视觉功能")
#     state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class SandboxBrowserTool:
    """沙箱浏览器工具类"""
    
    def __init__(self):
        """初始化沙箱浏览器工具"""
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
    @asynccontextmanager
    async def _get_browser(state: AgentState) -> AsyncGenerator[Tuple[AgentState, Browser], None]:
        """获取或创建浏览器实例的上下文管理器，自动关闭浏览器"""
        state, sandbox = await sbx_manager.get_sandbox_async(state)
        
        # 创建浏览器实例，直接传递参数
        browser = Browser(
            headless=False,
            disable_security=True,
            cdp_url=global_config.CHROME_CDP_URL
        )
        
        try:
            yield state, browser
        finally:
            # 确保浏览器被关闭
            await browser.close()
    
    @staticmethod
    async def run_browser_task(task: str, use_vision: bool, include_details: bool, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """运行浏览器任务"""
        log_index = await SandboxBrowserTool._add_log(state, f"🌐 执行浏览器任务: '{task}'", config)
        
        try:
            async with SandboxBrowserTool._get_browser(state) as (state, browser):                
                # 使用合适的LLM
                llm = ChatOpenAI(model=global_config.BROWSER_LLM, temperature=0.7,top_p=0.8, base_url=global_config.OPENAI_BASE_URL,streaming=True)
                planner_llm = ChatOpenAI(model=global_config.BROWSER_PLAN_LLM, temperature=0.7,top_p=0.8, base_url=global_config.OPENAI_BASE_URL,streaming=True) if global_config.BROWSER_PLAN_LLM else None
                
                # 创建Agent并执行任务
                agent = Agent(
                    task=task,
                    llm=llm,
                    planner_llm=planner_llm,
                    browser=browser,
                    use_vision=use_vision,
                )
                
                # 运行任务
                result = await agent.run()
                
                # 尝试不同方法获取结果
                content = ""
                
                # 首先尝试获取final_result
                final_result = result.final_result()
                if final_result:
                    content = final_result
                else:
                    # 尝试从extracted_content列表获取内容
                    extracted_contents = result.extracted_content()
                    if extracted_contents and len(extracted_contents) > 0:
                        content = "\n".join(extracted_contents)
                    else:
                        # 获取所有操作结果
                        action_results = result.action_results()
                        if action_results and len(action_results) > 0:
                            # 过滤有内容的结果
                            content_results = [r.extracted_content for r in action_results if r.extracted_content]
                            if content_results:
                                content = "\n".join(content_results)
                            else:
                                # 如果仍然没有内容，记录执行的动作名称
                                action_names = result.action_names()
                                if action_names:
                                    content = f"执行了以下操作：{', '.join(action_names)}"
                                    # 尝试获取最后一个动作的详细信息
                                    last_action = result.last_action()
                                    if last_action:
                                        content += f"\n最后操作详情: {last_action}"
                                else:
                                    content = "浏览器任务未产生明确结果"
                
                # 添加任务状态信息
                success_status = result.is_successful()
                if success_status is not None:
                    content += f"\n任务状态: {'成功' if success_status else '失败'}"
                
                # 如果有错误，也添加到结果中
                errors = [e for e in result.errors() if e is not None]
                if errors and not success_status:
                    content += "\n执行过程中的错误:\n" + "\n".join(errors)
                
                # 如果请求详细信息，添加URL和截图路径
                if include_details:
                    # 添加访问的URL历史
                    # urls = result.urls()
                    # if urls and any(urls):
                    #     content += "\n\n访问的URL历史:\n"
                    #     for i, url in enumerate([u for u in urls if u]):
                    #         content += f"{i+1}. {url}\n"
                    
                    # 添加截图路径
                    screenshots = result.screenshots()
                    if screenshots and any(screenshots):
                        for i, screenshot in screenshots[-1:]:
                            state["temporary_images"].append({
                                "mime_type": "image/png",
                                "base64": screenshot,
                                "file_path": "current_browser_screenshot.png"
                            })
                
                await SandboxBrowserTool._complete_log(state, log_index, config)
                return state, f"浏览器任务执行结果:\n{content}"
                
        except Exception as e:
            await SandboxBrowserTool._complete_log(state, log_index, config)
            return state, f"浏览器任务执行失败: {str(e)}"
    
    # 注释掉结构化浏览器任务方法
    # @staticmethod
    # async def run_structured_browser_task(task: str, output_schema: Dict[str, Any], use_vision: bool, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
    #     """运行结构化浏览器任务，返回符合指定格式的数据"""
    #     log_index = await SandboxBrowserTool._add_log(state, f"🌐 执行结构化浏览器任务: '{task}'", config)
    #     
    #     try:
    #         state, browser = await SandboxBrowserTool._get_browser(state)
    #         
    #         # 使用合适的LLM
    #         llm = ChatOpenAI(model=global_config.BROWSER_LLM, temperature=0.7,top_p=0.8, base_url=global_config.OPENAI_BASE_URL,streaming=True)
    #         planner_llm = ChatOpenAI(model=global_config.BROWSER_PLAN_LLM, temperature=0.7,top_p=0.8, base_url=global_config.OPENAI_BASE_URL,streaming=True) if global_config.BROWSER_PLAN_LLM else None
    #         
    #         # 创建输出控制器
    #         from pydantic import create_model
    #         ModelClass = create_model("DynamicModel", **output_schema)
    #         controller = Controller(output_model=ModelClass)
    #         
    #         # 创建Agent并执行任务
    #         agent = Agent(
    #             task=task,
    #             llm=llm,
    #             browser=browser,
    #             use_vision=use_vision,
    #             controller=controller
    #         )
    #         
    #         # 运行任务
    #         result = await agent.run()
    #         final_result = result.final_result()
    #         
    #         # 尝试解析结果
    #         try:
    #             parsed_result = ModelClass.model_validate_json(final_result)
    #             formatted_result = parsed_result.model_dump_json(indent=2)
    #             await SandboxBrowserTool._complete_log(state, log_index, config)
    #             return state, f"浏览器任务执行完成，结构化结果:\n{formatted_result}"
    #         except Exception as parse_error:
    #             await SandboxBrowserTool._complete_log(state, log_index, config)
    #             return state, f"浏览器任务执行完成，但结果解析失败: {str(parse_error)}\n原始结果:\n{final_result}"
    #             
    #     except Exception as e:
    #         await SandboxBrowserTool._complete_log(state, log_index, config)
    #         return state, f"结构化浏览器任务执行失败: {str(e)}"
    
    @staticmethod
    @tool("browser", args_schema=BrowserTaskInput)
    async def browser_tool(
        task: str,
        use_vision: bool = False,
        include_details: bool = False,
        state: Optional[AgentState] = None,
        special_config_param: Optional[RunnableConfig] = None
    ) -> Tuple[AgentState, str]:
        """
        使用浏览器执行网络任务，例如：
        - 搜索信息
        - 浏览网页
        - 执行网络操作
        - 提取网页信息
        
        参数:
        - task: 要执行的任务描述
        - use_vision: 是否使用视觉功能，对于需要识别图像内容的任务设置为True
        - include_details: 是否在结果中包含详细信息（URL历史、截图路径等）
        """
        config = special_config_param or RunnableConfig()
        return await SandboxBrowserTool.run_browser_task(task, use_vision, include_details, state, config)
    
    # 注释掉结构化浏览器工具
    # @staticmethod
    # @tool("browser_structured", args_schema=BrowserStructuredTaskInput)
    # async def browser_structured_tool(
    #     task: str,
    #     output_schema: Dict[str, Any],
    #     use_vision: bool = False,
    #     state: Optional[AgentState] = None,
    #     special_config_param: Optional[RunnableConfig] = None
    # ) -> Tuple[AgentState, str]:
    #     """
    #     使用浏览器执行网络任务，并返回符合指定结构的数据，例如：
    #     - 以特定格式抓取商品价格
    #     - 获取新闻列表
    #     - 提取结构化信息
    #     """
    #     config = special_config_param or RunnableConfig()
    #     return await SandboxBrowserTool.run_structured_browser_task(task, output_schema, use_vision, state, config)

# 导出工具
browser_tool = SandboxBrowserTool.browser_tool
# browser_structured_tool = SandboxBrowserTool.browser_structured_tool

# 测试代码
async def test_browser_tools():
    """测试浏览器工具"""
    print("开始测试沙箱浏览器工具...")
    import traceback
    
    # 创建一个初始状态
    state = AgentState(
        copilotkit={
            "actions": []
        },
        messages=[],
        logs=[],
        e2b_sandbox_id="your_sandbox_id_here"
    )
    
    try:
        # 测试基础浏览器工具
        print("\n1. 测试基础浏览器工具:")
        basic_result = await SandboxBrowserTool.browser_tool.ainvoke(
            {
                "task": "搜索并比较ChatGPT和Claude AI的价格", 
                "use_vision": False,
                "include_details": False,
                "state": state
            }
        )
        print(f"结果: {basic_result}")
        
        # 测试带详细信息的浏览器工具
        print("\n2. 测试带详细信息的浏览器工具:")
        detailed_result = await SandboxBrowserTool.browser_tool.ainvoke(
            {
                "task": "查找最新的Python编程教程", 
                "use_vision": True,
                "include_details": True,
                "state": state
            }
        )
        print(f"结果: {detailed_result}")
        
        # 注释掉结构化浏览器工具测试
        # print("\n3. 测试结构化浏览器工具:")
        # schema = {
        #     "products": (List[Dict[str, Union[str, float]]], ...)
        # }
        # structured_result = await SandboxBrowserTool.browser_structured_tool.ainvoke(
        #     {
        #         "task": "搜索ChatGPT和Claude AI的价格并提取结构化信息", 
        #         "output_schema": schema,
        #         "use_vision": False,
        #         "state": state
        #     }
        # )
        # print(f"结果: {structured_result}")
        
        print("\n测试完成: 沙箱浏览器工具测试成功!")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_browser_tools())