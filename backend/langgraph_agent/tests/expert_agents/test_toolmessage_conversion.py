"""
测试ToolMessage格式转换功能
"""
import json
import asyncio
from datetime import datetime
from langchain_core.messages import ToolMessage, AIMessage, HumanMessage
from langgraph_agent.graph.expert_agent import ExpertRemoteGraphManager

def create_test_tool_message():
    """创建测试用的ToolMessage - 图片类型"""
    return ToolMessage(
        content="已成功生成设计图，共3张",
        tool_call_id="design_task",
        additional_kwargs={
            "toolCalls": [{
                "id": f"design_{datetime.now().timestamp()}",
                "function": {
                    "name": "image",
                    "arguments": json.dumps([
                        "base64_image_1_data_here",
                        "base64_image_2_data_here",
                        "base64_image_3_data_here"
                    ])
                },
                "type": "function"
            }],
            "name": "image"
        }
    )

def create_test_file_message():
    """创建测试用的ToolMessage - 文件类型"""
    return ToolMessage(
        content="已保存设计文件",
        tool_call_id="file_task",
        additional_kwargs={
            "toolCalls": [{
                "id": f"file_{datetime.now().timestamp()}",
                "function": {
                    "name": "files",
                    "arguments": json.dumps({
                        "name": "画图.html",
                        "path": "deepresearch/画图.html",
                        "date": "2025-08-19 00:00:00"
                    })
                },
                "type": "function"
            }],
            "name": "files"
        }
    )

def test_toolmessage_conversion():
    """测试ToolMessage转换功能"""
    print("=" * 60)
    print("测试ToolMessage格式转换")
    print("=" * 60)
    
    # 创建管理器实例
    manager = ExpertRemoteGraphManager()
    
    # 测试1: 图片类型的ToolMessage
    print("\n测试1: 图片类型ToolMessage转换")
    print("-" * 40)
    
    image_msg = create_test_tool_message()
    result = {
        "messages": [
            HumanMessage(content="生成一个设计图"),
            image_msg,
            AIMessage(content="设计已完成")
        ]
    }
    
    state_update = manager._process_expert_result(result, {})
    
    print(f"原始消息数量: {len(result['messages'])}")
    print(f"处理后消息数量: {len(state_update['messages'])}")
    
    # 查找转换后的ToolMessage
    for msg in state_update['messages']:
        if isinstance(msg, dict) and msg.get('type') == 'tool':
            print(f"\n✅ ToolMessage已转换:")
            print(f"  - id: {msg['id']}")
            print(f"  - role: {msg['role']}")
            print(f"  - name: {msg['name']}")
            print(f"  - content: {msg['content']}")
            print(f"  - toolCalls存在: {'toolCalls' in msg}")
            if 'toolCalls' in msg:
                tool_call = msg['toolCalls'][0]
                print(f"  - function.name: {tool_call['function']['name']}")
                args = json.loads(tool_call['function']['arguments'])
                print(f"  - 图片数量: {len(args) if isinstance(args, list) else 'N/A'}")
        elif isinstance(msg, ToolMessage):
            # 检查是否有未转换的ToolMessage
            if msg.additional_kwargs and 'toolCalls' in msg.additional_kwargs:
                print(f"\n❌ 发现未转换的ToolMessage")
                print(f"  - content: {msg.content}")
                print(f"  - additional_kwargs: {list(msg.additional_kwargs.keys())}")
    
    # 测试2: 文件类型的ToolMessage
    print("\n\n测试2: 文件类型ToolMessage转换")
    print("-" * 40)
    
    file_msg = create_test_file_message()
    result2 = {
        "messages": [
            HumanMessage(content="保存文件"),
            file_msg
        ]
    }
    
    state_update2 = manager._process_expert_result(result2, {})
    
    print(f"原始消息数量: {len(result2['messages'])}")
    print(f"处理后消息数量: {len(state_update2['messages'])}")
    
    for msg in state_update2['messages']:
        if isinstance(msg, dict) and msg.get('type') == 'tool':
            print(f"\n✅ ToolMessage已转换:")
            print(f"  - id: {msg['id']}")
            print(f"  - role: {msg['role']}")
            print(f"  - name: {msg['name']}")
            print(f"  - content: {msg['content']}")
            if 'toolCalls' in msg:
                tool_call = msg['toolCalls'][0]
                print(f"  - function.name: {tool_call['function']['name']}")
                args = json.loads(tool_call['function']['arguments'])
                if isinstance(args, dict):
                    print(f"  - 文件名: {args.get('name')}")
                    print(f"  - 文件路径: {args.get('path')}")
    
    # 测试3: 混合消息类型
    print("\n\n测试3: 混合消息类型处理")
    print("-" * 40)
    
    mixed_result = {
        "messages": [
            HumanMessage(content="用户请求"),
            AIMessage(content="AI响应"),
            create_test_tool_message(),
            AIMessage(content="完成"),
            create_test_file_message()
        ]
    }
    
    state_update3 = manager._process_expert_result(mixed_result, {})
    
    print(f"原始消息数量: {len(mixed_result['messages'])}")
    print(f"处理后消息数量: {len(state_update3['messages'])}")
    
    tool_msg_count = 0
    ai_msg_count = 0
    human_msg_count = 0
    
    for msg in state_update3['messages']:
        if isinstance(msg, dict) and msg.get('type') == 'tool':
            tool_msg_count += 1
        elif isinstance(msg, AIMessage) or (isinstance(msg, dict) and msg.get('type') == 'ai'):
            ai_msg_count += 1
        elif isinstance(msg, HumanMessage) or (isinstance(msg, dict) and msg.get('type') == 'human'):
            human_msg_count += 1
    
    print(f"\n消息类型统计:")
    print(f"  - HumanMessage: {human_msg_count}")
    print(f"  - AIMessage: {ai_msg_count}")
    print(f"  - ToolMessage (已转换): {tool_msg_count}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_toolmessage_conversion()