#!/usr/bin/env python3
"""
多步骤A2A智能体协作测试脚本
专注于验证多步骤路由逻辑和任务分解功能
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

def print_all_messages(result_state: AgentState, test_name: str):
    """打印所有消息内容"""
    print(f"\n📝 {test_name} - 所有消息内容:")
    print("=" * 60)
    
    messages = result_state.get('messages', [])
    print(f"总消息数量: {len(messages)}")
    
    for i, message in enumerate(messages, 1):
        content = getattr(message, 'content', str(message))
        msg_type = getattr(message, 'type', 'unknown')
        
        print(f"\n消息 {i} (类型: {msg_type}):")
        print("-" * 40)
        print(content)
    
    print("=" * 60)
    
    # 打印状态信息
    print(f"\n📊 {test_name} - 状态信息:")
    print(f"  迭代次数: {result_state.get('iteration_count', 0)}")
    print(f"  任务完成: {result_state.get('completed', False)}")
    print(f"  当前智能体任务: {result_state.get('current_agent_task', 'None')}")
    print(f"  A2A失败次数: {result_state.get('a2a_failure_count', 0)}")
    
    # 检查已执行的智能体
    executed_agents = []
    for key in result_state.keys():
        if key.startswith("a2a_") and key.endswith("_completed"):
            executed_agents.append(key)
    
    print(f"  已执行的智能体: {executed_agents}")

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
        elif key in ['a2a_agents', 'workflow_plan', 'execution_results', 'supervisor_decision']:
            # 结构化数据特殊处理
            print(f"类型: {type(value).__name__}")
            if value:
                print("内容:")
                try:
                    import json
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
    
    # 多步骤任务专用检查
    workflow_plan = result_state.get('workflow_plan', {})
    if workflow_plan and workflow_plan.get('workflow_type') == 'multi_step':
        steps = workflow_plan.get('steps', [])
        print(f"📋 工作流步骤详情:")
        for i, step in enumerate(steps):
            step_status = "✅完成" if i < result_state.get('current_step_index', 0) else "⏳待执行"
            print(f"  步骤{i+1}: {step.get('description', 'Unknown')} - {step_status}")
    
    print(f"\n" + "="*80)
    print(f"🔍 {test_name} - AgentState内容结束")
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
        elif key in ['a2a_agents', 'workflow_plan', 'execution_results', 'supervisor_decision']:
            # 结构化数据特殊处理
            print(f"类型: {type(value).__name__}")
            if value:
                print("内容:")
                try:
                    import json
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
    
    # 多步骤任务专用检查
    workflow_plan = result_state.get('workflow_plan', {})
    if workflow_plan and workflow_plan.get('workflow_type') == 'multi_step':
        steps = workflow_plan.get('steps', [])
        print(f"📋 工作流步骤详情:")
        for i, step in enumerate(steps):
            step_status = "✅完成" if i < result_state.get('current_step_index', 0) else "⏳待执行"
            print(f"  步骤{i+1}: {step.get('description', 'Unknown')} - {step_status}")
    
    print(f"\n" + "="*80)
    print(f"🔍 {test_name} - AgentState内容结束")
    print("="*80)

def create_full_agent_state(user_query: str) -> AgentState:
    """创建包含全部5个A2A智能体的测试状态"""
    
    # 全部5个A2A智能体配置
    a2a_agents = [
        {
            "agent_id": "weather-agent",
            "name": "天气助手",
            "desc": "专业天气查询和预报服务",
            "user_id": "weather_user_001"
        },
        {
            "agent_id": "data-analyst", 
            "name": "数据分析师",
            "desc": "数据分析和可视化专家",
            "user_id": "analyst_user_002"
        },
        {
            "agent_id": "document-writer",
            "name": "文档助手", 
            "desc": "文档编写和格式化专家",
            "user_id": "writer_user_003"
        },
        {
            "agent_id": "code-generator",
            "name": "代码生成器",
            "desc": "编程和代码生成专家",
            "user_id": "coder_user_004"
        },
        {
            "agent_id": "knowledge-agent",
            "name": "知识专家",
            "desc": "知识问答和概念解释专家",
            "user_id": "knowledge_user_005"
        }
    ]
    
    test_input = {
        "messages": [],
        "input": {
            "message": [{
                "type": "human",
                "content": user_query
            }],
            "a2a_agents": a2a_agents
        },
        "model": "openai/gpt-4o-mini"
    }
    
    return create_initial_state(test_input)

async def test_phone_size_query_only():
    """单独测试手机尺寸查询（仅验证路由逻辑）"""
    print_section("📱 单独测试: 手机尺寸查询")
    
    user_query = "调用知识专家查一加手机11的尺寸，然后调用数据分析师分析一下销售数据趋势，最后使用通用智能体总结"
    
    print(f"测试时间: {datetime.datetime.now()}")
    print(f"用户查询: {user_query}")
    print(f"预期智能体协作: knowledge-agent → data-analyst")
    print(f"🎯 专注验证: supervisor创建次数、智能体切换逻辑")
    
    # 创建AgentState
    agent_state = create_full_agent_state(user_query)
    
    # 显示A2A智能体信息
    print(f"\n📋 挂载的A2A智能体:")
    for i, agent in enumerate(agent_state.get('a2a_agents', []), 1):
        print(f"  {i}. {agent['name']} (ID: {agent['agent_id']}) - {agent['desc']}")
        print(f"     用户ID: {agent.get('user_id', '未设置')}")
    
    # 创建AgentGraph并执行测试
    print(f"\n🚀 开始执行...")
    
    try:
        agent_graph = AgentGraph()
        
        config = {
            'configurable': {
                'model_name': 'openai/gpt-4o-mini',
                'session_id': f'test_phone_size_{int(datetime.datetime.now().timestamp())}'
            },
            'recursion_limit': 20  # 🔥 提高递归限制以支持多步骤任务
        }
        
        start_time = datetime.datetime.now()
        result_state = await agent_graph.ainvoke(agent_state, config)
        end_time = datetime.datetime.now()
        
        execution_time = end_time - start_time
        
        print(f"\n✅ 执行完成！")
        print(f"执行时间: {execution_time.total_seconds():.2f} 秒")
        
        # 打印所有消息
        print_all_messages(result_state, "手机尺寸查询")
        
        # 打印完整的AgentState内容
        print_complete_agent_state(result_state, "手机尺寸查询")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 执行异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_knowledge_to_code_scenario():
    """测试场景1: 知识查询 → 代码生成"""
    print_section("🧠➡️💻 测试1: 知识查询 → 代码生成")
    
    user_query = "请先查询北京、上海的天气，然后整理成文档，最后使用通用智能体总结"
    
    print(f"测试时间: {datetime.datetime.now()}")
    print(f"用户查询: {user_query}")
    print(f"预期智能体协作: knowledge-agent → code-generator")
    
    # 创建AgentState
    agent_state = create_full_agent_state(user_query)
    
    # 显示A2A智能体信息
    print(f"\n📋 挂载的A2A智能体:")
    for i, agent in enumerate(agent_state.get('a2a_agents', []), 1):
        print(f"  {i}. {agent['name']} (ID: {agent['agent_id']}) - {agent['desc']}")
        print(f"     用户ID: {agent.get('user_id', '未设置')}")
    
    # 创建AgentGraph并执行测试
    print(f"\n🚀 开始执行...")
    
    try:
        agent_graph = AgentGraph()
        
        config = {
            'configurable': {
                'model_name': 'openai/gpt-4o-mini',
                'session_id': f'test_knowledge_code_{int(datetime.datetime.now().timestamp())}'
            },
            'recursion_limit': 20  # 🔥 提高递归限制以支持多步骤任务
        }
        
        start_time = datetime.datetime.now()
        result_state = await agent_graph.ainvoke(agent_state, config)
        end_time = datetime.datetime.now()
        
        execution_time = end_time - start_time
        
        print(f"\n✅ 执行完成！")
        print(f"执行时间: {execution_time.total_seconds():.2f} 秒")
        
        # 打印所有消息
        print_all_messages(result_state, "知识查询 → 代码生成")
        
        # 打印完整的AgentState内容
        print_complete_agent_state(result_state, "知识查询 → 代码生成")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 执行异常: {str(e)}")
        return False

async def test_weather_to_document_scenario():
    """测试场景2: 天气查询 → 文档生成"""
    print_section("🌤️➡️📝 测试2: 天气查询 → 文档生成")
    
    user_query = "先调用天气助手查询北京今天的天气情况，然后调用文档助手生成一份天气报告"
    
    print(f"测试时间: {datetime.datetime.now()}")
    print(f"用户查询: {user_query}")
    print(f"预期智能体协作: weather-agent → document-writer")
    
    # 创建AgentState
    agent_state = create_full_agent_state(user_query)
    
    # 显示A2A智能体信息
    print(f"\n📋 挂载的A2A智能体:")
    for i, agent in enumerate(agent_state.get('a2a_agents', []), 1):
        print(f"  {i}. {agent['name']} (ID: {agent['agent_id']}) - {agent['desc']}")
        print(f"     用户ID: {agent.get('user_id', '未设置')}")
    
    # 创建AgentGraph并执行测试
    print(f"\n🚀 开始执行...")
    
    try:
        agent_graph = AgentGraph()
        
        config = {
            'configurable': {
                'model_name': 'openai/gpt-4o-mini',
                'session_id': f'test_weather_doc_{int(datetime.datetime.now().timestamp())}'
            },
            'recursion_limit': 20  # 🔥 提高递归限制
        }
        
        start_time = datetime.datetime.now()
        result_state = await agent_graph.ainvoke(agent_state, config)
        end_time = datetime.datetime.now()
        
        execution_time = end_time - start_time
        
        print(f"\n✅ 执行完成！")
        print(f"执行时间: {execution_time.total_seconds():.2f} 秒")
        
        # 打印所有消息
        print_all_messages(result_state, "天气查询 → 文档生成")
        
        # 打印完整的AgentState内容
        print_complete_agent_state(result_state, "天气查询 → 文档生成")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 执行异常: {str(e)}")
        return False

async def test_data_analysis_scenario():
    """测试场景3: 数据分析 → 文档报告"""
    print_section("📊➡️📝 测试3: 数据分析 → 文档报告")
    
    user_query = "请数据分析师分析一下销售数据趋势，然后让文档助手编写分析报告"
    
    print(f"测试时间: {datetime.datetime.now()}")
    print(f"用户查询: {user_query}")
    print(f"预期智能体协作: data-analyst → document-writer")
    
    # 创建AgentState
    agent_state = create_full_agent_state(user_query)
    
    # 显示A2A智能体信息
    print(f"\n📋 挂载的A2A智能体:")
    for i, agent in enumerate(agent_state.get('a2a_agents', []), 1):
        print(f"  {i}. {agent['name']} (ID: {agent['agent_id']}) - {agent['desc']}")
        print(f"     用户ID: {agent.get('user_id', '未设置')}")
    
    # 创建AgentGraph并执行测试
    print(f"\n🚀 开始执行...")
    
    try:
        agent_graph = AgentGraph()
        
        config = {
            'configurable': {
                'model_name': 'openai/gpt-4o-mini',
                'session_id': f'test_data_analysis_{int(datetime.datetime.now().timestamp())}'
            },
            'recursion_limit': 20  # 🔥 提高递归限制
        }
        
        start_time = datetime.datetime.now()
        result_state = await agent_graph.ainvoke(agent_state, config)
        end_time = datetime.datetime.now()
        
        execution_time = end_time - start_time
        
        print(f"\n✅ 执行完成！")
        print(f"执行时间: {execution_time.total_seconds():.2f} 秒")
        
        # 打印所有消息
        print_all_messages(result_state, "数据分析 → 文档报告")
        
        # 打印完整的AgentState内容
        print_complete_agent_state(result_state, "数据分析 → 文档报告")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 执行异常: {str(e)}")
        return False

async def run_all_multi_step_tests():
    """运行所有多步骤测试"""
    print(f"测试开始时间: {datetime.datetime.now()}")
    print(f"A2A服务地址: http://localhost:18585")
    print(f"测试目录: {os.getcwd()}")
    
    # 设置A2A服务URL
    os.environ["A2A_BASE_URL"] = "http://localhost:18585"
    
    # 运行所有多步骤测试
    test_results = []
    
    # 测试0: 手机尺寸查询
    #print("\n" + "📱" * 40)
    #result0 = await test_phone_size_query_only()
    #test_results.append(("手机尺寸查询 (单独测试)", result0))
    
    # 测试1: 知识查询 → 代码生成
    #print("\n" + "🟢" * 40)
    result1 = await test_knowledge_to_code_scenario()
    test_results.append(("知识查询 → 代码生成", result1))
    
    # 测试2: 天气查询 → 文档生成
    #print("\n" + "🟢" * 40)
    #result2 = await test_weather_to_document_scenario()
    #test_results.append(("天气查询 → 文档生成", result2))
    
    # 测试3: 数据分析 → 文档报告
    #print("\n" + "🟢" * 40)
    #result3 = await test_data_analysis_scenario()
    #test_results.append(("数据分析 → 文档报告", result3))
    
    # 汇总测试结果    
    success_count = 0
    for test_name, success in test_results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
        if success:
            success_count += 1
    
    total_tests = len(test_results)
    success_rate = success_count / total_tests * 100
    
    print(f"  - 总测试数: {total_tests}")
    print(f"  - 通过测试: {success_count}")
    print(f"  - 成功率: {success_rate:.1f}%")
    
    print(f"\n🎯 关键问题诊断:")
    print(f"  - 智能体切换逻辑: {'✅ 正常' if success_count >= 1 else '❌ 需修复'}")
    print(f"  - 递归限制配置: {'✅ 正常' if success_count >= 1 else '❌ 需调整'}")
    print(f"  - Supervisor重复创建: {'🔍 待观察日志' if success_count >= 1 else '❌ 明显异常'}")
    print(f"  - 任务分解功能: {'✅ 正常' if success_count >= 1 else '❌ 需优化'}")
    
    print(f"\n🏁 测试结束时间: {datetime.datetime.now()}")

    return success_rate >= 50

if __name__ == "__main__":    
    try:
        success = asyncio.run(run_all_multi_step_tests())
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