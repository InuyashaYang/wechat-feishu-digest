#!/bin/bash
# 一键运行入口
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 确认 Node.js 依赖
if ! node -e "require('cheerio')" 2>/dev/null; then
    echo "[setup] 安装 cheerio..."
    cd wechat_search && npm install cheerio --silent && cd ..
fi

python3 run.py "$@"
