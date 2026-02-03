# 专家智能体服务测试基础设施

## 📋 概述

本目录包含了专家智能体服务的测试基础设施，用于在独立的 LangGraph 服务中运行和测试各种专家智能体。这些服务为主系统提供专业化的功能，包括写作、PPT生成、Web搜索、播客制作等。

## 🏗️ 架构说明

### 系统架构
每个专家服务都采用 **两节点架构设计**：
- **Planner节点**：负责分析任务需求，制定执行计划
- **Agent节点**：根据计划执行具体任务，生成最终结果

### 服务列表

| 服务名称 | 目录 | 端口 | Graph ID | 功能描述 |
|---------|------|------|----------|----------|
| write | write_expert | 8001 | write-expert-v1 | 专业写作服务 |
| ppt | ppt_expert | 8002 | ppt-expert-v1 | PPT生成服务 |
| web | web_expert | 8003 | web-expert-v1 | Web搜索服务 |
| broadcast | broadcast_expert | 8004 | broadcast-expert-v1 | 播客制作服务 |
| design | design_expert | 8005 | design-expert-v1 | 设计创作服务 |

## 📁 目录结构

```
remote_graph/
├── README.md                  # 本文档
├── requirements.txt           # Python依赖包
├── test_expert_services.sh    # 服务管理脚本
├── logs/                      # 服务日志目录（运行时生成）
│   ├── *.log                 # 各服务的运行日志
│   └── *.pid                 # 各服务的进程ID文件
├── write_expert/              # 写作专家服务
│   ├── graph.py              # 图定义和节点实现
│   ├── langgraph.json        # LangGraph配置
│   └── .env.example          # 环境变量示例
├── ppt_expert/                # PPT专家服务
│   ├── graph.py
│   ├── langgraph.json
│   └── .env.example
├── web_expert/                # Web专家服务
│   ├── graph.py
│   ├── langgraph.json
│   └── .env.example
├── broadcast_expert/          # 播客专家服务
│   ├── graph.py
│   ├── langgraph.json
│   └── .env.example
└── design_expert/             # 设计专家服务
    ├── graph.py
    ├── langgraph.json
    ├── .env.example
    ├── test_api.py            # API测试脚本
    └── tools/
        └── design_tools.py    # 设计工具集
```

## 🚀 快速开始

### 1. 环境准备

确保已安装以下工具：
- Python 3.12+
- pip
- langgraph-cli

### 2. 安装依赖

```bash
# 进入服务目录
cd langgraph_backend/langgraph_agent/tests/servers/remote_graph

# 安装Python依赖
pip install -r requirements.txt

# 安装 LangGraph CLI（如果尚未安装）
pip install langgraph-cli
```

### 3. 配置环境变量

为每个服务配置环境变量：

```bash
# 复制环境变量示例文件
cp write_expert/.env.example write_expert/.env
cp ppt_expert/.env.example ppt_expert/.env
cp web_expert/.env.example web_expert/.env
cp broadcast_expert/.env.example broadcast_expert/.env
cp design_expert/.env.example design_expert/.env

# 编辑各个 .env 文件，设置必要的配置
# 主要配置项：
# - OPENAI_API_KEY: OpenAI API密钥
# - OPENAI_BASE_URL: API基础URL（可选）
# - OPENAI_MODEL: 使用的模型名称
# - LANGCHAIN_API_KEY: LangChain追踪密钥（可选）
```

### 4. 启动服务

```bash
# 启动所有服务
./test_expert_services.sh start

# 或启动单个服务
./test_expert_services.sh start write
```

## 🛠️ 服务管理

### 管理脚本使用

`test_expert_services.sh` 提供了统一的服务管理接口：

```bash
# 查看帮助信息
./test_expert_services.sh help

# 启动服务
./test_expert_services.sh start [service_name]  # 不指定则启动所有

# 停止服务
./test_expert_services.sh stop [service_name]   # 不指定则停止所有

# 查看服务状态
./test_expert_services.sh status [service_name] # 不指定则查看所有

# 重启服务
./test_expert_services.sh restart [service_name] # 不指定则重启所有

# 测试服务连接
./test_expert_services.sh test [service_name]   # 不指定则测试所有
```

### 服务状态示例

```bash
$ ./test_expert_services.sh status
专家服务状态:
============
write:      运行中 (PID: 12345, 端口: 8001)
ppt:        运行中 (PID: 12346, 端口: 8002)
web:        运行中 (PID: 12347, 端口: 8003)
broadcast:  运行中 (PID: 12348, 端口: 8004)
design:     运行中 (PID: 12349, 端口: 8005)
============
运行中: 5/5
```

## 📚 专家服务详情

### Write Expert (写作专家)
- **功能**：专业文档写作、报告生成、创意写作
- **架构**：planner节点制定写作大纲，agent节点执行写作任务
- **特点**：支持多种文档类型、自适应写作风格

