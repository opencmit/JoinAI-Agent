# 专家智能体测试用例文档

## 1. 测试概述

### 1.1 测试目标
- 验证专家智能体核心功能的正确性
- 确保连接池管理、认证机制和状态管理的可靠性
- 测试错误处理、重试机制和降级策略
- 验证与远程专家服务的端到端集成

### 1.2 测试范围
- **单元测试**：使用Mock对象测试独立组件
- **集成测试**：使用真实测试服务器验证完整流程
- **覆盖组件**：
  - ExpertRemoteGraphManager（连接管理器）
  - ExpertAgentManager（智能体管理器）
  - 认证机制（HMAC-SHA256和Bearer Token）
  - 异常处理和降级策略

### 1.3 测试策略
- 单元测试采用Mock隔离外部依赖
- 集成测试使用`tests/servers/remote_graph`中的测试服务器
- 使用pytest框架执行测试
- 支持并行测试执行以提高效率

## 2. 单元测试用例

### 2.1 连接管理测试 (ExpertRemoteGraphManager)

#### TC-UT-001: 创建新连接
**测试目标**：验证能够成功创建RemoteGraph连接
```python
def test_create_new_connection():
    """测试创建新的RemoteGraph连接"""
    # 输入：agent_type="write", 有效配置
    # 预期：成功创建连接，连接池size=1
    # Mock：RemoteGraph.__init__
```

#### TC-UT-002: 连接池复用
**测试目标**：验证相同配置的连接能够被复用
```python
def test_connection_pool_reuse():
    """测试连接池复用机制"""
    # 输入：两次相同的agent_type和配置
    # 预期：第二次调用复用第一次的连接，连接池size=1
    # Mock：RemoteGraph.__init__ (只调用一次)
```

#### TC-UT-003: 不同配置创建独立连接
**测试目标**：验证不同配置创建独立的连接
```python
def test_different_config_separate_connections():
    """测试不同配置创建独立连接"""
    # 输入：不同的agent_type或配置
    # 预期：创建多个独立连接，连接池size=配置数量
    # Mock：RemoteGraph.__init__ (调用多次)
```

#### TC-UT-004: 缺失URL配置异常
**测试目标**：验证缺失URL时抛出异常
```python
def test_missing_url_exception():
    """测试缺失URL配置时的异常处理"""
    # 输入：配置中缺少url字段
    # 预期：抛出ExpertServiceUnavailableException
    # Mock：无需
```

#### TC-UT-005: 缺失GraphID配置异常
**测试目标**：验证缺失graph_id时抛出异常
```python
def test_missing_graph_id_exception():
    """测试缺失graph_id配置时的异常处理"""
    # 输入：配置中缺少graph_id字段
    # 预期：抛出ExpertServiceUnavailableException
    # Mock：无需
```

#### TC-UT-006: 连接缓存键生成
**测试目标**：验证缓存键的正确生成
```python
def test_cache_key_generation():
    """测试连接缓存键的生成逻辑"""
    # 输入：不同的agent_type和配置组合
    # 预期：生成唯一的缓存键
    # Mock：无需
```

#### TC-UT-007: 并发连接创建
**测试目标**：验证并发场景下的连接创建
```python
def test_concurrent_connection_creation():
    """测试并发创建连接的线程安全性"""
    # 输入：多线程同时创建相同连接
    # 预期：只创建一个连接，无竞态条件
    # Mock：RemoteGraph.__init__，asyncio
```

#### TC-UT-008: 连接池清理
**测试目标**：验证连接池的清理机制
```python
def test_connection_pool_cleanup():
    """测试连接池清理功能"""
    # 输入：创建多个连接后清理
    # 预期：连接池被正确清空
    # Mock：RemoteGraph对象
```

### 2.2 认证机制测试

#### TC-UT-009: HMAC签名生成
**测试目标**：验证HMAC-SHA256签名的正确性
```python
def test_hmac_signature_generation():
    """测试HMAC-SHA256签名生成"""
    # 输入：app_id, api_key, api_host
    # 预期：生成正确格式的HMAC签名头
    # 验证：签名格式、时间戳RFC1123格式、Base64编码
```

