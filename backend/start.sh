#!/bin/bash
set -e

# 等待端口就绪的函数
wait_for_port() {
    # 优先使用环境变量 JOINAI_MCP_HOST，如果未设置则默认为 127.0.0.1
    local host="${JOINAI_MCP_HOST:-127.0.0.1}"
    local port=$1
    local service_name=$2
    local timeout=15
    local start_time=$(date +%s)

    echo "Waiting for $service_name on port $port..."
    while ! nc -z $host $port >/dev/null 2>&1; do
        current_time=$(date +%s)
        elapsed=$((current_time - start_time))
        if [ $elapsed -ge $timeout ]; then
            echo "Timeout waiting for $service_name on port $port (skipping)"
            return 1
        fi
        sleep 1
    done
    echo "$service_name is ready on port $port"
    return 0
}

# 尝试等待几个核心 MCP 服务的端口 (Serper: 7801, SerpAPI: 7802, Jina: 7803)
# 注意：run_all.py 可能根据环境变量跳过某些服务，所以这里只是尽力等待，超时不报错
# 至少等待 2 秒让 run_all.py 有机会启动子进程
sleep 2

# 如果配置了对应的 API KEY，尝试等待特定端口
if [ ! -z "$SERPER_API_KEY" ]; then
    wait_for_port 7801 "Serper MCP"
fi

if [ ! -z "$SERPAPI_API_KEY" ]; then
    wait_for_port 7802 "SerpAPI MCP"
fi

if [ ! -z "$JINA_API_KEY" ]; then
    wait_for_port 7803 "Jina MCP"
fi

# Baidu 和 DuckDuckGo 不需要 API KEY，但默认会由 run_all.py 启动
# Baidu: 7805, DuckDuckGo: 7806
wait_for_port 7805 "Baidu MCP"
wait_for_port 7806 "DuckDuckGo MCP"

# 启动 LangGraph API (前台运行)
echo "Starting LangGraph API..."
exec uvicorn langgraph_api.server:app --host 0.0.0.0 --port 8000
