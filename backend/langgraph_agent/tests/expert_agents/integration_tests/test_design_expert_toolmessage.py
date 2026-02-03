"""
集成测试：设计专家ToolMessage格式转换
"""
import os
import json
import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from langgraph_agent.graph.expert_agent import ExpertAgentManager
from langgraph_agent.graph.state import AgentState


class TestDesignExpertToolMessage:
    """测试设计专家的ToolMessage处理"""
    
    @pytest.mark.asyncio
    async def test_IT_DET_001_design_expert_image_response(self):
        """测试设计专家返回图片类型ToolMessage的处理"""
        print("\n" + "=" * 60)
        print("测试: 设计专家图片响应处理")
        print("=" * 60)
        
        # 创建ExpertAgentManager实例
        manager = ExpertAgentManager()
        
        # 模拟设计专家返回的ToolMessage
        mock_tool_message = ToolMessage(
            content="已成功生成'产品设计图'，创建了3张设计图",
            tool_call_id="design_task_123",
            additional_kwargs={
                "toolCalls": [{
                    "id": f"design_{datetime.now().timestamp()}",
                    "function": {
                        "name": "image",
                        "arguments": json.dumps([
                            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
                            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
                        ])
                    },
                    "type": "function"
                }],
                "name": "image"
            }
        )
        
        # 模拟远程图返回的结果
        mock_remote_result = {
            "messages": [
                AIMessage(content="开始生成设计图..."),
                mock_tool_message
            ]
        }
        
        # 创建测试状态
        test_state = {
            "agent_type": "design",
            "messages": [HumanMessage(content="生成产品设计图")],
            "expert_services": {
                "design": {
                    "url": "http://localhost:8005",
                    "graph_id": "design-expert-v1"
                }
            }
        }
        
        # Mock远程调用
        with patch.object(manager.remote_manager, 'get_remote_graph') as mock_get_remote:
            # 创建mock remote_graph
            mock_remote_graph = AsyncMock()
            
            # 模拟流式返回
            async def mock_astream(*args, **kwargs):
                # 返回包含ToolMessage的更新
                yield ("namespace", {"messages": [mock_tool_message]})
            
            mock_remote_graph.astream = mock_astream
            mock_get_remote.return_value = mock_remote_graph
            
            # 创建config
            config = RunnableConfig(configurable={"run_id": "test_run_123"})
            
            # 执行专家节点
            result = await manager.expert_agent_node(test_state, config)
            
            # 验证结果
            assert result.update is not None
            assert "messages" in result.update
            
            # 查找转换后的ToolMessage
            tool_message_found = False
            for msg in result.update["messages"]:
                if isinstance(msg, dict) and msg.get("type") == "tool":
                    tool_message_found = True
                    
                    # 验证格式转换
                    assert "toolCalls" in msg, "toolCalls应该在消息顶层"
                    assert "name" in msg, "name应该在消息顶层"
                    assert msg["name"] == "image", "name应该是'image'"
                    assert msg["role"] == "assistant", "role应该是'assistant'"
                    
                    # 验证toolCalls内容
                    tool_calls = msg["toolCalls"]
                    assert len(tool_calls) == 1
                    assert tool_calls[0]["function"]["name"] == "image"
                    
                    # 验证图片数据
                    arguments = json.loads(tool_calls[0]["function"]["arguments"])
                    assert len(arguments) == 3, "应该有3张图片"
                    
                    print(f"\n✅ ToolMessage转换成功:")
                    print(f"  - id: {msg.get('id')}")
                    print(f"  - name: {msg['name']}")
                    print(f"  - role: {msg['role']}")
                    print(f"  - content: {msg.get('content', '')[:50]}...")
                    print(f"  - 图片数量: {len(arguments)}")
            
            assert tool_message_found, "应该找到转换后的ToolMessage"
    
    @pytest.mark.asyncio
    async def test_IT_DET_002_design_expert_file_response(self):
        """测试设计专家返回文件类型ToolMessage的处理"""
        print("\n" + "=" * 60)
        print("测试: 设计专家文件响应处理")
        print("=" * 60)
        
        manager = ExpertAgentManager()
        
        # 模拟文件类型的ToolMessage
        mock_file_message = ToolMessage(
            content="已保存设计文件：design_preview.html",
            tool_call_id="file_task_456",
            additional_kwargs={
                "toolCalls": [{
                    "id": f"file_{datetime.now().timestamp()}",
                    "function": {
                        "name": "files",
                        "arguments": json.dumps({
                            "name": "design_preview.html",
                            "path": "designs/preview/design_preview.html",
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                    },
                    "type": "function"
                }],
                "name": "files"
            }
        )
        
        test_state = {
            "agent_type": "design",
            "messages": [HumanMessage(content="创建设计预览文件")],
            "expert_services": {
                "design": {
                    "url": "http://localhost:8005",
                    "graph_id": "design-expert-v1"
                }
            }
        }
        
        with patch.object(manager.remote_manager, 'get_remote_graph') as mock_get_remote:
            mock_remote_graph = AsyncMock()
            
            async def mock_astream(*args, **kwargs):
                yield ("namespace", {"messages": [mock_file_message]})
            
            mock_remote_graph.astream = mock_astream
            mock_get_remote.return_value = mock_remote_graph
            
            config = RunnableConfig(configurable={"run_id": "test_run_456"})
            result = await manager.expert_agent_node(test_state, config)
            
            # 验证文件类型的ToolMessage
            file_message_found = False
            for msg in result.update["messages"]:
                if isinstance(msg, dict) and msg.get("name") == "files":
                    file_message_found = True
                    
                    assert "toolCalls" in msg
                    tool_calls = msg["toolCalls"]
                    assert tool_calls[0]["function"]["name"] == "files"
                    
                    # 验证文件信息
                    file_info = json.loads(tool_calls[0]["function"]["arguments"])
                    assert file_info["name"] == "design_preview.html"
                    assert "path" in file_info
                    assert "date" in file_info
                    
                    print(f"\n✅ 文件类型ToolMessage转换成功:")
                    print(f"  - name: {msg['name']}")
                    print(f"  - 文件名: {file_info['name']}")
                    print(f"  - 文件路径: {file_info['path']}")
            
            assert file_message_found, "应该找到文件类型的ToolMessage"
    
    @pytest.mark.asyncio
    async def test_IT_DET_003_mixed_messages_with_toolmessage(self):
        """测试混合消息类型（包含ToolMessage）的处理"""
        print("\n" + "=" * 60)
        print("测试: 混合消息类型处理")
        print("=" * 60)
        
        manager = ExpertAgentManager()
        
        # 创建混合消息
        mock_tool_msg = ToolMessage(
            content="设计完成",
            tool_call_id="mixed_task",
            additional_kwargs={
                "toolCalls": [{
                    "id": "tool_789",
                    "function": {
                        "name": "image",
                        "arguments": json.dumps(["base64_image_data"])
                    },
                    "type": "function"
                }],
                "name": "image"
            }
        )
        
        test_state = {
            "agent_type": "design",
            "messages": [HumanMessage(content="设计请求")],
            "expert_services": {
                "design": {
                    "url": "http://localhost:8005",
                    "graph_id": "design-expert-v1"
                }
            }
        }
        
        with patch.object(manager.remote_manager, 'get_remote_graph') as mock_get_remote:
            mock_remote_graph = AsyncMock()
            
            async def mock_astream(*args, **kwargs):
                # 返回混合消息
                yield ("namespace", {
                    "messages": [
                        AIMessage(content="开始处理..."),
                        mock_tool_msg,
                        AIMessage(content="处理完成")
                    ]
                })
            
            mock_remote_graph.astream = mock_astream
            mock_get_remote.return_value = mock_remote_graph
            
            config = RunnableConfig(configurable={"run_id": "test_run_789"})
            result = await manager.expert_agent_node(test_state, config)
            
            # 统计各类消息
            ai_count = 0
            tool_count = 0
            
            for msg in result.update["messages"]:
                if isinstance(msg, AIMessage):
                    ai_count += 1
                elif isinstance(msg, dict) and msg.get("type") == "tool":
                    tool_count += 1
            
            print(f"\n消息统计:")
            print(f"  - AIMessage数量: {ai_count}")
            print(f"  - 转换后的ToolMessage数量: {tool_count}")
            
            assert ai_count == 2, "应该有2条AIMessage"
            assert tool_count == 1, "应该有1条转换后的ToolMessage"
            
            print("\n✅ 混合消息处理成功！")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])