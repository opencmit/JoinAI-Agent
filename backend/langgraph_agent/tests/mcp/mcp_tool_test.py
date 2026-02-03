"""
Agent Graph 测试模块

包含各种测试函数，用于验证 AgentGraph 的功能
"""

import asyncio
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph_agent.graph.graph import AgentGraph
from langgraph_agent.graph.state import AgentState


async def test_llm_parameter_extraction():
    """测试LLM参数自动提取功能"""
    print("=== 测试LLM参数自动提取功能 ===")
    
    # 模拟前端传递的数据格式（普通工具）
    test_mcp_tools = [
        {
            "tool_id": "calculator",
            "name": "计算器",
            "desc": "执行数学计算，支持加减乘除等基本运算",
            "arguments": [{
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式，如 '2+3*5'"
                    },
                    "precision": {
                        "type": "integer", 
                        "description": "计算精度（小数位数）",
                        "default": 2
                    }
                },
                "required": ["expression"]
            }],
            "type": "normal"
        },
        {
            "tool_id": "weather_api",
            "name": "天气查询",
            "desc": "查询指定城市的天气信息",
            "arguments": [{
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    },
                    "days": {
                        "type": "integer",
                        "description": "查询天数（1-7天）",
                        "default": 1
                    }
                },
                "required": ["city"]
            }],
            "type": "normal"
        }
    ]
    
    # 创建包含MCP工具的状态
    initial_state = AgentState(
        messages=[HumanMessage(content="请帮我计算 (果2+3)*5-8 的结")],
        mcp_tools=test_mcp_tools,
        max_iterations=3,
        temporary_message_content_list=[],
        iteration_count=0,
        logs=[],
        e2b_sandbox_id="test",
        copilotkit={"actions": []},
        temporary_images=[],
        structure_tool_results={},
        completed=False,
        model="qwen2.5"
    )
    
    print(f"测试查询: {initial_state['messages'][0].content}")
    print(f"可用MCP工具:")
    for tool in test_mcp_tools:
        print(f"  - {tool['name']}: {tool['desc']}")
    
    # 测试AgentGraph处理
    print(f"\n测试AgentGraph LLM参数提取:")
    agent = AgentGraph()
    
    # 创建模拟的LLM客户端
    # mock_llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key="test")
    
    try:
        # 测试MCP工具转换（带LLM）
        mcp_tools = agent.mcp_tools_manager.get_mcp_tools_from_state(initial_state)
        
        print(f"转换后的MCP工具:")
        for tool in mcp_tools:
            tool_type = getattr(tool, 'tool_type', 'unknown')
            has_llm = hasattr(tool, 'llm_client') and getattr(tool, 'llm_client') is not None
            print(f"  - {tool.name} (类型: {tool_type}, LLM参数提取: {has_llm})")
            
            # 测试工具的参数schema
            if hasattr(tool, 'args_schema'):
                schema = tool.args_schema
                print(f"    参数schema: {schema.__annotations__}")
        
        print(f"\n✅ LLM参数提取功能测试完成")
        return len(mcp_tools) == len(test_mcp_tools)
        
    except Exception as e:
        print(f"❌ LLM参数提取测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_knowledge_base_mcp_tool():
    """测试知识库类型的MCP工具"""
    print("=== 测试知识库MCP工具 ===")
    
    # 模拟知识库工具数据
    knowledge_mcp_tool = {
        "tool_id": "17ba836a79e44dd9a211de926c84b870",
        "name": "一加手机知识库",
        "desc": "搜索一加手机相关信息",
        "type": "knowledge",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询内容"
                },
                "limit": {
                    "type": "integer",
                    "description": "返回结果数量限制",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
    
    # 创建包含知识库工具的状态
    initial_state = AgentState(
        messages=[HumanMessage(content="一加11系列手机有哪些配置特点？")],
        mcp_tools=[knowledge_mcp_tool],
        max_iterations=3,
        temporary_message_content_list=[],
        iteration_count=0,
        logs=[],
        e2b_sandbox_id="test",
        copilotkit={"actions": []},
        temporary_images=[],
        structure_tool_results={},
        completed=False,
        model="qwen2.5-32b-instruct"
    )
    
    print(f"测试查询: {initial_state['messages'][0].content}")
    print(f"知识库工具信息:")
    print(f"  - 名称: {knowledge_mcp_tool['name']}")
    print(f"  - 描述: {knowledge_mcp_tool['desc']}")
    print(f"  - 类型: {knowledge_mcp_tool['type']}")
    print(f"  - 工具ID: {knowledge_mcp_tool['tool_id']}")
    
    # 测试AgentGraph处理知识库工具
    print(f"\n测试AgentGraph知识库工具转换:")
    agent = AgentGraph()
    
    # 创建模拟的LLM客户端
    mock_llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key="test")
    
    try:
        # 测试知识库工具转换
        mcp_tools = agent._get_mcp_tools_from_state(initial_state, mock_llm)
        
        print(f"转换后的知识库工具:")
        for tool in mcp_tools:
            tool_type = getattr(tool, 'tool_type', 'unknown')
            print(f"  - {tool.name} (类型: {tool_type})")
            print(f"    工具ID: {getattr(tool, 'tool_id', 'unknown')}")
            print(f"    描述: {tool.description}")
            
            # 检查知识库工具的特殊属性
            if tool_type == "knowledge":
                print(f"    ✓ 知识库工具保持原有参数格式")
                if hasattr(tool, 'args_schema'):
                    schema = tool.args_schema
                    print(f"    参数schema: {schema.__annotations__}")
            
        # 验证工具转换结果
        if len(mcp_tools) == 1:
            knowledge_tool = mcp_tools[0]
            if (getattr(knowledge_tool, 'tool_type', None) == 'knowledge' and 
                knowledge_tool.name == "一加手机知识库"):
                print(f"\n✅ 知识库MCP工具转换成功")
                return True
            else:
                print(f"\n❌ 知识库工具转换后属性不正确")
                return False
        else:
            print(f"\n❌ 知识库工具转换数量不正确，期望1个，实际{len(mcp_tools)}个")
            return False
        
    except Exception as e:
        print(f"❌ 知识库工具测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_knowledge_base_workflow():
    """测试完整的知识库工作流"""
    print("=== 测试知识库工作流 ===")

    # 模拟知识库工具数据
    knowledge_mcp_tool = {
        "tool_id": "17ba836a79e44dd9a211de926c84b870",
        "name": "一加手机知识库",
        "desc": "搜索一加手机相关信息",
        "type": "knowledge",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "搜索查询内容"
                }
            },
            "required": ["query"]
        }
    }

    # 创建初始状态
    initial_state = AgentState(
        messages=[
            HumanMessage(content="请帮我查询一下知识库有那些信息")
        ],
        mcp_tools=[knowledge_mcp_tool],
        model="qwen2.5-32b-instruct"
    )

    # 创建 AgentGraph 实例
    agent = AgentGraph()

    try:
        # 执行工作流
        print("\n执行知识库工作流...")
        print(f"用户查询: {initial_state['messages'][0].content}")
        print(f"可用知识库: {knowledge_mcp_tool['name']}")
        
        result = await agent.graph.ainvoke(initial_state)

        # 检查结果
        print("\n知识库工作流执行结果:")
        for i, msg in enumerate(result["messages"]):
            msg_type = type(msg).__name__
            content_preview = msg.content[:200] if len(str(msg.content)) > 200 else msg.content
            print(f"{i + 1}. {msg_type}: {content_preview}...")
            
            # 检查是否有工具调用
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tc in msg.tool_calls:
                    print(f"   工具调用: {tc['name']} - {tc.get('args', {})}")

        print("✅ 知识库工作流测试完成")

    except Exception as e:
        print(f"❌ 知识库工作流测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_mixed_mcp_tools():
    """测试混合类型的MCP工具（普通工具 + 知识库工具）"""
    print("=== 测试混合类型MCP工具 ===")
    
    # 混合工具：普通工具 + 知识库工具
    mixed_mcp_tools = [
        {
            "tool_id": "calculator",
            "name": "计算器",
            "desc": "执行数学计算",
            "type": "normal",
            "arguments": [{
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式"
                    }
                },
                "required": ["expression"]
            }]
        },
        {
            "tool_id": "17ba836a79e44dd9a211de926c84b870",
            "name": "一加手机知识库",
            "desc": "搜索一加手机相关信息",
            "type": "knowledge",
            "argumens": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询内容"
                    }
                },
                "required": ["query"]
            }
        }
    ]
    
    # 创建初始状态
    initial_state = AgentState(
        messages=[
            HumanMessage(content="总结一下知识库中的文件")
        ],
        mcp_tools=mixed_mcp_tools,
        model="qwen2.5-32b-instruct"
    )
    
    print(f"测试查询: {initial_state['messages'][0].content}")
    print(f"可用工具:")
    for tool in mixed_mcp_tools:
        print(f"  - {tool['name']} (类型: {tool['type']})")
    
    # 测试工具转换
    agent = AgentGraph()
    # mock_llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key="test")
    
    try:
        # mcp_tools = agent._get_mcp_tools_from_state(initial_state, mock_llm)
        mcp_tools = agent._get_mcp_tools_from_state(initial_state)
        
        print(f"\n转换后的混合工具:")
        normal_count = 0
        knowledge_count = 0
        
        for tool in mcp_tools:
            tool_type = getattr(tool, 'tool_type', 'unknown')
            has_llm = hasattr(tool, 'llm_client') and getattr(tool, 'llm_client') is not None
            print(f"  - {tool.name} (类型: {tool_type}, LLM提取: {has_llm})")
            
            if tool_type == "normal":
                normal_count += 1
            elif tool_type == "knowledge":
                knowledge_count += 1
        
        print(f"\n工具统计:")
        print(f"  普通工具: {normal_count} 个")
        print(f"  知识库工具: {knowledge_count} 个")
        print(f"  总计: {len(mcp_tools)} 个")
        
        if normal_count == 1 and knowledge_count == 1:
            print(f"\n✅ 混合MCP工具转换成功")
            return True
        else:
            print(f"\n❌ 混合工具转换数量不正确")
            return False
            
    except Exception as e:
        print(f"❌ 混合工具测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_with_files_tool():
    """测试 Agent 工作流中的文件工具功能"""
    print("开始测试 Agent 工作流中的文件工具...")

    # 创建初始状态
    initial_state = AgentState(
        # input="请创建一个名为test_agent.txt的文件，内容为'Hello from Agent'",
        # max_iterations=5
        messages=[
            # HumanMessage(content="请创建一个名为test_agent.txt的文件，内容为'Hello from Agent'")
            # HumanMessage(content="使用ask向我提问我的生日")
            HumanMessage(content="使用web搜索金毛犬")
        ],
        model="Qwen2.5-14B-Instruct"
    )

    # 创建 AgentGraph 实例
    agent = AgentGraph()

    try:
        # 执行工作流
        print("\n执行工作流...")
        result = await agent.graph.ainvoke(initial_state)

        # 检查结果
        print("\n工作流执行结果:")
        for i, msg in enumerate(result["messages"]):
            print(f"{i + 1}. {type(msg).__name__}: {msg.content}")

        # 检查日志
        print("\n操作日志:")
        if result.get("logs"):
            for log in result["logs"]:
                print(f"- {log['message']} (完成: {log['done']})")
        else:
            print("没有日志记录")

        # 验证文件是否创建成功
        print("\n验证文件操作结果...")
        # 使用文件工具直接检查文件是否存在
        from langgraph_agent.tools import files_tool
        _, file_content = await files_tool.ainvoke({
            "operation": "read",
            "path": "test_agent.txt",
            "state": result
        })

        if "Hello from Agent" in file_content:
            print("✅ 测试成功: 文件创建并写入内容正确")
        else:
            print(f"❌ 测试失败: 文件内容不符合预期\n实际内容: {file_content}")

    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


async def run_all_tests():
    """运行所有测试"""
    print("开始运行所有测试...")
    print("="*50)
    
    tests = [
        ("LLM参数提取功能", test_llm_parameter_extraction),
        ("知识库MCP工具", test_knowledge_base_mcp_tool),
        ("知识库工作流", test_knowledge_base_workflow),
        ("混合MCP工具", test_mixed_mcp_tools),
        # ("Agent文件工具", test_agent_with_files_tool),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func.__name__ in ["test_knowledge_base_workflow", "test_agent_with_files_tool"]:
                # 这些测试没有返回值，只打印结果
                await test_func()
                results[test_name] = "完成"
            else:
                # 这些测试有返回值
                result = await test_func()
                results[test_name] = "成功" if result else "失败"
        except Exception as e:
            print(f"测试 {test_name} 发生异常: {str(e)}")
            results[test_name] = "异常"
    
    print(f"\n{'='*20} 测试总结 {'='*20}")
    for test_name, result in results.items():
        status_icon = "✅" if result in ["成功", "完成"] else "❌"
        print(f"{status_icon} {test_name}: {result}")


if __name__ == "__main__":
    # 可以选择运行单个测试或所有测试
    
    # 运行所有测试
    asyncio.run(test_llm_parameter_extraction())
    
    # 或者运行特定测试
    # asyncio.run(test_knowledge_base_mcp_tool())
    # asyncio.run(test_knowledge_base_workflow())