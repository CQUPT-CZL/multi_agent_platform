#!/bin/bash

# 脚本出错时立即退出
set -e

# --- 自定义配置 ---
# 你的项目在服务器上的绝对路径
PROJECT_DIR="/home/czl/project/multi_agent_platform" 
# 你要拉取代码的分支
GIT_BRANCH="main"
# 你的虚拟环境文件夹路径
VENV_PATH="$PROJECT_DIR/.venv"
# PM2中后端应用的名字
BACKEND_APP_NAME="multi-agent-backend"
# PM2中前端应用的名字
FRONTEND_APP_NAME="multi-agent-frontend"
# uv命令的绝对路径 (通过 which uv 命令查找)
UV_PATH="/home/czl/.local/bin/uv"

# ‼️【新增】日志文件路径
LOG_FILE="$PROJECT_DIR/deploy.log"

# ‼️【新增】将所有输出（标准输出和错误输出）都追加到日志文件中
exec &> >(tee -a "$LOG_FILE")

# --- 部署流程 ---
echo "===== 开始部署: $(date) ====="

# 1. 进入项目目录
echo ">>> 正在进入项目目录: $PROJECT_DIR"
cd "$PROJECT_DIR"

# 2. 从 Gitee 拉取最新代码
echo ">>> 正在从 Gitee 拉取分支: $GIT_BRANCH"
git pull origin "$GIT_BRANCH"

# 3. 激活虚拟环境
echo ">>> 正在激活虚拟环境: $VENV_PATH"
source "$VENV_PATH/bin/activate"

# 4. 使用 uv sync 同步依赖包 (核心步骤！)
# 这会自动安装、更新、卸载包，使环境和 pyproject.toml 完全一致
echo ">>> 正在使用 uv sync 同步依赖..."
"$UV_PATH" sync

# 5. 重启后端和前端应用
echo ">>> 正在使用 PM2 重启应用..."
pm2 restart "$BACKEND_APP_NAME"
pm2 restart "$FRONTEND_APP_NAME"

echo "===== ✅ 部署成功！ ====="
