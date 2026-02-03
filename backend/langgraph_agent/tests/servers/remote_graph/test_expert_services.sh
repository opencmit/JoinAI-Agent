#!/bin/bash

# Expert Services Manager Script
# 用于管理专家智能体测试服务器
# 使用方式: ./test_expert_services.sh {start|stop|status|restart} [service_name]

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
LOGS_DIR="$SCRIPT_DIR/logs"

# 确保logs目录存在
mkdir -p "$LOGS_DIR"

# 服务配置数组 (name:directory:port:graph_id)
SERVICES=(
    "write:write_expert:8001:write-expert-v1"
    "ppt:ppt_expert:8002:ppt-expert-v1" 
    "web:web_expert:8003:web-expert-v1"
    "broadcast:broadcast_expert:8004:broadcast-expert-v1"
    "design:design_expert:8005:design-expert-v1"
)

# 日志函数无颜色输出

# 日志函数
log_info() {
    echo "[INFO] $1"
}

log_success() {
    echo "[SUCCESS] $1"
}

log_warning() {
    echo "[WARNING] $1"
}

log_error() {
    echo "[ERROR] $1"
}

# 检查命令是否存在
check_command() {
    if ! command -v langgraph &> /dev/null; then
        log_error "langgraph 命令未找到，请确保已安装 langgraph-cli"
        return 1
    fi
    return 0
}

# 获取服务PID
get_service_pid() {
    local service_name=$1
    local pid_file="$LOGS_DIR/${service_name}.pid"
    
    if [[ -f "$pid_file" ]]; then
        cat "$pid_file"
    else
        echo ""
    fi
}

