<div align="center">

<p align="center">
  <img src="images/logo2.jpeg" alt="Logo" width="80" style="vertical-align: middle; margin-right: 20px;">
  <span style="font-size: 2em; font-weight: bold; vertical-align: middle;">JoinAI-Agent</span>
</p>

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)
![Contributions](https://img.shields.io/badge/Contributions-welcome-green.svg)

**A General AI Agent That Thinks and Acts**

Systematically building a complete agent capability closed loop from perception, planning, execution to collaboration for complex task scenarios.

[中文](README_CN.md) • [Framework Performance](#framework-performance) • [Project Architecture](#project-architecture) • [Quick Start](#quick-start) • [Examples](#examples)


</div>

---
## What is JoinAI-Agent

JoinAI-Agent is born from China Mobile's self-developed Jiutian·Juzhi Intelligent Agent Platform. As an AI agent that "thinks and acts", JoinAI-Agent pioneers the definition of next-generation enterprise-level agent engine core capabilities, systematically building a complete agent capability closed loop from perception, planning, execution to collaboration for complex task scenarios, marking an important breakthrough for China Mobile in the field of general agent systems. The open source of JoinAI-Agent will break down technical barriers, accelerate industry collaboration, and continuously empower intelligent upgrades across industries.

This time we have open-sourced the standard framework and basic capabilities of JoinAI-Agent. The entire system adopts a frontend-backend separation architecture, with the frontend supporting file uploads, sandbox task tracking, etc., and the backend based on a DAG execution engine, with built-in multiple professional sub-agents (such as information integration, code expert, report generation, etc.) and a rich tool ecosystem (such as search, file processing, etc.).

## 📋 Framework Performance <a id="framework-performance"></a>

In the GAIA benchmark test, JoinAI-Agent achieved a comprehensive score of 90.70, ranking first on the leaderboard.

![GAIA Leaderboard](images/GAIA.png)

## 🏗️ Project Architecture <a id="project-architecture"></a>

![Project Architecture Diagram](images/JoinAI.png)

This open source project open-sources the frontend, agent's react mode, multiple sub-agents (reporter, researcher, coder), various standardized interaction protocols, sandbox, etc.

### **Features and Advantages**

- **End-to-End Complete Product**: One-click deployment, out-of-the-box, supporting secondary development and customized extensions
- **Standardized Protocol Support**: Integrates MCP and A2A protocols, supporting pluggable extensions of tools and agents
- **Secure Sandbox Execution**: Based on E2B sandbox environment, providing secure code execution capabilities, supporting Shell, file operations, browser automation, etc.
- **Flexible Architecture Design**: Frontend-backend separation, modular design, easy to integrate and maintain

### **Core Features**

JoinAI-Agent is a powerful agent engine that integrates the following core capabilities:
- 🔧 **Tool Integration**: Supports various tools including web search, file operations, code execution, and more
- 🤝 **A2A Support**: Supports A2A protocol for inter-agent collaboration
- 🔌 **MCP Support**: Integrates MCP protocol, supporting extensible tools
- 🖥️ **Sandbox Execution**: Secure code execution environment
- 💬 **Web Interface**: Simple and easy-to-use frontend interface with file upload support
- 🌐 **Browser-Use**: Supports browser automation operations, including clicking, typing, scrolling, and other operations, enabling automated web interaction and task execution

## 🚀 Quick Start <a id="quick-start"></a>

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- Node.js 20+ (for local development)

### Deploy with Docker Compose (Recommended)

1. **Clone the repository**

```bash
git clone https://github.com/opencmit/JoinAI-Agent.git
cd JoinAI-Agent
```

2. **Configure environment variables**

Backend service: Copy `backend/.env.template` to `backend/.env`, and fill in the necessary keys in the `.env` file. Model and sandbox configurations are required. E2B_API_KEY can be applied at https://e2b.dev/:

**Model examples:**

```env
# OpenAI Official API
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-openai-api-key-here
BASE_LLM=gpt-5
```

```env
# Compatible with other model API services
OPENAI_BASE_URL=https://api.siliconflow.cn/v1
OPENAI_API_KEY=your-api-key
BASE_LLM=deepseek-ai/DeepSeek-V3.2-Exp
```

To use JINA, SERPER, or Bocha search tools, you need to apply for JINA_API_KEY (https://jina.ai/), SERPER_API_KEY (https://serper.dev), and BOCHA_API_KEY (https://bocha.cn/) and add them to the `.env` file.

Frontend service: Copy `frontend/.env.template` to `frontend/.env`, and fill in the necessary keys in the `.env` file. The `E2B_API_KEY` must match the `E2B_API_KEY` in the backend `.env` file.

A2A agent: An image parsing agent is preconfigured. To use it, copy `backend/a2a_agent/pic_agent/.env.template` to `backend/a2a_agent/pic_agent/.env`, fill in the VL model information in the `.env` file, and upload images via attachment.
```env
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=sk-your-openai-api-key-here
BASE_LLM=qwen-vl-plus
```

3. **Start services**

```bash
docker-compose up -d
```

4. **Access the application**

- Frontend interface: http://localhost:9094

![Frontend interface](images/frontend.png)

- Backend API: http://localhost:18100

### Local Development

#### Backend Development

```bash
cd backend
pip install -r requirements.txt

# Test backend service
python test_demo.py
```

#### Frontend Development

```bash
cd frontend
pnpm install
pnpm dev
```

### MCP Configuration

MCP tool configuration is located in `backend/config/mcp_server.json`. Serper and Jina search tools are already configured. After configuring the corresponding keys, they can be used. Users can configure MCP tools themselves.

### A2A Configuration

A2A agent configuration is in `backend/config/a2a_server.json`. An image parsing agent is preconfigured. After configuring the corresponding keys, it can be used. Users can configure A2A agents themselves.

## 📹 Examples <a id="examples"></a>

<table>
<tr>
<td width="50%">

**Browser-Use**
Fill in the API key in the browser-use section of `backend/config/mcp_server.json` (https://cloud.browser-use.com/), then the agent can automatically operate web pages through browser tools, including clicking, typing, scrolling, and other operations, enabling automated web interaction and task execution.

https://github.com/user-attachments/assets/a161f4fa-c894-4ecd-b415-defd3bdf2dbf

</td>
<td width="50%">

**A2A_Image Parsing**
An image parsing agent has been integrated via A2A. Configure VL model information in `backend/a2a_agent/pic_agent/.env`, and upload images via attachment to use it.

https://github.com/user-attachments/assets/3fc43ca2-f5b6-461f-a62e-4f4b18e58e44

</td>
</tr>
<tr>
<td width="50%">

**Report Writing**
Enter a report topic, fill in Serper and Jina keys in `backend/.env`, collect relevant information about the topic by calling search tools such as Serper and Jina, and the report agent will complete the report writing.

https://github.com/user-attachments/assets/37a83da1-def8-415b-b125-9c4d651acc45

</td>
<td width="50%">

**Attachment Processing**
Supports uploading attachments in various formats. The agent can read and process attachment content, including text files, images, etc. Text attachments are converted to markdown format before subsequent tasks.

https://github.com/user-attachments/assets/b50b0535-fba5-4933-a648-772ff02d7ce0

</td>
</tr>
</table>

## 🔒 Security Considerations

- Sandbox environment is enabled by default to ensure secure code execution
- Sensitive configurations are managed through environment variables
- Do not commit API keys to the code repository

## 📝 ToDoList
- [ ] Plan reasoning mode
- [ ] More tool support
- [ ] Multi-agent memory
- [ ] Rich execution environments

## 📄 License

This project is licensed under the [Apache License 2.0](LICENSE) open source license.

---

**Note**: This project is under active development. APIs and configurations may change. Please refer to the latest documentation and code updates.

