# 前端内容
# FROM node:20-alpine AS frontend-builder
# WORKDIR /app/frontend
# COPY frontend/package.json frontend/package-lock.json ./
# RUN npm install
# COPY frontend/ ./
# RUN npm run build

# 使用LangGraph官方镜像
FROM langchain/langgraph-api:3.12

USER root
# 更换 pip 源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources && \
        sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources; \
    fi && \
    if [ -f /etc/apt/sources.list ]; then \
        sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list && \
        sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list; \
    fi

# 基础编译工具
RUN apt-get update && apt-get install -y build-essential curl netcat-openbsd && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*


WORKDIR /deps/joinai
COPY . .

RUN pip install -e .
RUN chmod +x start.sh

ENV LANGGRAPH_CONFIG=langgraph.json

CMD ["./start.sh"]