# 检查进程是否运行
is_process_running() {
    local pid=$1
    if [[ -n "$pid" ]] && ps -p "$pid" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 检查端口是否被占用
is_port_in_use() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 获取服务配置
get_service_config() {
    local service_name=$1
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r name directory port graph_id <<< "$service"
        if [[ "$name" == "$service_name" ]]; then
            echo "$directory:$port:$graph_id"
            return 0
        fi
    done
    return 1
}

# 启动单个服务
start_service() {
    local service_name=$1
    local config
    config=$(get_service_config "$service_name")
    
    if [[ -z "$config" ]]; then
        log_error "未知服务: $service_name"
        return 1
    fi
    
    IFS=':' read -r directory port graph_id <<< "$config"
    local service_dir="$SCRIPT_DIR/$directory"
    local pid_file="$LOGS_DIR/${service_name}.pid"
    local log_file="$LOGS_DIR/${service_name}.log"
    
    # 检查服务目录是否存在
    if [[ ! -d "$service_dir" ]]; then
        log_error "服务目录不存在: $service_dir"
        return 1
    fi
    
    # 检查服务是否已经在运行
    local existing_pid=$(get_service_pid "$service_name")
    if is_process_running "$existing_pid"; then
        log_warning "服务 $service_name 已经在运行 (PID: $existing_pid)"
        return 0
    fi
    
    # 检查端口是否被占用
    if is_port_in_use "$port"; then
        log_error "端口 $port 已被占用，无法启动服务 $service_name"
        return 1
    fi
    
    log_info "启动服务 $service_name (端口: $port)..."
    
    # 删除旧的日志文件并创建新的
    if [[ -f "$log_file" ]]; then
        rm -f "$log_file"
        log_info "删除旧日志文件: $log_file"
    fi
    > "$log_file"
    log_info "创建新日志文件: $log_file"
    
    # 切换到服务目录并启动服务
    cd "$service_dir" || return 1
    
    # 启动 langgraph 服务
    nohup langgraph dev --port "$port" --host localhost \
        >> "$log_file" 2>&1 & 
    
    local pid=$!
    echo "$pid" > "$pid_file"
    
    # 等待服务启动
    sleep 3
    
    # 验证服务是否成功启动
    if is_process_running "$pid" && is_port_in_use "$port"; then
        log_success "服务 $service_name 启动成功 (PID: $pid, 端口: $port)"
        return 0
    else
        log_error "服务 $service_name 启动失败"
        rm -f "$pid_file"
        return 1
    fi
}

# 停止单个服务
stop_service() {
    local service_name=$1
    local pid_file="$LOGS_DIR/${service_name}.pid"
    local pid=$(get_service_pid "$service_name")
    
    if [[ -z "$pid" ]]; then
        log_warning "服务 $service_name 未运行或PID文件不存在"
        return 0
    fi
    
    if is_process_running "$pid"; then
        log_info "停止服务 $service_name (PID: $pid)..."
        kill "$pid"
        
        # 等待进程结束
        local count=0
        while is_process_running "$pid" && [[ $count -lt 10 ]]; do
            sleep 1
            ((count++))
        done
        
        if is_process_running "$pid"; then
            log_warning "强制停止服务 $service_name"
            kill -9 "$pid"
            sleep 2
        fi
        
        if ! is_process_running "$pid"; then
            log_success "服务 $service_name 已停止"
            rm -f "$pid_file"
            return 0
        else
            log_error "无法停止服务 $service_name"
            return 1
        fi
    else
        log_warning "服务 $service_name 进程已不存在，清理PID文件"
        rm -f "$pid_file"
        return 0
    fi
}

# 检查单个服务状态
check_service_status() {
    local service_name=$1
    local config
    config=$(get_service_config "$service_name")
    
    if [[ -z "$config" ]]; then
        log_error "未知服务: $service_name"
        return 1
    fi
    
    IFS=':' read -r directory port graph_id <<< "$config"
    local pid=$(get_service_pid "$service_name")
    
    printf "%-12s" "$service_name:"
    
    if [[ -n "$pid" ]] && is_process_running "$pid"; then
        if is_port_in_use "$port"; then
            printf "运行中 (PID: %s, 端口: %s)\n" "$pid" "$port"
            return 0
        else
            printf "异常 (进程存在但端口未监听)\n"
            return 1
        fi
    else
        printf "已停止\n"
        return 1
    fi
}

# 重启单个服务
restart_service() {
    local service_name=$1
    log_info "重启服务 $service_name..."
    stop_service "$service_name"
    sleep 2
    start_service "$service_name"
}

# 启动所有服务
start_all() {
    log_info "启动所有专家服务..."
    local success_count=0
    local total_count=${#SERVICES[@]}
    
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r service_name directory port graph_id <<< "$service"
        if start_service "$service_name"; then
            ((success_count++))
        fi
    done
    
    log_info "启动完成: $success_count/$total_count 个服务成功启动"
}

# 停止所有服务
stop_all() {
    log_info "停止所有专家服务..."
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r service_name directory port graph_id <<< "$service"
        stop_service "$service_name"
    done
}

# 检查所有服务状态
status_all() {
    echo "专家服务状态:"
    echo "============"
    local running_count=0
    local total_count=${#SERVICES[@]}
    
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r service_name directory port graph_id <<< "$service"
        if check_service_status "$service_name"; then
            ((running_count++))
        fi
    done
    
    echo "============"
    echo "运行中: $running_count/$total_count"
}

# 重启所有服务
restart_all() {
    log_info "重启所有专家服务..."
    stop_all
    sleep 3
    start_all
}

# 测试服务功能
test_service() {
    local service_name=$1
    local config
    config=$(get_service_config "$service_name")
    
    if [[ -z "$config" ]]; then
        log_error "未知服务: $service_name"
        return 1
    fi
    
    IFS=':' read -r directory port graph_id <<< "$config"
    
    log_info "测试服务 $service_name..."
    
    # 检查服务是否运行
    if ! check_service_status "$service_name" > /dev/null; then
        log_error "服务 $service_name 未运行，无法测试"
        return 1
    fi
    
    # 测试HTTP连接
    local url="http://localhost:$port"
    if curl -s -f "$url" > /dev/null; then
        log_success "服务 $service_name HTTP连接测试通过"
        return 0
    else
        log_error "服务 $service_name HTTP连接测试失败"
        return 1
    fi
}

# 测试所有服务
test_all() {
    log_info "测试所有专家服务..."
    local success_count=0
    local total_count=${#SERVICES[@]}
    
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r service_name directory port graph_id <<< "$service"
        if test_service "$service_name"; then
            ((success_count++))
        fi
    done
    
    log_info "测试完成: $success_count/$total_count 个服务测试通过"
}

# 显示帮助信息
show_help() {
    echo "专家智能体服务管理脚本"
    echo "使用方法:"
    echo "  $0 {start|stop|status|restart|test} [service_name]"
    echo ""
    echo "命令:"
    echo "  start [service]   - 启动服务(不指定则启动所有)"
    echo "  stop [service]    - 停止服务(不指定则停止所有)"
    echo "  status [service]  - 查看服务状态(不指定则查看所有)"
    echo "  restart [service] - 重启服务(不指定则重启所有)"
    echo "  test [service]    - 测试服务(不指定则测试所有)"
    echo ""
    echo "可用服务:"
    for service in "${SERVICES[@]}"; do
        IFS=':' read -r service_name directory port graph_id <<< "$service"
        echo "  $service_name (端口: $port)"
    done
}

# 主函数
main() {
    # 检查langgraph命令
    if ! check_command; then
        exit 1
    fi
    
    local command=$1
    local service_name=$2
    
    case "$command" in
        "start")
            if [[ -n "$service_name" ]]; then
                start_service "$service_name"
            else
                start_all
            fi
            ;;
        "stop")
            if [[ -n "$service_name" ]]; then
                stop_service "$service_name"
            else
                stop_all
            fi
            ;;
        "status")
            if [[ -n "$service_name" ]]; then
                check_service_status "$service_name"
            else
                status_all
            fi
            ;;
        "restart")
            if [[ -n "$service_name" ]]; then
                restart_service "$service_name"
            else
                restart_all
            fi
            ;;
        "test")
            if [[ -n "$service_name" ]]; then
                test_service "$service_name"
            else
                test_all
            fi
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo "无效命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"