#### TC-UT-010: Bearer Token认证头
**测试目标**：验证Bearer Token认证头生成
```python
def test_bearer_token_auth_header():
    """测试Bearer Token认证头生成"""
    # 输入：设置EXPERT_BEARER_TOKEN环境变量
    # 预期：生成Authorization: Bearer <token>
    # Mock：os.getenv
```

#### TC-UT-011: 认证优先级测试
**测试目标**：验证Bearer Token优先于HMAC
```python
def test_auth_priority():
    """测试认证方式优先级"""
    # 输入：同时配置Bearer Token和HMAC认证
    # 预期：优先使用Bearer Token
    # Mock：os.getenv
```

#### TC-UT-012: 无认证配置警告
**测试目标**：验证无认证配置时的警告
```python
def test_no_auth_warning():
    """测试无认证配置时的警告日志"""
    # 输入：无任何认证配置
    # 预期：记录警告日志，返回基础headers
    # Mock：logger.warning
```

#### TC-UT-013: HMAC时间戳格式
**测试目标**：验证RFC1123时间戳格式
```python
def test_rfc1123_timestamp_format():
    """测试RFC1123时间戳格式正确性"""
    # 输入：当前时间
    # 预期：生成符合RFC1123的时间戳
    # 验证：格式匹配 "Mon, 01 Jan 2025 00:00:00 GMT"
```

#### TC-UT-014: 认证头完整性
**测试目标**：验证认证头的完整性
```python
def test_auth_headers_completeness():
    """测试认证头字段完整性"""
    # 输入：HMAC认证配置
    # 预期：包含所有必需字段(X-JZ-AUTHORIZATION, X-JZ-DATE, X-JZ-HOST, X-JZ-APPID)
    # Mock：无需
```

### 2.3 状态管理测试

#### TC-UT-015: 远程状态准备
**测试目标**：验证远程状态的正确准备
```python
def test_prepare_remote_state():
    """测试远程状态准备"""
    # 输入：包含messages和session_id的AgentState
    # 预期：正确提取并深拷贝必需字段
    # Mock：deepcopy
```

#### TC-UT-016: 空消息状态处理
**测试目标**：验证空消息状态的处理
```python
def test_empty_messages_state():
    """测试空消息状态处理"""
    # 输入：messages为空的状态
    # 预期：返回空列表，不报错
    # Mock：无需
```

#### TC-UT-017: 消息格式标准化
**测试目标**：验证消息格式的标准化
```python
def test_message_standardization():
    """测试消息格式标准化"""
    # 输入：混合格式的消息（dict, AIMessage, AIMessageChunk）
    # 预期：统一转换为标准AIMessage格式
    # Mock：AIMessage
```

#### TC-UT-018: ID格式内容过滤
**测试目标**：验证ID格式内容的过滤
```python
def test_id_format_content_filtering():
    """测试ID格式内容的过滤"""
    # 输入：content为UUID或run--开头的消息
    # 预期：过滤掉这些无效消息
    # Mock：无需
```

#### TC-UT-019: 空内容消息过滤
**测试目标**：验证空内容消息的过滤
```python
def test_empty_content_filtering():
    """测试空内容消息的过滤"""
    # 输入：content为空的消息
    # 预期：过滤掉空内容消息
    # Mock：无需
```

#### TC-UT-020: 结果处理完整性
**测试目标**：验证结果处理的完整性
```python
def test_process_result_completeness():
    """测试结果处理的完整性"""
    # 输入：包含messages和completed字段的结果
    # 预期：正确提取所有字段到state_update
    # Mock：无需
```

### 2.4 异常处理测试 (ExpertAgentManager)

#### TC-UT-021: 空agent_type处理
**测试目标**：验证空agent_type的处理
```python
def test_empty_agent_type():
    """测试空agent_type的处理"""
    # 输入：state中agent_type为None
    # 预期：返回错误Command，goto="supervisor"
    # Mock：无需
```

