#!/bin/bash
# Codespace 启动时自动启动后端和前端开发服务器

WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "========================================="
echo " 智慧购房决策工具 - 启动服务"
echo "========================================="

# 启动后端 API 服务（后台运行）
echo "[1/2] 启动后端 API 服务 (端口 8000)..."
cd "${WORKSPACE_DIR}/backend"
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
echo "      后端 PID: $!"

# 等待后端启动
sleep 2

# 启动前端开发服务（后台运行）
echo "[2/2] 启动前端开发服务 (端口 5173)..."
cd "${WORKSPACE_DIR}/frontend"
nohup npm run dev -- --host 0.0.0.0 > /tmp/frontend.log 2>&1 &
echo "      前端 PID: $!"

echo ""
echo "========================================="
echo " 服务已启动!"
echo ""
echo " 后端 API:  端口 8000 (Codespaces 自动转发)"
echo " 前端页面:  端口 5173 (Codespaces 自动转发)"
echo " 后端日志:  tail -f /tmp/backend.log"
echo " 前端日志:  tail -f /tmp/frontend.log"
echo "========================================="