### PPT Expert (PPT专家)
- **功能**：幻灯片内容生成、结构设计、要点提炼
- **架构**：planner节点设计演示结构，agent节点生成具体内容
- **特点**：结构化输出、支持多种演示场景

### Web Expert (Web专家)
- **功能**：网页搜索、信息提取、内容聚合
- **架构**：planner节点规划搜索策略，agent节点执行搜索和整理
- **特点**：多源信息整合、智能结果筛选

### Broadcast Expert (播客专家)
- **功能**：播客脚本创作、对话生成、音频内容策划
- **架构**：planner节点设计节目结构，agent节点生成对话内容
- **特点**：多角色对话、自然语言风格

### Design Expert (设计专家)
- **功能**：图像生成、图像修改、设计创作、样式转换
- **架构**：planner节点制定设计方案，agent节点执行设计任务
- **特点**：支持多种设计风格、图像处理、创意生成
- **工具集**：
  - `generate_image`: 生成新图像（海报、Logo、图标等）
  - `modify_image`: 修改现有图像（风格转换、效果调整）
  - `analyze_design_request`: 分析设计需求
  - `save_design_file`: 保存设计文件
  - `create_design_preview`: 创建预览页面

## 👨‍💻 开发指南

### 添加新的专家服务

1. **创建服务目录**：
```bash
mkdir new_expert
cd new_expert
```

2. **创建必需文件**：

`graph.py` - 图定义和节点实现：
```python
from typing import Annotated
from typing_extensions import TypedDict
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

def create_planner():
    # 实现planner节点
    pass

def create_agent():
    # 实现agent节点
    pass

# 构建图
builder = StateGraph(State)
builder.add_node("planner", create_planner())
builder.add_node("agent", create_agent())
builder.add_edge(START, "planner")
builder.add_edge("planner", "agent")
builder.add_edge("agent", END)

new_expert_graph = builder.compile()
```

`langgraph.json` - LangGraph配置：
```json
{
  "graphs": {
    "new-expert-v1": "./graph.py:new_expert_graph"
  },
  "env": ".env",
  "python_version": "3.12",
  "dependencies": [
    ".."
  ]
}
```

`.env.example` - 环境变量示例：
```bash
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4
```

3. **更新服务管理脚本**：

编辑 `test_expert_services.sh`，在 `SERVICES` 数组中添加新服务：
```bash
SERVICES=(
    # ... 现有服务
    "new:new_expert:8006:new-expert-v1"
)
```

## 🧪 测试说明

### 运行集成测试

1. **设置测试环境变量**：
```bash
export STREAMING_TEST_MODE=true
export EXPERT_MAX_RETRIES=3
export EXPERT_REQUEST_TIMEOUT=600
```

2. **启动专家服务**：
```bash
./test_expert_services.sh start
```

3. **运行测试**：
```bash
# 运行所有集成测试
pytest ../../../integration_tests/ -v --timeout=600 --tb=short

# 运行特定测试
pytest ../../../integration_tests/test_e2e_service_calls.py::TestE2EServiceCalls::test_IT_E2E_001_write_service -v
```

### 手动测试服务

使用 curl 直接测试服务：

```bash
# 1. 创建助手
ASSISTANT_ID=$(curl -X POST http://localhost:8001/assistants \
  -H "Content-Type: application/json" \
  -d '{"graph_id": "write-expert-v1", "metadata": {"name": "Test"}}' \
  | jq -r '.assistant_id')

# 2. 创建线程
THREAD_ID=$(curl -X POST http://localhost:8001/threads \
  -H "Content-Type: application/json" \
  -d '{}' \
  | jq -r '.thread_id')

# 3. 发送请求
curl -N -X POST http://localhost:8001/runs/stream \
  -H "Content-Type: application/json" \
  -d "{
    \"thread_id\": \"$THREAD_ID\",
    \"assistant_id\": \"$ASSISTANT_ID\",
    \"input\": {
      \"messages\": [{\"type\": \"human\", \"content\": \"写一篇关于AI的文章\"}]
    },
    \"stream_mode\": \"values\"
  }"
```

### 测试设计专家服务

设计专家服务支持两种请求格式：

#### 1. 图像生成测试
```bash
# 创建助手和线程
ASSISTANT_ID=$(curl -X POST http://localhost:8005/assistants \
  -H "Content-Type: application/json" \
  -d '{"graph_id": "design-expert-v1"}' \
  | jq -r '.assistant_id')

THREAD_ID=$(curl -X POST http://localhost:8005/threads \
  -H "Content-Type: application/json" \
  -d '{}' \
  | jq -r '.thread_id')

# 发送生成请求
curl -N -X POST http://localhost:8005/runs/stream \
  -H "Content-Type: application/json" \
  -d "{
    \"thread_id\": \"$THREAD_ID\",
    \"assistant_id\": \"$ASSISTANT_ID\",
    \"input\": {
      \"messages\": [{
        \"type\": \"human\",
        \"content\": \"{\\\"query\\\": \\\"生成一个校庆海报\\\", \\\"image\\\": \\\"\\\"}\"
      }]
    },
    \"stream_mode\": \"updates\"
  }"
```

