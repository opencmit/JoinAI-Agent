#!/bin/bash

# ===============================================
# MCP A2A Knowledge Server Docker 构建和打包脚本
# ===============================================

set -e  # 遇到错误即停止

# 配置变量
IMAGE_NAME="mcp-a2a-knowledge-server"
IMAGE_TAG="1.0.0"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"
EXPORT_FILE="${IMAGE_NAME}-${IMAGE_TAG}.tar"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装或未在PATH中找到"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 守护进程未运行"
        exit 1
    fi
    
    log_success "Docker 环境检查通过"
}

# 清理旧镜像
cleanup_old_images() {
    log_info "清理旧版本镜像..."
    
    # 删除同名镜像
    if docker images | grep -q "${IMAGE_NAME}"; then
        docker rmi $(docker images "${IMAGE_NAME}" -q) 2>/dev/null || true
        log_info "已清理旧版本镜像"
    fi
    
    # 清理dangling镜像
    if docker images -f "dangling=true" -q | grep -q .; then
        docker image prune -f
        log_info "已清理悬空镜像"
    fi
}

# 构建Docker镜像
build_image() {
    log_info "开始构建 Docker 镜像: ${FULL_IMAGE_NAME}"
    log_info "基础镜像: python:3.12-slim"
    
    # 显示构建上下文
    log_info "构建上下文目录: $(pwd)"
    log_info "使用Dockerfile: Dockerfile.mcp_a2a"
    
    # 执行构建
    docker build \
        --platform linux/amd64 \
        -f Dockerfile.mcp_a2a \
        -t "${FULL_IMAGE_NAME}" \
        --build-arg BUILD_DATE="$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --no-cache \
        .
    
    if [ $? -eq 0 ]; then
        log_success "镜像构建成功: ${FULL_IMAGE_NAME}"
    else
        log_error "镜像构建失败"
        exit 1
    fi
}

# 验证镜像
verify_image() {
    log_info "验证构建的镜像..."
    
    # 检查镜像是否存在
    if docker images | grep -q "${IMAGE_NAME}.*${IMAGE_TAG}"; then
        log_success "镜像验证通过"
        
        # 显示镜像信息
        log_info "镜像详细信息:"
        docker images "${IMAGE_NAME}:${IMAGE_TAG}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        
        # 显示镜像层信息
        log_info "镜像层数: $(docker history ${FULL_IMAGE_NAME} --quiet | wc -l)"
        
    else
        log_error "镜像验证失败"
        exit 1
    fi
}

# 运行测试
test_image() {
    log_info "启动容器进行功能测试..."
    
    # 启动容器
    CONTAINER_ID=$(docker run -d -p 18585:18585 --name "${IMAGE_NAME}-test" "${FULL_IMAGE_NAME}")
    
    if [ $? -eq 0 ]; then
        log_success "容器启动成功: ${CONTAINER_ID:0:12}"
        
        # 等待服务启动
        log_info "等待服务启动..."
        sleep 10
        
        # 健康检查
        if curl -f http://localhost:18585/health > /dev/null 2>&1; then
            log_success "健康检查通过"
        else
            log_warning "健康检查失败，但继续进行打包"
        fi
        
        # 停止并删除测试容器
        docker stop "${CONTAINER_ID}" > /dev/null
        docker rm "${CONTAINER_ID}" > /dev/null
        log_info "测试容器已清理"
        
    else
        log_error "容器启动失败"
        exit 1
    fi
}

# 导出镜像
export_image() {
    log_info "导出镜像到文件: ${EXPORT_FILE}"
    
    # 检查是否存在同名文件
    if [ -f "${EXPORT_FILE}" ]; then
        log_warning "文件 ${EXPORT_FILE} 已存在，将被覆盖"
        rm -f "${EXPORT_FILE}"
    fi
    
    # 导出镜像
    docker save "${FULL_IMAGE_NAME}" -o "${EXPORT_FILE}"
    
    if [ $? -eq 0 ]; then
        log_success "镜像导出成功: ${EXPORT_FILE}"
        
        # 显示文件信息
        FILE_SIZE=$(du -h "${EXPORT_FILE}" | cut -f1)
        log_info "文件大小: ${FILE_SIZE}"
        log_info "文件路径: $(pwd)/${EXPORT_FILE}"
        
        # 生成校验和
        CHECKSUM=$(sha256sum "${EXPORT_FILE}" | cut -d' ' -f1)
        echo "${CHECKSUM}  ${EXPORT_FILE}" > "${EXPORT_FILE}.sha256"
        log_info "SHA256 校验和: ${CHECKSUM}"
        
    else
        log_error "镜像导出失败"
        exit 1
    fi
}

# 显示使用说明
show_usage() {
    echo "==================================="
    echo "🐳 镜像构建和打包完成！"
    echo "==================================="
    echo ""
    echo "📦 导出文件:"
    echo "  - 镜像文件: ${EXPORT_FILE}"
    echo "  - 校验文件: ${EXPORT_FILE}.sha256"
    echo ""
    echo "🚀 部署命令:"
    echo "  # 加载镜像"
    echo "  docker load -i ${EXPORT_FILE}"
    echo ""
    echo "  # 运行容器"
    echo "  docker run -d -p 18585:18585 --name mcp-a2a-server ${FULL_IMAGE_NAME}"
    echo ""
    echo "  # 访问服务"
    echo "  curl http://localhost:18585/health"
    echo ""
    echo "📋 更多信息请查看部署文档: deployment_guide.md"
    echo "==================================="
}

# 主函数
main() {
    echo "==================================="
    echo "🐳 MCP A2A Knowledge Server"
    echo "   Docker 镜像构建开始"
    echo "==================================="
    echo ""
    
    # 执行构建流程
    check_docker
    cleanup_old_images
    build_image
    verify_image
    test_image
    export_image
    
    echo ""
    show_usage
}

# 脚本入口
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 