#### TC-UT-022: normal类型降级
**测试目标**：验证normal类型的降级处理
```python
def test_normal_type_fallback():
    """测试normal类型的降级处理"""
    # 输入：agent_type="normal"
    # 预期：设置expert_connection_failed=True，降级处理
    # Mock：无需
```

#### TC-UT-023: 不支持的agent_type
**测试目标**：验证不支持的agent_type处理
```python
def test_unsupported_agent_type():
    """测试不支持的agent_type"""
    # 输入：agent_type不在EXPERT_AGENTS列表
    # 预期：返回错误消息，goto="supervisor"
    # Mock：EXPERT_AGENTS常量
```

#### TC-UT-024: 超时异常处理
**测试目标**：验证超时异常的处理
```python
def test_timeout_exception_handling():
    """测试超时异常处理"""
    # 输入：远程调用超时
    # 预期：捕获TimeoutError，调用_handle_expert_fallback
    # Mock：asyncio.wait_for抛出TimeoutError
```

#### TC-UT-025: 服务异常处理
**测试目标**：验证服务异常的处理
```python
def test_service_exception_handling():
    """测试服务异常处理"""
    # 输入：远程调用抛出ExpertServiceException
    # 预期：正确处理并记录日志
    # Mock：remote_graph.astream
```

#### TC-UT-026: 重试机制第一次
**测试目标**：验证第一次重试
```python
def test_retry_first_attempt():
    """测试第一次重试"""
    # 输入：expert_retry_count=0，失败
    # 预期：增加retry_count，goto="expert_agent"
    # Mock：asyncio.sleep
```

#### TC-UT-027: 重试机制第二次
**测试目标**：验证第二次重试
```python
def test_retry_second_attempt():
    """测试第二次重试"""
    # 输入：expert_retry_count=1，失败
    # 预期：增加retry_count，goto="expert_agent"
    # Mock：asyncio.sleep
```

#### TC-UT-028: 重试次数耗尽
**测试目标**：验证重试次数耗尽后的处理
```python
def test_retry_exhausted():
    """测试重试次数耗尽"""
    # 输入：expert_retry_count>=max_retries
    # 预期：设置expert_connection_failed=True，goto="supervisor"
    # Mock：os.getenv("EXPERT_MAX_RETRIES")
```

#### TC-UT-029: 指数退避延迟
**测试目标**：验证指数退避延迟策略
```python
def test_exponential_backoff():
    """测试指数退避延迟"""
    # 输入：不同的retry_count
    # 预期：delay = 2^retry_count
    # Mock：asyncio.sleep
```

#### TC-UT-030: 成功调用后状态更新
**测试目标**：验证成功调用后的状态更新
```python
def test_success_state_update():
    """测试成功调用后的状态更新"""
    # 输入：成功的远程调用结果
    # 预期：清除失败标志，设置completed=True
    # Mock：remote_graph.astream返回成功结果
```

## 3. 集成测试用例

### 3.1 端到端服务调用测试

#### TC-IT-001: 写作专家服务调用
**测试目标**：验证写作专家服务的完整调用流程
```python
def test_write_expert_service():
    """测试写作专家服务端到端调用"""
    # 前置条件：启动write_expert测试服务器(端口8001)
    # 输入：写作任务消息
    # 预期：返回写作规划和执行结果
    # 验证：两节点架构(planner + agent)正常工作
```

#### TC-IT-002: PPT专家服务调用
**测试目标**：验证PPT专家服务的完整调用流程
```python
def test_ppt_expert_service():
    """测试PPT专家服务端到端调用"""
    # 前置条件：启动ppt_expert测试服务器(端口8002)
    # 输入：PPT制作任务消息
    # 预期：返回PPT内容和结构
    # 验证：专用工具调用正常
```

#### TC-IT-003: Web专家服务调用
**测试目标**：验证Web专家服务的完整调用流程
```python
def test_web_expert_service():
    """测试Web专家服务端到端调用"""
    # 前置条件：启动web_expert测试服务器(端口8003)
    # 输入：Web搜索或信息提取任务
    # 预期：返回搜索结果或提取的信息
    # 验证：Web工具集成正常
```

