# Pic-Agent 多模态识别智能体

## 简介

Pic-Agent 是一个基于 大模型 的多模态识别 A2A (Agent-to-Agent) 智能体，专门用于处理图像和文本的多模态分析任务。它能够智能识别用户输入中的图片URL、base64编码或文件路径，并自动调用相应的工具进行处理。

## 功能特性

- **多模态识别**: 支持图像、文本以及图像+文本的综合分析
- **智能提取**: 自动从用户输入中提取图片URL和文本内容
- **A2A通信**: 基于 python-a2a 协议，支持与其他智能体无缝通信
- **灵活输入**: 支持多种图片输入格式：
  - HTTP/HTTPS URL
  - Base64编码
  - 本地文件路径
- **容错性强**: 内置多种容灾机制，确保服务稳定性

## 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   用户输入      │ -> │  Pic-Agent      │ -> │   OpenAI API    │
│                 │    │  多模态识别器   │    │   GPT-4o        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  A2A 通信协议  │
                       │                 │
                       └─────────────────┘
```

## 安装说明

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   pip install -r requirements.txt
   cd juzhigongfang/a2a_agent/pic-agent
   ```

2. **配置环境变量**

   创建 `.env` 文件在项目根目录：
   ```bash
   # OpenAI 配置
   OPENAI_API_KEY=your_openai_api_key_here
   OPENAI_BASE_URL=https://api.openai.com/v1  # 可选，默认使用官方API
   OPENAI_MODEL=gpt-4o  # 推荐使用 gpt-4o，支持多模态

   # 智能体配置
   AGENT_NAME=multimodal-recognizer
   AGENT_HOST=0.0.0.0
   AGENT_PORT=8000

   # 日志配置
   LOG_LEVEL=INFO
   ```

## 使用方法

### 启动智能体

```bash
python main.py
```

智能体将在配置的端口启动服务，输出类似：
```
2024-01-01 12:00:00 - __main__ - INFO - 正在启动多模态识别智能体: multimodal-recognizer
2024-01-01 12:00:00 - __main__ - INFO - 智能体服务启动在 0.0.0.0:8000
```


## 核心组件

### 1. MultimodalAgent (app/agent.py)
主智能体类，负责：
- A2A 通信协议处理
- 消息路由和分发
- 错误处理和容灾

### 2. MultimodalRecognizer (app/multimodal.py)
多模态识别核心，负责：
- 图像和文本的预处理
- OpenAI API 调用
- 结果格式化

### 3. 工具模块
- **image_utils.py**: 图像下载、编码转换
- **text_utils.py**: 文本预处理和清理
- **settings.py**: 配置管理

## 性能优化

- **智能缓存**: 使用 LRU 缓存减少重复计算
- **异步处理**: 支持异步图像下载和处理
- **容灾机制**: 多重 JSON 解析容灾，确保服务稳定性
- **内存管理**: 自动清理临时资源
