#!/usr/bin/env python3
"""
A2A智能体功能测试脚本
模拟AgentState的"a2a_agents"场景，测试A2A智能体功能
"""

import asyncio
import json
import sys
import os
import datetime
from typing import List, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from langgraph_agent.graph.state import AgentState, create_initial_state
from langgraph_agent.graph import AgentGraph
from langgraph_agent.graph.a2a_agent import A2AHttpClient, A2AAgentInfo, get_a2a_agents_from_state

def print_header(title: str):
    """打印标题"""
    print("=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80)

def print_section(title: str):
    """打印章节标题"""
    print("\n" + "-" * 60)
    print(f" {title} ")
    print("-" * 60)

def print_message_history(result_state: AgentState, test_name: str):
    """打印所有messages的历史记录"""
    print(f"\n" + "="*80)
    print(f"📜 {test_name} - 完整Messages历史记录")
    print("="*80)
    
    messages = result_state.get('messages', [])
    if not messages:
        print("没有messages记录")
        return
    
    print(f"总messages数量: {len(messages)}")
    print("-" * 80)
    
    for i, message in enumerate(messages, 1):
        print(f"\n📨 Message {i}:")
        print(f"{'='*50}")
        
        # 获取消息类型
        msg_type = None
        if hasattr(message, '__class__'):
            msg_type = message.__class__.__name__
        else:
            msg_type = type(message).__name__
        
        print(f"类型 (Type): {msg_type}")
        
        # 获取消息内容
        content = None
        if hasattr(message, 'content'):
            content = message.content
        elif hasattr(message, 'additional_kwargs'):
            content = getattr(message, 'additional_kwargs', {})
        elif isinstance(message, dict):
            content = message.get('content', str(message))
        else:
            content = str(message)
        
        print(f"内容 (Content):")
        if isinstance(content, str):
            # 如果内容很长，进行适当的分割显示
            if len(content) > 1000:
                print(f"  {content[:500]}...")
                print(f"  [中间省略 {len(content)-1000} 个字符]")
                print(f"  ...{content[-500:]}")
            else:
                # 按行显示，每行前面加缩进
                lines = content.split('\n')
                for line in lines:
                    print(f"  {line}")
        else:
            print(f"  {content}")
        
        # 检查是否有工具调用
        if hasattr(message, 'tool_calls') and message.tool_calls:
            print(f"工具调用 (Tool Calls): {len(message.tool_calls)} 个")
            for j, tool_call in enumerate(message.tool_calls, 1):
                print(f"  工具 {j}: {tool_call.get('name', 'Unknown')}")
                if 'args' in tool_call:
                    print(f"    参数: {tool_call['args']}")
        
        # 检查是否有其他重要属性
        if hasattr(message, 'additional_kwargs') and message.additional_kwargs:
            print(f"额外信息 (Additional): {message.additional_kwargs}")
        
        print(f"{'='*50}")
    
    print(f"\n" + "="*80)
    print(f"📜 {test_name} - Messages历史记录结束")
    print("="*80)

def print_complete_agent_state(result_state: AgentState, test_name: str):
    """打印完整的AgentState内容"""
    print(f"\n" + "="*80)
    print(f"🔍 {test_name} - 完整AgentState内容")
    print("="*80)
    
    # 打印所有状态字段
    all_keys = result_state.keys() if hasattr(result_state, 'keys') else []
    print(f"AgentState字段总数: {len(all_keys)}")
    print("-" * 80)
    
    # 按字段逐一显示
    for key in sorted(all_keys):
        value = result_state.get(key)
        print(f"\n📋 字段: {key}")
        print(f"{'='*50}")
        
        if key == 'messages':
            # 消息字段特殊处理
            print(f"类型: {type(value).__name__}")
            print(f"数量: {len(value) if value else 0}")
            if value:
                print("消息概览:")
                for i, msg in enumerate(value):
                    msg_type = type(msg).__name__ if hasattr(msg, '__class__') else str(type(msg))
                    content_preview = ""
                    if hasattr(msg, 'content'):
                        content_preview = str(msg.content)[:100] + "..." if len(str(msg.content)) > 100 else str(msg.content)
                    print(f"  [{i+1}] {msg_type}: {content_preview}")
        elif key in ['a2a_agents', 'workflow_plan', 'execution_results']:
            # 结构化数据特殊处理
            print(f"类型: {type(value).__name__}")
            if value:
                print("内容:")
                try:
                    formatted_value = json.dumps(value, indent=2, ensure_ascii=False)
                    print(f"  {formatted_value}")
                except:
                    print(f"  {str(value)}")
            else:
                print("  [空]")
        else:
            # 普通字段
            print(f"类型: {type(value).__name__}")
            print(f"值: {value}")
        
        print(f"{'='*50}")
    
    # 重点关注关键字段
    print(f"\n" + "🎯 关键字段状态检查:")
    print("-" * 40)
    print(f"✅ completed: {result_state.get('completed', '未设置')}")
    print(f"🔄 iteration_count: {result_state.get('iteration_count', '未设置')}")
    print(f"❌ a2a_failure_count: {result_state.get('a2a_failure_count', '未设置')}")
    print(f"📝 current_step_index: {result_state.get('current_step_index', '未设置')}")
    print(f"🎭 workflow_type: {result_state.get('workflow_plan', {}).get('workflow_type', '未设置') if result_state.get('workflow_plan') else '未设置'}")
    print(f"📊 total_steps: {result_state.get('workflow_plan', {}).get('total_steps', '未设置') if result_state.get('workflow_plan') else '未设置'}")
    print(f"🚪 current_step_completed: {result_state.get('current_step_completed', '未设置')}")
    print(f"🤖 a2a_agents数量: {len(result_state.get('a2a_agents', []))}")
    
    print(f"\n" + "="*80)
    print(f"🔍 {test_name} - AgentState内容结束")
    print("="*80)

def create_test_agent_state(agent_id: str, name: str, desc: str, user_query: str, user_id: str) -> AgentState:
    """创建测试用的AgentState"""
    
    test_input = {
        "messages": [],
        "input": {
            "message": [{
                "type": "human",
                "content": user_query
            }],
            "a2a_agents": [{
                "agent_id": agent_id,
                "name": name,
                "desc": desc,
                "user_id": user_id
            }]
        },
        "model": "openai/gpt-4o-mini"
    }
    
    # 🔍 添加调试信息：打印输入数据
    print(f"🔍 创建测试AgentState - 输入数据:")
    print(f"    test_input: {test_input}")
    print(f"    a2a_agents in input: {test_input['input']['a2a_agents']}")
    
    result_state = create_initial_state(test_input)
    
    # 🔍 调试信息：检查创建后的结果
    print(f"🔍 创建后的AgentState - a2a_agents:")
    print(f"    result_state a2a_agents: {result_state.get('a2a_agents', [])}")
    
    return result_state

def create_empty_a2a_agent_state(user_query: str) -> AgentState:
    """创建a2a_agents为空的测试AgentState"""
    
    test_input = {
        "messages": [],
        "input": {
            "message": [{
                "type": "human",
                "content": user_query
            }],
            "a2a_agents": []  # 空的a2a_agents列表
        },
        "model": "openai/gpt-4o-mini"
    }
    
    return create_initial_state(test_input)

async def test_weather_agent_functionality():
    """测试weather-agent功能"""
    print_section("🌤️ Weather Agent 功能测试")
    
    # 创建AgentState
    agent_state = create_test_agent_state(
        agent_id="weather-agent",
        name="天气助手",
        desc="专业天气查询和预报服务，支持多城市天气数据查询，提供详细气象分析和生活建议",
        user_query="上海今天天气怎么样？",
        user_id="weather_user_001"
    )
    
    print(f"测试时间: {datetime.datetime.now()}")
    print(f"A2A服务: http://localhost:18585")
    print(f"智能体ID: weather-agent")
    print(f"智能体名称: 天气助手")
    print(f"用户查询: 上海今天天气怎么样？")
    
    # 设置A2A服务URL
    os.environ["A2A_BASE_URL"] = "http://localhost:18585"
    
    # 显示AgentState详情
    print(f"\n📋 AgentState详情:")
    print(f"  - A2A智能体数量: {len(agent_state.get('a2a_agents', []))}")
    print(f"  - A2A失败计数: {agent_state.get('a2a_failure_count', 0)}")
    print(f"  - Fallback设置: {agent_state.get('a2a_fallback_to_general', True)}")
    print(f"  - 任务完成状态: {agent_state.get('completed', False)}")
    
    # 🔍 添加调试信息：检查初始AgentState的a2a_agents详细内容
    print(f"\n🔍 初始AgentState的a2a_agents详细内容:")
    for i, agent in enumerate(agent_state.get('a2a_agents', [])):
        print(f"  智能体 {i+1}: {agent}")
        # 检查每个字段
        print(f"    - agent_id: {agent.get('agent_id', '缺失')}")
        print(f"    - name: {agent.get('name', '缺失')}")
        print(f"    - desc: {agent.get('desc', '缺失')}")
        print(f"    - user_id: {agent.get('user_id', '❌ 缺失！')}")
        print(f"    - 所有字段: {list(agent.keys())}")
    
    # 打印A2A智能体信息
    for agent in agent_state.get('a2a_agents', []):
        print(f"  - 智能体: {agent['name']} (ID: {agent['agent_id']})")
        print(f"    描述: {agent['desc']}")
        print(f"    用户ID: {agent.get('user_id', '未设置')}")
    
    # 创建AgentGraph并执行测试
    print(f"\n🚀 开始执行测试...")
    
    try:
        agent_graph = AgentGraph()
        config = {
            'configurable': {
                'model_name': 'openai/gpt-4o-mini',
                'session_id': f'weather_test_{int(datetime.datetime.now().timestamp())}'
            },
            'recursion_limit': 10
        }
        
        start_time = datetime.datetime.now()
        result_state = await agent_graph.ainvoke(agent_state, config)
        end_time = datetime.datetime.now()
        
        execution_time = end_time - start_time
        
        print(f"\n✅ 测试完成！")
        print(f"执行时间: {execution_time.total_seconds():.2f} 秒")
        print(f"迭代次数: {result_state.get('iteration_count', 0)}")
        print(f"A2A失败次数: {result_state.get('a2a_failure_count', 0)}")
        print(f"任务完成: {result_state.get('completed', False)}")
        
        # 显示最后消息
        messages = result_state.get('messages', [])
        if messages:
            last_msg = messages[-1]
            content = getattr(last_msg, 'content', str(last_msg))
            print(f"\n📝 最终回复:")
            print(f"  {content[:300]}..." if len(content) > 300 else f"  {content}")
        
        # 验证结果
        success = (
            result_state.get('completed', False) and
            result_state.get('iteration_count', 0) < 10 and
            execution_time.total_seconds() < 30
        )
        
        print(f"\n🎯 测试结果: {'✅ 通过' if success else '❌ 失败'}")
        
        # 打印完整的messages历史记录
        print_message_history(result_state, "Weather Agent 功能测试")
        
        # 打印完整的AgentState内容
        print_complete_agent_state(result_state, "Weather Agent 功能测试")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_data_analyst_functionality():
    """测试data-analyst功能"""
    print_section("📊 Data Analyst 功能测试")
    
    # 创建AgentState
    agent_state = create_test_agent_state(
        agent_id="data-analyst",
        name="数据分析师",
        desc="数据探索分析和质量评估，统计分析和假设检验，数据可视化和图表生成，商业洞察和趋势预测",
        user_query="我有一份销售数据，想做趋势分析，应该怎么做？",
        user_id="analyst_user_002"
    )
    
    print(f"测试时间: {datetime.datetime.now()}")
    print(f"A2A服务: http://localhost:18585")
    print(f"智能体ID: data-analyst")
    print(f"智能体名称: 数据分析师")
    print(f"用户查询: 我有一份销售数据，想做趋势分析，应该怎么做？")
    
    # 设置A2A服务URL
    os.environ["A2A_BASE_URL"] = "http://localhost:18585"
    
    # 显示AgentState详情
    print(f"\n📋 AgentState详情:")
    print(f"  - A2A智能体数量: {len(agent_state.get('a2a_agents', []))}")
    print(f"  - A2A失败计数: {agent_state.get('a2a_failure_count', 0)}")
    print(f"  - Fallback设置: {agent_state.get('a2a_fallback_to_general', True)}")
    print(f"  - 任务完成状态: {agent_state.get('completed', False)}")
    
    # 打印A2A智能体信息
    for agent in agent_state.get('a2a_agents', []):
        print(f"  - 智能体: {agent['name']} (ID: {agent['agent_id']})")
        print(f"    描述: {agent['desc']}")
        print(f"    用户ID: {agent.get('user_id', '未设置')}")
    
    # 创建AgentGraph并执行测试
    print(f"\n🚀 开始执行测试...")
    
    try:
        agent_graph = AgentGraph()
        config = {
            'configurable': {
                'model_name': 'openai/gpt-4o-mini',
                'session_id': f'data_analyst_test_{int(datetime.datetime.now().timestamp())}'
            },
            'recursion_limit': 10
        }
        
        start_time = datetime.datetime.now()
        result_state = await agent_graph.ainvoke(agent_state, config)
        end_time = datetime.datetime.now()
        
        execution_time = end_time - start_time
        
        print(f"\n✅ 测试完成！")
        print(f"执行时间: {execution_time.total_seconds():.2f} 秒")
        print(f"迭代次数: {result_state.get('iteration_count', 0)}")
        print(f"A2A失败次数: {result_state.get('a2a_failure_count', 0)}")
        print(f"任务完成: {result_state.get('completed', False)}")
        
        # 显示最后消息
        messages = result_state.get('messages', [])
        if messages:
            last_msg = messages[-1]
            content = getattr(last_msg, 'content', str(last_msg))
            print(f"\n📝 最终回复:")
            print(f"  {content[:300]}..." if len(content) > 300 else f"  {content}")
        
        # 验证结果
        success = (
            result_state.get('completed', False) and
            result_state.get('iteration_count', 0) < 10 and
            execution_time.total_seconds() < 30
        )
        
        print(f"\n🎯 测试结果: {'✅ 通过' if success else '❌ 失败'}")
        
        # 打印完整的messages历史记录
        print_message_history(result_state, "Data Analyst 功能测试")
        
        # 打印完整的AgentState内容
        print_complete_agent_state(result_state, "Data Analyst 功能测试")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_custom_agent_functionality():
    """测试自定义智能体功能"""
    print_section("🔧 自定义智能体功能测试")
    
    # 创建AgentState - 模拟用户提供的示例
    agent_state = create_test_agent_state(
        agent_id="123",
        name="123",
        desc="123",
        user_query="测试123智能体功能",
        user_id="custom_user_123"
    )
    
    print(f"测试时间: {datetime.datetime.now()}")
    print(f"A2A服务: http://localhost:18585")
    print(f"智能体ID: 123")
    print(f"智能体名称: 123")
    print(f"用户查询: 测试自定义智能体功能")
    
    # 设置A2A服务URL
    os.environ["A2A_BASE_URL"] = "http://localhost:18585"
    
    # 显示AgentState详情
    print(f"\n📋 AgentState详情:")
    print(f"  - A2A智能体数量: {len(agent_state.get('a2a_agents', []))}")
    print(f"  - A2A失败计数: {agent_state.get('a2a_failure_count', 0)}")
    print(f"  - Fallback设置: {agent_state.get('a2a_fallback_to_general', True)}")
    print(f"  - 任务完成状态: {agent_state.get('completed', False)}")
    
    # 打印A2A智能体信息
    for agent in agent_state.get('a2a_agents', []):
        print(f"  - 智能体: {agent['name']} (ID: {agent['agent_id']})")
        print(f"    描述: {agent['desc']}")
        print(f"    用户ID: {agent.get('user_id', '未设置')}")
    
    # 创建AgentGraph并执行测试
    print(f"\n🚀 开始执行测试...")
    print(f"⚠️  注意: 这个智能体可能不存在，预期会触发fallback机制")
    
    try:
        agent_graph = AgentGraph()
        config = {
            'configurable': {
                'model_name': 'openai/gpt-4o-mini',
                'session_id': f'custom_test_{int(datetime.datetime.now().timestamp())}'
            },
            'recursion_limit': 8  # 较小的限制用于测试fallback
        }
        
        start_time = datetime.datetime.now()
        result_state = await agent_graph.ainvoke(agent_state, config)
        end_time = datetime.datetime.now()
        
        execution_time = end_time - start_time
        
        print(f"\n✅ 测试完成！")
        print(f"执行时间: {execution_time.total_seconds():.2f} 秒")
        print(f"迭代次数: {result_state.get('iteration_count', 0)}")
        print(f"A2A失败次数: {result_state.get('a2a_failure_count', 0)}")
        print(f"任务完成: {result_state.get('completed', False)}")
        
        # 显示最后消息
        messages = result_state.get('messages', [])
        if messages:
            last_msg = messages[-1]
            content = getattr(last_msg, 'content', str(last_msg))
            print(f"\n📝 最终回复:")
            print(f"  {content[:300]}..." if len(content) > 300 else f"  {content}")
        
        # 验证结果（对于不存在的智能体，重点验证fallback机制）
        fallback_success = (
            result_state.get('completed', False) and
            result_state.get('iteration_count', 0) < 8 and
            execution_time.total_seconds() < 30
        )
        
        if result_state.get('a2a_failure_count', 0) > 0:
            print(f"🔄 Fallback机制正常工作: A2A失败 {result_state.get('a2a_failure_count', 0)} 次")
        
        print(f"\n🎯 测试结果: {'✅ 通过' if fallback_success else '❌ 失败'}")
        
        # 打印完整的messages历史记录
        print_message_history(result_state, "自定义智能体功能测试")
        
        # 打印完整的AgentState内容
        print_complete_agent_state(result_state, "自定义智能体功能测试")
        
        return fallback_success
        
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_a2a_agent_direct():
    """直接测试A2A HTTP客户端"""
    print_section("⚡ 直接测试A2A HTTP客户端")
    
    # 设置A2A服务URL
    base_url = "http://localhost:18585"
    os.environ["A2A_BASE_URL"] = base_url
    
    # 创建A2A HTTP客户端实例
    client = A2AHttpClient(base_url)
    
    # 测试weather-agent
    print(f"\n🌤️ 直接测试weather-agent:")
    
    try:
        # 调用A2A智能体
        result = await client.call_a2a_agent(
            agent_id="weather-agent",
            session_id="test_session_direct",
            messages=[{"type": "text", "content": "北京今天天气怎么样？"}],
            user_id="direct_test_user"
        )
        
        print(f"✅ 直接调用成功")
        print(f"响应类型: {result.type}")
        print(f"响应状态: {result.status}")
        print(f"是否最终响应: {result.final}")
        print(f"错误信息: {result.error_msg}")
        
        # 显示响应内容
        if result.content:
            print(f"响应内容预览: {result.content[:200]}..." if len(result.content) > 200 else f"响应内容: {result.content}")
        
        return result.status
        
    except Exception as e:
        print(f"❌ 直接测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_empty_a2a_agents():
    """测试a2a_agents为空时的功能"""
    print_section("🚫 空A2A智能体列表测试")
    
    # 创建没有A2A智能体的AgentState
    agent_state = create_empty_a2a_agent_state(
        user_query="你是谁？"
    )
    
    print(f"测试时间: {datetime.datetime.now()}")
    print(f"A2A智能体数量: 0 (空列表)")
    print(f"用户查询: {agent_state.get('user_query')}")
    print(f"预期行为: 系统应该直接使用常规对话模式，不尝试调用A2A智能体")
    
    # 设置A2A服务URL（虽然不会使用）
    os.environ["A2A_BASE_URL"] = "http://localhost:18585"
    
    # 显示AgentState详情
    print(f"\n📋 AgentState详情:")
    print(f"  - A2A智能体数量: {len(agent_state.get('a2a_agents', []))}")
    print(f"  - A2A失败计数: {agent_state.get('a2a_failure_count', 0)}")
    print(f"  - Fallback设置: {agent_state.get('a2a_fallback_to_general', True)}")
    print(f"  - 任务完成状态: {agent_state.get('completed', False)}")
    
    a2a_agents = agent_state.get('a2a_agents', [])
    if not a2a_agents:
        print(f"  - ✅ A2A智能体列表为空，符合测试预期")
    else:
        print(f"  - ❌ A2A智能体列表不为空: {len(a2a_agents)} 个智能体")
    
    # 创建AgentGraph并执行测试
    print(f"\n🚀 开始执行测试...")
    print(f"📝 测试重点: 验证系统在没有A2A智能体时的常规对话能力")
    
    try:
        agent_graph = AgentGraph()
        config = {
            'configurable': {
                'model_name': 'openai/gpt-4o-mini',
                'session_id': f'empty_a2a_test_{int(datetime.datetime.now().timestamp())}'
            },
            'recursion_limit': 5  # 较小的限制，因为应该是简单对话
        }
        
        start_time = datetime.datetime.now()
        result_state = await agent_graph.ainvoke(agent_state, config)
        end_time = datetime.datetime.now()
        
        execution_time = end_time - start_time
        
        print(f"\n✅ 测试完成！")
        print(f"执行时间: {execution_time.total_seconds():.2f} 秒")
        print(f"迭代次数: {result_state.get('iteration_count', 0)}")
        print(f"A2A失败次数: {result_state.get('a2a_failure_count', 0)}")
        print(f"任务完成: {result_state.get('completed', False)}")
        
        # 显示最后消息
        messages = result_state.get('messages', [])
        if messages:
            last_msg = messages[-1]
            content = getattr(last_msg, 'content', str(last_msg))
            print(f"\n📝 最终回复:")
            print(f"  {content[:400]}..." if len(content) > 400 else f"  {content}")
        
        # 验证结果 - 空A2A智能体时的成功条件
        success_conditions = [
            result_state.get('completed', False),  # 任务完成
            result_state.get('iteration_count', 0) <= 3,  # 迭代次数不多
            execution_time.total_seconds() < 20,  # 执行时间合理
            result_state.get('a2a_failure_count', 0) == 0,  # 没有A2A失败（因为没有尝试）
            len(result_state.get('messages', [])) > 0  # 有回复消息
        ]
        
        success = all(success_conditions)
        
        print(f"\n🔍 验证条件检查:")
        print(f"  ✅ 任务完成: {result_state.get('completed', False)}")
        print(f"  ✅ 迭代次数合理: {result_state.get('iteration_count', 0)} <= 3")
        print(f"  ✅ 执行时间合理: {execution_time.total_seconds():.2f}s < 20s")
        print(f"  ✅ 无A2A失败: {result_state.get('a2a_failure_count', 0)} == 0")
        print(f"  ✅ 有回复消息: {len(result_state.get('messages', []))} > 0")
        
        # 特别检查：确保没有尝试使用A2A智能体
        if result_state.get('a2a_failure_count', 0) == 0:
            print(f"  ✅ 符合预期：没有尝试调用A2A智能体")
        else:
            print(f"  ⚠️  意外情况：有A2A调用尝试 ({result_state.get('a2a_failure_count', 0)} 次失败)")
        
        print(f"\n🎯 测试结果: {'✅ 通过' if success else '❌ 失败'}")
        
        # 打印完整的messages历史记录
        print_message_history(result_state, "空A2A智能体列表测试")
        
        # 打印完整的AgentState内容
        print_complete_agent_state(result_state, "空A2A智能体列表测试")
        
        return success
        
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def run_all_tests():
    """运行所有测试"""
    print_header("A2A智能体功能测试套件")
    print(f"测试开始时间: {datetime.datetime.now()}")
    print(f"A2A服务地址: http://localhost:18585")
    print(f"测试目录: {os.getcwd()}")
    
    # 运行所有测试
    test_results = []
    
    #测试1: Weather Agent
    result1 = await test_weather_agent_functionality()
    test_results.append(("Weather Agent", result1))
    
    # 测试2: 空A2A智能体列表
    result2 = await test_empty_a2a_agents()
    test_results.append(("空A2A智能体列表", result2))
    
    # 测试3: Data Analyst
    #result3 = await test_data_analyst_functionality()
    #test_results.append(("Data Analyst", result3))
    
    # 测试4: 自定义智能体（模拟用户示例）
    result4 = await test_custom_agent_functionality()
    test_results.append(("自定义智能体", result4))
    
    # 测试5: 直接测试A2A HTTP客户端
    result5 = await test_a2a_agent_direct()
    test_results.append(("直接A2A HTTP客户端", result5))
    
    # 汇总测试结果
    print_header("测试结果汇总")
    
    success_count = 0
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    total_tests = len(test_results)
    success_rate = success_count / total_tests * 100
    
    print(f"\n📊 测试统计:")
    print(f"  - 总测试数: {total_tests}")
    print(f"  - 通过测试: {success_count}")
    print(f"  - 成功率: {success_rate:.1f}%")
    
    print(f"\n🏁 测试结束时间: {datetime.datetime.now()}")
    
    if success_rate >= 75:
        print(f"🎉 测试总体通过！")
    else:
        print(f"⚠️  测试需要进一步检查")
    
    return success_rate >= 75

if __name__ == "__main__":
    print("A2A智能体功能测试启动...")
    
    try:
        success = asyncio.run(run_all_tests())
        exit_code = 0 if success else 1
        print(f"\n程序退出码: {exit_code}")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        exit_code = 2
    except Exception as e:
        print(f"\n程序异常: {str(e)}")
        import traceback
        traceback.print_exc()
        exit_code = 3
    
    sys.exit(exit_code) 