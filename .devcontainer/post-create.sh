#!/bin/bash
set -e

# Codespaces 的工作区在 /workspaces/<repo-name>
WORKSPACE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "========================================="
echo " 智慧购房决策工具 - 环境初始化"
echo " 工作区: ${WORKSPACE_DIR}"
echo "========================================="

# 1. 安装后端依赖
echo ""
echo "[1/4] 安装后端 Python 依赖..."
cd "${WORKSPACE_DIR}/backend"
pip install --no-cache-dir -r requirements.txt

# 2. 初始化数据库和种子数据
echo ""
echo "[2/4] 初始化数据库和种子数据..."
mkdir -p data
python scripts/seed_data.py

# 3. 创建 .env 文件（如果不存在）
if [ ! -f .env ]; then
    echo ""
    echo "[3/4] 创建 .env 配置文件..."
    cp .env.example .env
    echo "提示: 请在 Codespace Secrets 中配置 AMAP_API_KEY（高德地图 API 密钥）"
    echo "      或编辑 backend/.env 文件手动填入"
else
    echo ""
    echo "[3/4] .env 配置文件已存在，跳过"
fi

# 4. 安装前端依赖
echo ""
echo "[4/4] 安装前端 Node.js 依赖..."
cd "${WORKSPACE_DIR}/frontend"
npm install

echo ""
echo "========================================="
echo " 初始化完成! 使用以下命令启动服务:"
echo ""
echo " 启动后端: cd backend && uvicorn app.main:app --host 0.0.0.0 --reload"
echo " 启动前端: cd frontend && npm run dev -- --host 0.0.0.0"
echo " 运行测试: cd backend && pytest tests/ -v"
echo ""
echo " 提示: Codespaces 会自动转发端口 8000 和 5173"
echo "========================================="
