# 🐳 MCP A2A Knowledge Server 部署指南

> **📢 重要提示**
>
> 该Docker镜像构建为 **Linux/AMD64** 架构，适用于x86_64服务器。
> 文件大小：143MB | SHA256: `f56a076d02895c8aeada5601c7c154531addc95642a6d006876f1e8410ef16b9`

## 📋 概述

本文档提供 **MCP A2A Knowledge Server** 在Linux系统上的Docker手动部署指南。该服务器整合了MCP工具调用和A2A智能体功能，提供统一的API接口。

### 🎯 服务特性

- **MCP工具调用**：支持6种基础工具（计算器、天气、文件操作等）
- **A2A智能体**：集成5个专业智能体（天气、数据分析、文档编写、代码生成、知识问答）
- **知识库检索**：内置知识库查询和文档管理
- **SSE流式响应**：支持实时流式数据传输
- **统一API**：兼容MCP和A2A协议

---

## 🔧 系统要求

- **操作系统**：Linux (Ubuntu 18.04+, CentOS 7+, RHEL 7+)
- **架构**：x86_64 (AMD64) ⭐ **推荐**
- **内存**：至少 2GB RAM
- **存储**：至少 5GB 可用空间
- **Docker版本**：20.10.0 或更高版本

### 📦 镜像信息

- **镜像架构**：`linux/amd64`
- **镜像大小**：143MB (压缩后)
- **基础镜像**：`python:3.12-slim`
- **SHA256校验**：`f56a076d02895c8aeada5601c7c154531addc95642a6d006876f1e8410ef16b9`

### 🖥️ 架构兼容性

- **✅ 完全兼容**：x86_64/AMD64 Linux服务器
- **⚠️ 需要模拟**：ARM64 Linux服务器（通过Docker平台仿真）
- **❌ 不支持**：Windows、macOS 容器运行时

---

## 🚀 部署步骤

### 1. 文件上传

```bash
# 上传部署文件到Linux服务器
scp mcp-a2a-knowledge-server-1.0.0.tar* user@server:/opt/mcp-server/
```

### 2. 验证文件完整性

```bash
# 验证SHA256校验和
sha256sum -c mcp-a2a-knowledge-server-1.0.0.tar.sha256

# 查看文件信息
ls -lh mcp-a2a-knowledge-server-1.0.0.tar*
```

### 3. 加载Docker镜像

```bash
# 加载镜像文件
docker load -i mcp-a2a-knowledge-server-1.0.0.tar

# 验证镜像已加载
docker images | grep mcp-a2a-knowledge-server

# 检查镜像架构（可选）
docker inspect mcp-a2a-knowledge-server:1.0.0 | grep -A 2 "Architecture"
```

### 4. 创建数据目录

```bash
# 创建数据持久化目录
mkdir -p /opt/mcp-server/data
mkdir -p /opt/mcp-server/logs

# 设置目录权限
chmod 755 /opt/mcp-server/data
chmod 755 /opt/mcp-server/logs
```

### 5. 启动服务

```bash
# 基础启动
docker run -d \
  --name mcp-a2a-server \
  -p 18585:18585 \
  --restart unless-stopped \
  mcp-a2a-knowledge-server:1.0.0

# 推荐启动（带数据持久化和资源限制）
docker run -d \
  --name mcp-a2a-server \
  -p 18585:18585 \
  -v /opt/mcp-server/data:/app/data \
  -v /opt/mcp-server/logs:/app/logs \
  --restart unless-stopped \
  mcp-a2a-knowledge-server:1.0.0
```

### 6. 验证服务

```bash
# 健康检查
curl http://localhost:18585/health

# 检查容器状态
docker ps | grep mcp-a2a-server

# 查看容器日志
docker logs mcp-a2a-server
```

---

## 🔌 API接口

### 基础信息

- **服务地址**：`http://localhost:18585`
- **协议**：HTTP/1.1
- **数据格式**：JSON

### 主要端点

#### 健康检查

```bash
curl http://localhost:18585/health
```

#### A2A智能体

```bash
# 智能体列表
curl http://localhost:18585/agents

# 智能体调用（SSE流式）
curl -N -X POST http://localhost:18585/mae/api/v1.0/rest/a2aChat \
  -H "Content-Type: application/json" \
  -d '{
    "agentId": "weather-agent",
    "sessionId": "session_123",
    "messages": [{"type": "text", "content": "北京今天天气怎么样？"}]
  }'
```

#### MCP工具

```bash
# 工具列表
curl http://localhost:18585/agentV2/multi-agents/mcp/api/tool/list

# 工具调用
curl -X POST http://localhost:18585/agentV2/multi-agents/mcp/api/tool/callTool \
  -H "Content-Type: application/json" \
  -d '{
    "toolId": "calculator",
    "arguments": {"expression": "2+3*4"}
  }'
```

