# Dockerfile for frontend Next.js application

# 1. 一阶段镜像：安装依赖
FROM node:20-alpine AS deps

# Install pnpm
RUN npm install -g pnpm

WORKDIR /app

# Copy package.json and lockfile
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile

# 2. 二阶段镜像：构建
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set build-time environment variables if needed
# ARG NEXT_PUBLIC_API_URL
# ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Build the Next.js application
RUN npm install -g pnpm
RUN pnpm run build

# 3. 三阶段镜像：运行
FROM node:20-alpine AS runner
WORKDIR /app

RUN apk update
RUN apk upgrade
RUN apk add vim curl nginx 

ENV NODE_ENV production
# Uncomment the next line in case you need native bindings
# RUN apk add --no-cache libc6-compat

# 复制nginx的配置文件
COPY nginx.conf /etc/nginx/
COPY start.sh /app/

# Copy necessary files from the builder stage
COPY --from=builder /app/public ./public

# Automatically leverage output traces to reduce image size
# https://nextjs.org/docs/advanced-features/output-file-tracing
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# 创建启动脚本
RUN chmod +x /app/start.sh
RUN sed -i 's/\r$//' /app/start.sh

# Expose the port the app runs on
EXPOSE 3000

# Set the default command to run the application
ENTRYPOINT ["/bin/sh", "-c", "/app/start.sh"]