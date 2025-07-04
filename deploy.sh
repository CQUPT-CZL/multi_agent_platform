#!/bin/bash
set -e

# --- 自定义配置 ---
PROJECT_DIR="/home/czl/project/multi_agent_platform" # ‼️【已更新】项目绝对路径
GIT_BRANCH="main"
VENV_PATH="$PROJECT_DIR/.venv"
ECOSYSTEM_FILE="$PROJECT_DIR/ecosystem.config.js" # ‼️【已更新】配置文件的绝对路径
UV_PATH="/home/czl/.local/bin/uv"
LOG_FILE="$PROJECT_DIR/deploy.log" # ‼️【已更新】日志文件路径

# --- 主要部署逻辑函数 ---
main() {
    echo "================================================="
    echo "===== 开始部署: $(date) ====="
    echo "================================================="

    cd "$PROJECT_DIR"
    echo ">>> 正在从 Gitee 拉取分支: $GIT_BRANCH"
    git pull origin "$GIT_BRANCH"

    echo ">>> 正在激活虚拟环境..."
    source "$VENV_PATH/bin/activate"

    echo ">>> 正在使用 uv sync 同步依赖..."
    "$UV_PATH" sync

    echo ">>> 正在使用 PM2 和配置文件重启所有应用..."
    pm2 reload "$ECOSYSTEM_FILE"

    echo "===== ✅ 部署成功！ ====="
    echo ""
}

# --- 执行主函数并将所有输出追加到日志文件 ---
main 2>&1 | tee -a "$LOG_FILE"