#### 2. 图像修改测试
```bash
curl -N -X POST http://localhost:8005/runs/stream \
  -H "Content-Type: application/json" \
  -d "{
    \"thread_id\": \"$THREAD_ID\",
    \"assistant_id\": \"$ASSISTANT_ID\",
    \"input\": {
      \"messages\": [{
        \"type\": \"human\",
        \"content\": \"{\\\"query\\\": \\\"改为简约风格\\\", \\\"image\\\": \\\"data:image/png;base64,...\\\"}\"
      }]
    },
    \"stream_mode\": \"updates\"
  }"
```

#### 3. 使用测试脚本
```bash
# 运行设计专家API测试
cd design_expert
python test_api.py
```

输出格式说明：
- 设计专家返回的是 `ToolMessage` 格式
- `additional_kwargs` 包含 `toolCalls` 结构
- 图片以 base64 数组形式返回

## 🔧 故障排查

### 常见问题

1. **服务无法启动**
   - 检查端口是否被占用：`lsof -i :8001`
   - 查看日志文件：`tail -f logs/write.log`
   - 确认环境变量配置正确

2. **连接超时**
   - 增加超时时间：`export EXPERT_REQUEST_TIMEOUT=900`
   - 检查网络连接和防火墙设置

3. **认证失败**
   - 验证 API 密钥是否正确
   - 检查 API 配额和限制

### 日志查看

```bash
# 查看所有服务日志
tail -f logs/*.log

# 查看特定服务日志
tail -f logs/write.log

# 查看错误日志
grep ERROR logs/*.log
```

### 调试技巧

1. **启用详细日志**：
```bash
export DEBUG=true
export LANGCHAIN_TRACING_V2=true
```

2. **单步调试**：
在 `graph.py` 中添加断点：
```python
import pdb; pdb.set_trace()
```

3. **性能分析**：
使用 LangSmith 追踪请求链路和性能瓶颈

## 📊 监控和性能

### 服务健康检查

每个服务都提供健康检查端点：
```bash
curl http://localhost:8001/health
```

### 性能指标

- 请求响应时间
- 并发处理能力
- 资源使用情况（CPU、内存）

### 日志轮转

建议配置日志轮转以避免磁盘空间问题：
```bash
# 使用 logrotate 配置
/path/to/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

## 📝 API 参考

### 通用端点

所有专家服务都实现以下标准端点：

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/assistants` | POST | 创建助手实例 |
| `/threads` | POST | 创建会话线程 |
| `/runs/stream` | POST | 流式执行请求 |
| `/health` | GET | 健康检查 |

### 请求格式

```json
{
  "thread_id": "thread-uuid",
  "assistant_id": "assistant-uuid",
  "input": {
    "messages": [
      {
        "type": "human",
        "content": "用户请求内容"
      }
    ]
  },
  "stream_mode": "values"
}
```

### 响应格式

流式响应使用 Server-Sent Events (SSE) 格式：
```
event: data
data: {"type": "message", "content": "响应内容"}

event: end
data: {"status": "completed"}
```

#### 设计专家响应格式
设计专家服务返回特殊的 `ToolMessage` 格式，用于传递图像数据：

```json
{
  "agent": {
    "messages": [{
      "type": "tool",
      "content": "已成功生成设计图",
      "tool_call_id": "design_task",
      "additional_kwargs": {
        "toolCalls": [{
          "id": "design_123456",
          "function": {
            "name": "image",
            "arguments": "[\"data:image/png;base64,iVBORw0...\"]"
          },
          "type": "function"
        }],
        "name": "image"
      }
    }]
  }
}
```

输入格式支持：
- JSON格式：`{"query": "设计需求", "image": "base64图片或空字符串"}`
- 纯文本：直接发送设计需求文本
- 特殊输入：发送 `"？"` 生成示例设计

## 🤝 贡献指南

欢迎贡献代码和改进建议！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支：`git checkout -b feature/new-expert`
3. 提交更改：`git commit -m 'Add new expert service'`
4. 推送分支：`git push origin feature/new-expert`
5. 创建 Pull Request

## 📄 许可证

本项目遵循项目根目录的许可证文件。

## 📮 联系方式

如有问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件到项目维护者

---
*最后更新：2025年9月17日*
*版本：1.1.0 - 添加设计专家服务支持*