#### TC-IT-004: 广播专家服务调用
**测试目标**：验证广播专家服务的完整调用流程
```python
def test_broadcast_expert_service():
    """测试广播专家服务端到端调用"""
    # 前置条件：启动broadcast_expert测试服务器(端口8004)
    # 输入：播客脚本生成任务
    # 预期：返回对话脚本
    # 验证：广播工具正常工作
```

#### TC-IT-005: 多专家并行调用
**测试目标**：验证多个专家服务的并行调用
```python
def test_multiple_experts_parallel():
    """测试多专家并行调用"""
    # 前置条件：启动所有测试服务器
    # 输入：并发调用不同专家服务
    # 预期：所有服务独立完成，无相互干扰
    # 验证：连接池管理正确
```

#### TC-IT-006: 服务切换测试
**测试目标**：验证不同专家服务间的切换
```python
def test_service_switching():
    """测试专家服务切换"""
    # 前置条件：启动多个测试服务器
    # 输入：连续调用不同专家服务
    # 预期：正确切换，连接复用
    # 验证：状态隔离正确
```

#### TC-IT-007: 长时间运行测试
**测试目标**：验证长时间任务的处理
```python
def test_long_running_task():
    """测试长时间运行任务"""
    # 前置条件：配置较长的超时时间
    # 输入：需要较长处理时间的任务
    # 预期：正常完成，不超时
    # 验证：超时配置生效
```

#### TC-IT-008: 大消息负载测试
**测试目标**：验证大消息负载的处理
```python
def test_large_message_payload():
    """测试大消息负载处理"""
    # 前置条件：测试服务器正常运行
    # 输入：包含大量内容的消息
    # 预期：正确处理，无截断
    # 验证：消息完整性
```

### 3.2 流式输出测试

#### TC-IT-009: 流式响应接收
**测试目标**：验证流式响应的正确接收
```python
def test_streaming_response():
    """测试流式响应接收"""
    # 前置条件：服务支持流式输出
    # 输入：触发流式响应的任务
    # 预期：增量接收内容
    # 验证：stream_mode="updates"工作正常
```

#### TC-IT-010: 增量内容检测
**测试目标**：验证增量内容的正确检测
```python
def test_incremental_content_detection():
    """测试增量内容检测"""
    # 前置条件：流式输出启用
    # 输入：生成增量内容的任务
    # 预期：正确识别新增内容
    # 验证：累积式和替换式内容区分
```

#### TC-IT-011: 消息格式转换
**测试目标**：验证流式消息格式转换
```python
def test_streaming_message_format():
    """测试流式消息格式转换"""
    # 前置条件：接收不同格式的流式消息
    # 输入：AIMessageChunk等格式
    # 预期：统一转换为AIMessage
    # 验证：格式标准化正确
```

#### TC-IT-012: 子图数据处理
**测试目标**：验证子图数据的处理
```python
def test_subgraph_data_processing():
    """测试子图数据处理"""
    # 前置条件：subgraphs=True
    # 输入：包含子图的响应
    # 预期：正确解析namespace和updates
    # 验证：元组格式处理正确
```

#### TC-IT-013: 空块处理
**测试目标**：验证空流式块的处理
```python
def test_empty_chunk_handling():
    """测试空流式块处理"""
    # 前置条件：流式输出包含空块
    # 输入：混合空块和有效块
    # 预期：跳过空块，处理有效内容
    # 验证：无异常抛出
```

#### TC-IT-014: 流式超时处理
**测试目标**：验证流式输出的超时处理
```python
def test_streaming_timeout():
    """测试流式输出超时"""
    # 前置条件：设置较短超时
    # 输入：长时间流式输出
    # 预期：触发超时异常
    # 验证：TimeoutError正确处理
```

### 3.3 错误恢复测试