#### 知识库检索

```bash
curl -X POST http://localhost:18585/agentV2/multi-agents/mcp/knowledge/retrieval \
  -H "Content-Type: application/json" \
  -d '{
    "content": "搜索内容",
    "dbList": [{"name": "数据库ID"}]
  }'
```

### 可用智能体

| 智能体ID            | 名称         | 功能描述         |
| ------------------- | ------------ | ---------------- |
| `weather-agent`   | 天气助手     | 天气查询和预报   |
| `data-analyst`    | 数据分析师   | 数据分析和可视化 |
| `document-writer` | 文档编写助手 | 文档创建和编辑   |
| `code-generator`  | 代码生成器   | 代码生成和优化   |
| `knowledge-agent` | 知识问答专家 | 知识库查询       |

---

## 🛠️ 服务管理

### 基础管理命令

```bash
# 查看服务状态
docker ps | grep mcp-a2a-server

# 查看服务日志
docker logs -f mcp-a2a-server

# 停止服务
docker stop mcp-a2a-server

# 启动服务
docker start mcp-a2a-server

# 重启服务
docker restart mcp-a2a-server

# 删除服务
docker stop mcp-a2a-server && docker rm mcp-a2a-server
```

### 环境变量配置

```bash
# 使用环境变量启动
docker run -d \
  --name mcp-a2a-server \
  -p 18585:18585 \
  -e FLASK_ENV=production \
  -e LOG_LEVEL=INFO \
  -e OPENAI_API_KEY=your_key_here \
  -v /opt/mcp-server/data:/app/data \
  -v /opt/mcp-server/logs:/app/logs \
  --restart unless-stopped \
  mcp-a2a-knowledge-server:1.0.0
```

### 数据目录结构

```
/opt/mcp-server/
├── data/
│   ├── knowledge/          # 知识库数据
│   ├── sessions/          # 会话数据
│   └── cache/             # 缓存文件
└── logs/
    ├── app.log           # 应用日志
    ├── access.log        # 访问日志
    └── error.log         # 错误日志
```

---

## 🔧 故障排除

### 常见问题

#### 1. 容器启动失败

```bash
# 检查容器日志
docker logs mcp-a2a-server

# 检查镜像完整性
docker inspect mcp-a2a-knowledge-server:1.0.0

# 重新启动容器
docker rm -f mcp-a2a-server
docker run -d --name mcp-a2a-server -p 18585:18585 mcp-a2a-knowledge-server:1.0.0
```

#### 2. 端口冲突

```bash
# 检查端口占用
netstat -tulpn | grep 18585
lsof -i :18585

# 使用其他端口
docker run -d --name mcp-a2a-server -p 8080:18585 mcp-a2a-knowledge-server:1.0.0

# 停止占用端口的进程
sudo kill -9 $(lsof -t -i:18585)
```

#### 3. 内存不足

```bash
# 限制容器内存使用
docker run -d --name mcp-a2a-server \
  -p 18585:18585 \
  --memory=1g \
  --memory-swap=2g \
  mcp-a2a-knowledge-server:1.0.0

# 检查系统资源
free -h
df -h
docker stats mcp-a2a-server
```

#### 4. 架构兼容性问题

```bash
# 检查系统架构
uname -m

# 检查Docker架构支持
docker version | grep -i arch

# ARM64服务器运行AMD64镜像（会有性能警告，但功能正常）
docker run -d --name mcp-a2a-server \
  -p 18585:18585 \
  --platform linux/amd64 \
  mcp-a2a-knowledge-server:1.0.0
```

#### 5. 服务调试

```bash
# 交互式进入容器
docker exec -it mcp-a2a-server /bin/bash

# 手动启动服务（调试模式）
docker run -it --rm -p 18585:18585 mcp-a2a-knowledge-server:1.0.0 /bin/bash
```

---

## 🔄 更新升级

```bash
# 1. 停止当前服务
docker stop mcp-a2a-server

# 2. 备份数据
docker cp mcp-a2a-server:/app/data /backup/mcp-data-$(date +%Y%m%d)

# 3. 移除旧容器
docker rm mcp-a2a-server

# 4. 加载新镜像
docker load -i mcp-a2a-knowledge-server-new.tar

# 5. 启动新容器
docker run -d --name mcp-a2a-server \
  -p 18585:18585 \
  -v /opt/mcp-server/data:/app/data \
  -v /opt/mcp-server/logs:/app/logs \
  --restart unless-stopped \
  mcp-a2a-knowledge-server:new-version
```
