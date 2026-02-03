from copilotkit.langchain import copilotkit_emit_state

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union, Tuple
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from typing_extensions import Annotated
from langgraph_agent.graph.state import AgentState
from langgraph_agent.tools.sandbox.manager import sbx_manager
from langgraph_agent.utils.message_utils import get_last_show_message_id

# 键盘按键列表
KEYBOARD_KEYS = [
    'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
    'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z',
    '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
    'enter', 'esc', 'backspace', 'tab', 'space', 'delete',
    'ctrl', 'alt', 'shift', 'win',
    'up', 'down', 'left', 'right',
    'f1', 'f2', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9', 'f10', 'f11', 'f12',
    'ctrl+c', 'ctrl+v', 'ctrl+x', 'ctrl+z', 'ctrl+a', 'ctrl+s',
    'alt+tab', 'alt+f4', 'ctrl+alt+delete'
]

# 输入模型定义
class MouseMoveInput(BaseModel):
    x: int = Field(description="鼠标移动的目标X坐标")
    y: int = Field(description="鼠标移动的目标Y坐标")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class MouseClickInput(BaseModel):
    x: Optional[int] = Field(None, description="点击的X坐标（可选）")
    y: Optional[int] = Field(None, description="点击的Y坐标（可选）")
    button: str = Field("left", description="鼠标按键：left, right, middle")
    num_clicks: int = Field(1, description="点击次数")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class ScrollInput(BaseModel):
    amount: int = Field(description="滚动量（正数向上，负数向下）", ge=-10, le=10)
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class TypeTextInput(BaseModel):
    text: str = Field(description="要输入的文本")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class KeyPressInput(BaseModel):
    key: str = Field(description="要按下的按键")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class WaitInput(BaseModel):
    duration: float = Field(0.5, description="等待时间（秒）", ge=0, le=10)
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class DragInput(BaseModel):
    x: int = Field(description="拖拽目标的X坐标")
    y: int = Field(description="拖拽目标的Y坐标")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class ScreenshotInput(BaseModel):
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

# 统一的鼠标工具输入模型
class MouseToolInput(BaseModel):
    operation: str = Field(description="操作类型，可选值: move, click, scroll, drag, screenshot")
    x: Optional[int] = Field(None, description="鼠标X坐标，适用于move, click, drag操作")
    y: Optional[int] = Field(None, description="鼠标Y坐标，适用于move, click, drag操作")
    button: Optional[str] = Field(None, description="鼠标按键：left, right, middle，适用于click操作")
    num_clicks: Optional[int] = Field(None, description="点击次数，适用于click操作")
    amount: Optional[int] = Field(None, description="滚动量，适用于scroll操作")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

# 统一的键盘工具输入模型
class KeyboardToolInput(BaseModel):
    operation: str = Field(description="操作类型，可选值: type_text, press_key, wait")
    text: Optional[str] = Field(None, description="要输入的文本，适用于type_text操作")
    key: Optional[str] = Field(None, description="要按下的按键，适用于press_key操作")
    duration: Optional[float] = Field(None, description="等待时间（秒），适用于wait操作")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