#### TC-IT-015: 服务不可用恢复
**测试目标**：验证服务不可用时的恢复
```python
def test_service_unavailable_recovery():
    """测试服务不可用恢复"""
    # 前置条件：服务初始不可用
    # 输入：调用请求
    # 预期：触发重试，最终降级
    # 验证：降级到普通智能体
```

#### TC-IT-016: 网络中断恢复
**测试目标**：验证网络中断的恢复
```python
def test_network_interruption_recovery():
    """测试网络中断恢复"""
    # 前置条件：模拟网络中断
    # 输入：进行中的请求
    # 预期：检测中断，重试
    # 验证：重试机制生效
```

#### TC-IT-017: 服务重启恢复
**测试目标**：验证服务重启后的恢复
```python
def test_service_restart_recovery():
    """测试服务重启恢复"""
    # 前置条件：服务运行中
    # 输入：重启服务，继续请求
    # 预期：新连接建立成功
    # 验证：连接池更新
```

#### TC-IT-018: 部分失败处理
**测试目标**：验证部分失败的处理
```python
def test_partial_failure_handling():
    """测试部分失败处理"""
    # 前置条件：多专家服务运行
    # 输入：部分服务失败
    # 预期：失败服务降级，其他正常
    # 验证：隔离性
```

#### TC-IT-019: 认证失败处理
**测试目标**：验证认证失败的处理
```python
def test_auth_failure_handling():
    """测试认证失败处理"""
    # 前置条件：错误的认证配置
    # 输入：调用请求
    # 预期：认证失败，记录日志
    # 验证：不影响无认证服务
```

#### TC-IT-020: 级联失败预防
**测试目标**：验证级联失败的预防
```python
def test_cascading_failure_prevention():
    """测试级联失败预防"""
    # 前置条件：高负载场景
    # 输入：一个服务失败
    # 预期：不影响其他服务
    # 验证：熔断机制工作
```

## 4. 测试数据

### 4.1 Mock消息样本
```python
# 标准消息格式
standard_messages = [
    HumanMessage(content="请帮我写一篇关于AI的文章"),
    AIMessage(content="我将为您撰写一篇关于AI的文章...")
]

# 混合格式消息
mixed_messages = [
    {"type": "human", "content": "用户消息"},
    AIMessage(content="AI响应"),
    {"type": "ai", "content": "字典格式AI消息"}
]

# 无效消息（应被过滤）
invalid_messages = [
    {"type": "ai", "content": "run--abc123-def456"},  # ID格式
    {"type": "ai", "content": ""},  # 空内容
    {"type": "ai", "content": "550e8400-e29b-41d4-a716-446655440000"}  # UUID
]
```

### 4.2 配置数据集
```python
# 有效配置
valid_config = {
    "expert_services": {
        "write": {
            "url": "http://localhost:8001",
            "graph_id": "write-expert-v1"
        }
    }
}

# 缺失URL配置
missing_url_config = {
    "expert_services": {
        "write": {
            "graph_id": "write-expert-v1"
        }
    }
}

# 认证配置
auth_config = {
    "app_id": "TEST_APP_ID",
    "api_key": "TEST_API_KEY",
    "api_host": "http://test.api.host"
}
```

### 4.3 异常场景数据
```python
# 超时场景
timeout_scenario = {
    "timeout": 1,  # 1秒超时
    "delay": 5,    # 服务延迟5秒
    "expected_exception": ExpertServiceTimeoutException
}

# 服务不可用场景
unavailable_scenario = {
    "service_status": "stopped",
    "retry_count": 3,
    "expected_exception": ExpertServiceUnavailableException
}
```

### 4.4 预期结果集
```python
# 成功响应
success_response = {
    "messages": [
        AIMessage(content="专家响应内容", name="expert")
    ],
    "completed": True
}

# 降级响应
fallback_response = {
    "messages": [
        AIMessage(content="专家服务连接失败，已降级到普通智能体", name="system")
    ],
    "expert_connection_failed": True,
    "expert_failure_reason": "服务不可用"
}
```

## 5. 测试执行说明

