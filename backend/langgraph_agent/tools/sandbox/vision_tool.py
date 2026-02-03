from copilotkit.langchain import copilotkit_emit_state

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union, Tuple
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool, InjectedToolArg
from typing_extensions import Annotated
from langgraph_agent.graph.state import AgentState
from langgraph_agent.tools.sandbox.manager import sbx_manager
from langgraph_agent.utils.message_utils import get_last_show_message_id

import base64
import mimetypes
import os

# 添加常见的图片MIME类型
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("image/jpeg", ".jpg")
mimetypes.add_type("image/jpeg", ".jpeg")
mimetypes.add_type("image/png", ".png")
mimetypes.add_type("image/gif", ".gif")

# 最大图片大小（10MB）
MAX_IMAGE_SIZE = 10 * 1024 * 1024

class SeeImageInput(BaseModel):
    file_path: str = Field(description="要查看的图片文件路径，相对于workspace目录")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")

class VisionToolInput(BaseModel):
    operation: str = Field(description="视觉操作类型，可选值: see_image")
    file_path: str = Field(description="要查看的图片文件路径，相对于workspace目录")
    state: Annotated[Optional[AgentState], InjectedToolArg] = Field(description="状态，由系统提供")


class SandboxVisionTool:
    """沙箱视觉工具类"""
    
    def __init__(self):
        """初始化沙箱视觉工具"""
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
    async def _get_sandbox(state: AgentState):
        """获取沙箱实例"""
        return await sbx_manager.get_sandbox_async(state)
    
    @staticmethod
    async def see_image(file_path: str, state: AgentState, config: RunnableConfig) -> Tuple[AgentState, str]:
        """查看图片文件"""
        log_index = await SandboxVisionTool._add_log(state, f"👁️ 查看图片: '{file_path}'", config)
        
        try:
            state, sandbox = await SandboxVisionTool._get_sandbox(state)
            
            # 检查文件是否存在
            if not await sandbox.files.exists(file_path):
                await SandboxVisionTool._complete_log(state, log_index, config)
                return state, f"图片文件 '{file_path}' 不存在"
            
            # 获取文件信息（检查文件大小）
            file_info = await sandbox.files.stat(file_path)
            if file_info.size > MAX_IMAGE_SIZE:
                await SandboxVisionTool._complete_log(state, log_index, config)
                return state, f"图片文件 '{file_path}' 太大({file_info.size / (1024*1024):.2f}MB)。最大允许大小为{MAX_IMAGE_SIZE / (1024*1024)}MB"
            
            # 读取图片文件内容
            image_bytes = await sandbox.files.read(file_path, encoding=None)
            
            # 转换为base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # 确定MIME类型
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type or not mime_type.startswith('image/'):
                # 如果mimetypes失败，根据扩展名进行基础回退
                ext = os.path.splitext(file_path)[1].lower()
                if ext == '.jpg' or ext == '.jpeg': mime_type = 'image/jpeg'
                elif ext == '.png': mime_type = 'image/png'
                elif ext == '.gif': mime_type = 'image/gif'
                elif ext == '.webp': mime_type = 'image/webp'
                else:
                    await SandboxVisionTool._complete_log(state, log_index, config)
                    return state, f"不支持的图片格式: '{file_path}'。支持的格式: JPG, PNG, GIF, WEBP"
            
            # 在state中存储图片信息
            # state["temporary_images"] = state.get("temporary_images", [])
            state["temporary_images"] = [] # 清空临时图片列表
            state["temporary_images"].append({
                "mime_type": mime_type,
                "base64": base64_image,
                "file_path": file_path
            })
            
            await SandboxVisionTool._complete_log(state, log_index, config)
            return state, f"成功加载图片 '{file_path}'，现在可以在上下文中看到它"
                
        except Exception as e:
            state["temporary_images"] = [] # 清空临时图片列表
            await SandboxVisionTool._complete_log(state, log_index, config)
            return state, f"查看图片失败: {str(e)}"
    
    @staticmethod
    @tool("vision", args_schema=VisionToolInput)
    async def vision_tool(
        operation: str,
        file_path: str,
        state: Optional[AgentState] = None,
        special_config_param: Optional[RunnableConfig] = None
    ) -> Tuple[AgentState, str]:
        """
        视觉操作工具，支持以下操作：
        - see_image: 查看图片文件
        """
        config = special_config_param or RunnableConfig()
        
        if operation == "see_image":
            if not file_path:
                return state, "查看图片操作需要提供file_path参数"
            return await SandboxVisionTool.see_image(file_path, state, config)
        else:
            return state, f"不支持的视觉操作: {operation}"

vision_tool = SandboxVisionTool.vision_tool

async def test_tools_invoke():
    """使用工具调用API测试工具函数"""
    print("开始测试沙箱视觉工具的工具调用API...")
    import traceback
    
    # 创建一个初始状态
    state = AgentState(
        copilotkit={
            "actions": []
        },
        messages=[],
        logs=[],  # 初始化 logs 为一个空列表
        e2b_sandbox_id="your_sandbox_id_here"  # 提供一个字符串作为 e2b_sandbox_id
    )
    
    try:
        # 测试视觉工具 - 查看图片
        print("\n1. 测试视觉工具 - 查看图片:")
        see_image_result = await SandboxVisionTool.vision_tool.ainvoke(
            {
                "operation": "see_image", 
                "file_path": "test_image.png", 
                "state": state
            }
        )
        print(f"结果: {see_image_result}")
        
        print("\n测试完成: 视觉工具测试成功!")
        
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
    
    if hasattr(state, 'images') and state.images:
        for i, image in enumerate(state.images):
            print(f"Image {i+1}: {image['file_path']} - MIME类型: {image['mime_type']}")
    else:
        print("没有图片记录")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_tools_invoke())
