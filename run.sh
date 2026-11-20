#!/bin/zsh
# 启动法规学习系统（构建前端 + 启动服务）
set -e
cd "$(dirname "$0")"

if [ ! -d web/dist ]; then
  echo ">>> 构建前端..."
  (cd web && npm install && npm run build)
fi

echo ">>> 启动: http://127.0.0.1:8790"
exec uv run uvicorn app.main:app --host 127.0.0.1 --port 8790