### 5.1 环境准备
```bash
# 1. 安装测试依赖
pip install pytest pytest-asyncio pytest-mock pytest-cov

# 2. 设置环境变量（可选）
export EXPERT_BEARER_TOKEN="test_token"
export EXPERT_APP_ID="test_app_id"
export EXPERT_API_KEY="test_api_key"
export EXPERT_API_HOST="http://test.host"
```

### 5.2 单元测试执行
```bash
# 运行所有单元测试
pytest tests/expert_agents/unit_tests/ -v

# 运行特定测试文件
pytest tests/expert_agents/unit_tests/test_expert_remote_manager.py -v

# 运行特定测试用例
pytest tests/expert_agents/unit_tests/test_expert_remote_manager.py::test_create_new_connection -v

# 生成覆盖率报告
pytest tests/expert_agents/unit_tests/ --cov=langgraph_agent.graph.expert_agent --cov-report=html
```

### 5.3 集成测试执行
```bash
# 1. 启动测试服务器
./tests/servers/remote_graph/test_expert_services.sh start

# 2. 运行所有集成测试
pytest tests/expert_agents/integration_tests/ -v

# 3. 运行特定专家服务测试
pytest tests/expert_agents/integration_tests/test_expert_services.py::test_write_expert_service -v

# 4. 停止测试服务器
./tests/servers/remote_graph/test_expert_services.sh stop
```

### 5.4 并行测试执行
```bash
# 使用pytest-xdist进行并行测试
pip install pytest-xdist

# 并行运行（自动检测CPU核心数）
pytest tests/expert_agents/ -n auto

# 指定并行进程数
pytest tests/expert_agents/ -n 4
```

### 5.5 持续集成配置
```yaml
# .gitlab-ci.yml 或 .github/workflows/test.yml
test:
  stage: test
  script:
    - pip install -r requirements-test.txt
    - ./tests/servers/remote_graph/test_expert_services.sh start
    - pytest tests/expert_agents/unit_tests/ -v --cov
    - pytest tests/expert_agents/integration_tests/ -v
    - ./tests/servers/remote_graph/test_expert_services.sh stop
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

## 6. 测试覆盖率目标

### 6.1 单元测试覆盖率
- **目标**: ≥ 85%
- **关键路径**: 100%
- **异常处理**: 100%
- **边界条件**: ≥ 90%

### 6.2 集成测试覆盖率
- **端到端流程**: 100%
- **专家服务**: 所有6种类型
- **错误场景**: ≥ 80%
- **性能场景**: 基准测试

### 6.3 质量指标
- **缺陷密度**: < 1 bug/KLOC
- **测试执行时间**: < 5分钟（单元测试）
- **测试稳定性**: > 99%（无随机失败）
- **代码审查覆盖**: 100%

## 7. 风险和缓解措施

### 7.1 测试风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 测试服务器不稳定 | 集成测试失败 | Mock服务器备选方案 |
| 网络延迟 | 超时测试不准确 | 可配置超时参数 |
| 并发测试竞态 | 测试结果不确定 | 使用锁和同步机制 |
| 环境配置差异 | 测试结果不一致 | 容器化测试环境 |

### 7.2 质量保证
- 测试代码审查
- 测试用例评审
- 定期更新测试数据
- 监控测试覆盖率趋势
- 失败测试分析和修复

## 8. 附录

### 8.1 测试工具和框架
- **pytest**: 测试框架
- **pytest-asyncio**: 异步测试支持
- **pytest-mock**: Mock对象支持
- **pytest-cov**: 覆盖率统计
- **pytest-xdist**: 并行测试

### 8.2 参考文档
- [LangGraph RemoteGraph文档](https://python.langchain.com/docs/langgraph)
- [pytest文档](https://docs.pytest.org/)
- [Python unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

### 8.3 版本历史
| 版本 | 日期 | 作者 | 说明 |
|------|------|------|------|
| 1.0 | 2025-09-15 | Claude | 初始版本，包含50个测试用例 |

---
**文档维护说明**：本文档应随着代码更新而同步更新，每次新增功能或修复bug后都应更新相应的测试用例。