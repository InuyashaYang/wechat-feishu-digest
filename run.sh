#!/bin/bash
# 一键运行入口
# 用法：
#   bash run.sh              → 直接运行爬取（CLI 模式）
#   bash run.sh --ui         → 启动 Web UI（默认 http://localhost:8765）
#   bash run.sh --ui --port 9000
#   bash run.sh --days 14
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 确认 Node.js 依赖
if ! node -e "require('cheerio')" 2>/dev/null; then
    echo "[setup] 安装 cheerio..."
    cd wechat_search && npm install cheerio --silent && cd ..
fi

# 检查是否有 --ui 参数
if [[ "$1" == "--ui" ]]; then
    shift
    PORT=8765
    for arg in "$@"; do
        if [[ "$arg" == "--port" ]]; then continue; fi
        if [[ "$prev" == "--port" ]]; then PORT="$arg"; fi
        prev="$arg"
    done
    echo "  ✅ 启动 UI：http://localhost:$PORT"
    python3 ui.py --port "$PORT"
else
    python3 run.py "$@"
fi
