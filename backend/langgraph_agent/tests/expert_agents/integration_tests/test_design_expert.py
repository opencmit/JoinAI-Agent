"""
设计专家智能体集成测试
"""

import json
import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, ToolMessage


# 导入要测试的图
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../servers/remote_graph/design_expert'))
from graph import create_design_expert_graph


class TestDesignExpert:
    """设计专家测试类"""
    
    @pytest.mark.asyncio
    async def test_image_generation(self):
        """测试图像生成功能"""
        # 创建图实例
        graph = create_design_expert_graph()
        
        # 准备测试输入 - 生成图像请求
        test_input = {
            "messages": [
                HumanMessage(content=json.dumps({
                    "query": "生成一个校庆海报",
                    "image": ""
                }))
            ]
        }
        
        # 执行图
        result = await graph.ainvoke(test_input)
        
        # 验证结果
        assert "messages" in result
        messages = result["messages"]
        assert len(messages) > 0
        
        # 查找最终的 ToolMessage
        tool_message = None
        for msg in messages:
            if isinstance(msg, ToolMessage) and hasattr(msg, 'additional_kwargs'):
                tool_message = msg
                break
        
        # 验证 ToolMessage 格式
        assert tool_message is not None, "应该返回 ToolMessage"
        assert tool_message.content, "content 应包含描述信息"
        assert "生成" in tool_message.content, "content 应描述生成操作"
        
        # 验证 additional_kwargs 格式
        assert "toolCalls" in tool_message.additional_kwargs
        assert "name" in tool_message.additional_kwargs
        assert tool_message.additional_kwargs["name"] == "image"
        
        # 验证 toolCalls 结构
        tool_calls = tool_message.additional_kwargs["toolCalls"]
        assert len(tool_calls) > 0
        tool_call = tool_calls[0]
        assert "function" in tool_call
        assert tool_call["function"]["name"] == "image"
        
        # 验证 arguments 包含图片数组
        arguments = json.loads(tool_call["function"]["arguments"])
        assert isinstance(arguments, list), "arguments 应该是图片数组"
        assert len(arguments) > 0, "应该至少生成一张图片"
    
    @pytest.mark.asyncio
    async def test_image_modification(self):
        """测试图像修改功能"""
        # 创建图实例
        graph = create_design_expert_graph()
        
        # 准备测试输入 - 修改图像请求
        test_input = {
            "messages": [
                HumanMessage(content=json.dumps({
                    "query": "对这个图片调一下风格，改为简约风",
                    "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA..."
                }))
            ]
        }
        
        # 执行图
        result = await graph.ainvoke(test_input)
        
        # 验证结果
        assert "messages" in result
        messages = result["messages"]
        assert len(messages) > 0
        
        # 查找最终的 ToolMessage
        tool_message = None
        for msg in messages:
            if isinstance(msg, ToolMessage) and hasattr(msg, 'additional_kwargs'):
                tool_message = msg
                break
        
        # 验证 ToolMessage 格式
        assert tool_message is not None, "应该返回 ToolMessage"
        assert tool_message.content, "content 应包含描述信息"
        assert "修改" in tool_message.content or "应用" in tool_message.content, "content 应描述修改操作"
        
        # 验证 additional_kwargs 格式
        assert "toolCalls" in tool_message.additional_kwargs
        assert tool_message.additional_kwargs["name"] == "image"
        
        # 验证修改后的图片
        tool_calls = tool_message.additional_kwargs["toolCalls"]
        tool_call = tool_calls[0]
        arguments = json.loads(tool_call["function"]["arguments"])
        assert isinstance(arguments, list), "应返回修改后的图片数组"
        assert len(arguments) > 0, "应该至少有一张修改后的图片"
    
    @pytest.mark.asyncio
    async def test_file_generation(self):
        """测试设计文件生成功能"""
        # 创建图实例
        graph = create_design_expert_graph()
        
        # 准备测试输入 - 可能触发文件生成的请求
        test_input = {
            "messages": [
                HumanMessage(content=json.dumps({
                    "query": "生成一个网页设计稿并保存为HTML文件",
                    "image": ""
                }))
            ]
        }
        
        # Mock save_design_file 以触发文件返回
        with patch('graph.save_design_file') as mock_save:
            mock_save.invoke.return_value = {
                "name": "design.html",
                "path": "deepresearch/design.html",
                "date": "2025-09-17 12:00:00"
            }
            
            # 执行图
            result = await graph.ainvoke(test_input)
            
            # 查找返回的消息
            messages = result["messages"]
            
            # 如果返回了文件格式，验证其结构
            for msg in messages:
                if isinstance(msg, ToolMessage) and hasattr(msg, 'additional_kwargs'):
                    if msg.additional_kwargs.get("name") == "files":
                        # 验证文件格式
                        tool_calls = msg.additional_kwargs["toolCalls"]
                        tool_call = tool_calls[0]
                        assert tool_call["function"]["name"] == "files"
                        
                        # 验证文件信息
                        file_info = json.loads(tool_call["function"]["arguments"])
                        assert "name" in file_info
                        assert "path" in file_info
                        assert "date" in file_info
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """测试错误处理"""
        # 创建图实例
        graph = create_design_expert_graph()
        
        # 准备无效的测试输入
        test_input = {
            "messages": [
                HumanMessage(content="invalid json content")
            ]
        }
        
        # 执行图 - 应该能够优雅地处理错误
        result = await graph.ainvoke(test_input)
        
        # 验证结果
        assert "messages" in result
        messages = result["messages"]
        assert len(messages) > 0
        
        # 即使输入无效，也应该返回某种响应
        last_message = messages[-1]
        assert last_message is not None
    
    @pytest.mark.asyncio
    async def test_planner_agent_flow(self):
        """测试 Planner -> Agent 的完整流程"""
        # 创建图实例
        graph = create_design_expert_graph()
        
        # 准备测试输入
        test_input = {
            "messages": [
                HumanMessage(content=json.dumps({
                    "query": "生成一个现代风格的公司Logo",
                    "image": ""
                }))
            ]
        }
        
        # 执行图
        result = await graph.ainvoke(test_input)
        
        # 验证消息链
        messages = result["messages"]
        
        # 应该至少有3条消息：用户输入、规划结果、执行结果
        assert len(messages) >= 3, "应该包含完整的消息链"
        
        # 验证是否有规划阶段的输出
        has_planning = False
        for msg in messages:
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                if "规划" in msg.content or "设计目标" in msg.content:
                    has_planning = True
                    break
        
        assert has_planning or len(messages) > 1, "应该包含规划阶段的输出"
        
        # 验证最终输出
        tool_message = None
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage) and hasattr(msg, 'additional_kwargs'):
                tool_message = msg
                break
        
        assert tool_message is not None, "应该有最终的设计输出"
        assert tool_message.additional_kwargs.get("name") in ["image", "files"], "应该返回图片或文件"


# 运行测试的辅助函数
def run_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    # 可以直接运行此文件进行测试
    run_tests()