# 基础工具类，提供共享功能
class SandboxBaseTool:
    """沙箱工具基类，提供共享功能"""
    
    def __init__(self):
        """初始化沙箱工具"""
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
    def _get_sandbox(state: AgentState):
        """获取沙箱实例"""
        return sbx_manager.get_sandbox(state)
    
    @staticmethod
    async def wait(duration: float, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """等待指定时间"""
        log_index = await SandboxBaseTool._add_log(state, f"⏳ 等待 {duration} 秒", config)
        
        try:
            state, sandbox = SandboxBaseTool._get_sandbox(state)
            sandbox.wait(int(duration * 1000))  # 转换为毫秒
            
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"已等待 {duration} 秒"
        except Exception as e:
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"等待操作失败: {str(e)}"

class SandboxMouseTool(SandboxBaseTool):
    """统一的沙箱鼠标控制工具类"""
    
    @staticmethod
    async def move_mouse(x: int, y: int, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """移动鼠标到指定位置"""
        log_index = await SandboxBaseTool._add_log(state, f"🖱️ 移动鼠标到: ({x}, {y})", config)
        
        try:
            state, sandbox = SandboxBaseTool._get_sandbox(state)
            sandbox.move_mouse(x, y)
            
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"鼠标已移动到 ({x}, {y})"
        except Exception as e:
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"移动鼠标失败: {str(e)}"
    
    @staticmethod
    async def click_mouse(x: Optional[int], y: Optional[int], button: str, num_clicks: int,
                         state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """在当前或指定位置点击鼠标"""
        log_index = await SandboxBaseTool._add_log(
            state, 
            f"🖱️ {button}键点击{num_clicks}次" + (f" 在 ({x}, {y})" if x is not None and y is not None else ""),
            config
        )
        
        try:
            state, sandbox = SandboxBaseTool._get_sandbox(state)
            
            if num_clicks == 2:
                sandbox.double_click(x, y)
            else:
                for _ in range(num_clicks):
                    if button == "left":
                        sandbox.left_click(x, y)
                    elif button == "right":
                        sandbox.right_click(x, y)
                    elif button == "middle":
                        sandbox.middle_click(x, y)
            
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"完成{button}键点击{num_clicks}次"
        except Exception as e:
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"鼠标点击失败: {str(e)}"
    
    @staticmethod
    async def scroll_mouse(amount: int, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """滚动鼠标滚轮"""
        direction = "up" if amount > 0 else "down"
        log_index = await SandboxBaseTool._add_log(state, f"🖱️ 滚轮向{direction}滚动 {abs(amount)} 步", config)
        
        try:
            state, sandbox = SandboxBaseTool._get_sandbox(state)
            sandbox.scroll(direction, abs(amount))
            
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"滚轮已向{direction}滚动 {abs(amount)} 步"
        except Exception as e:
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"滚动失败: {str(e)}"
    
    @staticmethod
    async def drag_mouse(x: int, y: int, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """拖拽鼠标到指定位置"""
        log_index = await SandboxBaseTool._add_log(state, f"🖱️ 拖拽到: ({x}, {y})", config)
        
        try:
            state, sandbox = SandboxBaseTool._get_sandbox(state)
            # 获取当前鼠标位置
            current_x, current_y = sandbox.get_cursor_position()
            # 执行拖拽
            sandbox.drag((current_x, current_y), (x, y))
            
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"已拖拽到 ({x}, {y})"
        except Exception as e:
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"拖拽操作失败: {str(e)}"
    
    @staticmethod
    async def take_screenshot(state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """获取屏幕截图"""
        log_index = await SandboxBaseTool._add_log(state, "📸 获取屏幕截图", config)
        
        try:
            state, sandbox = SandboxBaseTool._get_sandbox(state)
            screenshot = sandbox.screenshot()
            
            # 保存截图
            import os
            import time
            
            screenshots_dir = "screenshots"
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)
                
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(screenshots_dir, f"screenshot_{timestamp}.png")
            
            with open(filename, "wb") as f:
                f.write(screenshot)
                
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"截图已保存到: {filename}"
        except Exception as e:
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"截图失败: {str(e)}"
    
    @staticmethod
    @tool("mouse", args_schema=MouseToolInput)
    async def mouse_tool(
        operation: str,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: Optional[str] = "left",
        num_clicks: Optional[int] = 1,
        amount: Optional[int] = None,
        state: Optional[AgentState] = None,
        special_config_param: Optional[RunnableConfig] = None
    ) -> Tuple[AgentState, str]:
        """
        统一的鼠标控制工具，支持以下操作：
        - move: 移动鼠标到指定位置
        - click: 在当前或指定位置点击鼠标
        - scroll: 滚动鼠标滚轮
        - drag: 拖拽鼠标到指定位置
        - screenshot: 获取屏幕截图
        """
        config = special_config_param or RunnableConfig()
        
        if operation == "move":
            if x is None or y is None:
                return state, "移动鼠标操作需要提供x和y坐标"
            return await SandboxMouseTool.move_mouse(x, y, state, config)
        
        elif operation == "click":
            return await SandboxMouseTool.click_mouse(x, y, button, num_clicks, state, config)
        
        elif operation == "scroll":
            if amount is None:
                return state, "滚动操作需要提供amount参数"
            return await SandboxMouseTool.scroll_mouse(amount, state, config)
        
        elif operation == "drag":
            if x is None or y is None:
                return state, "拖拽操作需要提供x和y坐标"
            return await SandboxMouseTool.drag_mouse(x, y, state, config)
        
        elif operation == "screenshot":
            return await SandboxMouseTool.take_screenshot(state, config)
        
        else:
            return state, f"不支持的鼠标操作: {operation}"

class SandboxKeyboardTool(SandboxBaseTool):
    """统一的沙箱键盘控制工具类"""
    
    @staticmethod
    async def type_text(text: str, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """输入文本"""
        log_index = await SandboxBaseTool._add_log(state, f"⌨️ 输入文本: {text}", config)
        
        try:
            state, sandbox = SandboxBaseTool._get_sandbox(state)
            sandbox.write(text)
            
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"已输入文本: {text}"
        except Exception as e:
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"文本输入失败: {str(e)}"
    
    @staticmethod
    async def press_key(key: str, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """按下指定按键"""
        log_index = await SandboxBaseTool._add_log(state, f"⌨️ 按下按键: {key}", config)
        
        try:
            state, sandbox = SandboxBaseTool._get_sandbox(state)
            
            if "+" in key:  # 组合键
                keys = key.split("+")
                sandbox.press(keys)
            else:
                sandbox.press(key)
            
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"已按下按键: {key}"
        except Exception as e:
            await SandboxBaseTool._complete_log(state, log_index, config)
            return state, f"按键操作失败: {str(e)}"
    
    @staticmethod
    @tool("keyboard", args_schema=KeyboardToolInput)
    async def keyboard_tool(
        operation: str,
        text: Optional[str] = None,
        key: Optional[str] = None,
        duration: Optional[float] = 0.5,
        state: Optional[AgentState] = None,
        special_config_param: Optional[RunnableConfig] = None
    ) -> Tuple[AgentState, str]:
        """
        统一的键盘控制工具，支持以下操作：
        - type_text: 输入文本
        - press_key: 按下指定按键
        - wait: 等待指定时间
        """
        config = special_config_param or RunnableConfig()
        
        if operation == "type_text":
            if text is None:
                return state, "输入文本操作需要提供text参数"
            return await SandboxKeyboardTool.type_text(text, state, config)
        
        elif operation == "press_key":
            if key is None:
                return state, "按键操作需要提供key参数"
            return await SandboxKeyboardTool.press_key(key, state, config)
        
        elif operation == "wait":
            return await SandboxBaseTool.wait(duration, state, config)
        
        else:
            return state, f"不支持的键盘操作: {operation}"

computer_use_mouse_tool = SandboxMouseTool.mouse_tool
computer_use_keyboard_tool = SandboxKeyboardTool.keyboard_tool

async def test_tools_invoke():
    """测试工具调用API"""
    print("开始测试计算机控制工具的工具调用API...")
    import traceback
    
    state = AgentState(
        copilotkit={"actions": []},
        messages=[],
        logs=[],
        e2b_sandbox_id="your_sandbox_id_here"
    )
    
    # 不再需要创建实例，直接使用静态方法
    # mouse_tool = SandboxMouseTool()
    # keyboard_tool = SandboxKeyboardTool()
    
    try:
        # 测试鼠标工具 - 移动鼠标
        print("\n1. 测试鼠标工具 - 移动鼠标:")
        move_result = await SandboxMouseTool.mouse_tool.ainvoke(
            {
            "operation":"move",
            "x":100,
            "y":100,
            "state":state
        })
        print(f"结果: {move_result}")
        
        # 测试鼠标工具 - 点击鼠标
        print("\n2. 测试鼠标工具 - 点击鼠标:")
        click_result = await SandboxMouseTool.mouse_tool.ainvoke(
            {
            "operation":"click",
            "x":100,
            "y":100,
            "button":"left",
            "num_clicks":1,
            "state":state
        })
        print(f"结果: {click_result}")
        
        # 测试鼠标工具 - 滚动鼠标
        print("\n3. 测试鼠标工具 - 滚动鼠标:")
        scroll_result = await SandboxMouseTool.mouse_tool.ainvoke(
            {
            "operation":"scroll",
            "amount":5,
            "state":state
        })
        print(f"结果: {scroll_result}")
        
        # 测试键盘工具 - 输入文本
        print("\n4. 测试键盘工具 - 输入文本:")
        type_result = await SandboxKeyboardTool.keyboard_tool.ainvoke(
            {
            "operation":"type_text",
            "text":"Hello, World!",
            "state":state
        })
        print(f"结果: {type_result}")
        
        # 测试键盘工具 - 按键
        print("\n5. 测试键盘工具 - 按键:")
        key_result = await SandboxKeyboardTool.keyboard_tool.ainvoke(
            {
            "operation":"press_key",
            "key":"enter",
            "state":state
        })
        print(f"结果: {key_result}")
        
        # 测试键盘工具 - 等待
        print("\n6. 测试键盘工具 - 等待:")
        wait_result = await SandboxKeyboardTool.keyboard_tool.ainvoke(
            {
            "operation":"wait",
            "duration":1.0,
            "state":state
        })
        print(f"结果: {wait_result}")
        
        # 测试鼠标工具 - 拖拽
        print("\n7. 测试鼠标工具 - 拖拽:")
        drag_result = await SandboxMouseTool.mouse_tool.ainvoke(
            {
            "operation":"drag",
            "x":200,
            "y":200,
            "state":state
        })
        print(f"结果: {drag_result}")
        
        # 测试鼠标工具 - 截图
        print("\n8. 测试鼠标工具 - 截图:")
        screenshot_result = await SandboxMouseTool.mouse_tool.ainvoke(
            {
            "operation":"screenshot",
            "state":state
        })
        print(f"结果: {screenshot_result}")
        
        print("\n所有工具调用API测试完成!")
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        traceback.print_exc()
        
    print("\n最终状态:")
    if hasattr(state, 'logs') and state.logs:
        for i, log in enumerate(state.logs):
            print(f"Log {i+1}: {log['message']} - 完成状态: {log['done']}")
    else:
        print("没有日志记录")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tools_invoke())
