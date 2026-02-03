#!/bin/sh

# 启动nginx
nginx

# 等待nginx启动
sleep 2s

# 启动node应用
PORT=3001 HOSTNAME=0.0.0.0 nohup node server.js > /app/run.log 2>&1 &

# 等待node启动
sleep 2s

tail -f /app/run.log