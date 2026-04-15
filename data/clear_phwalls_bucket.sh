#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUCKET="${1:-${BUCKET:-phwalls}}"

if command -v wrangler >/dev/null 2>&1; then
  WRANGLER_BIN="wrangler"
else
  WRANGLER_BIN="npx -y wrangler"
fi

cd "$ROOT_DIR"

echo "项目目录: $ROOT_DIR"
echo "目标桶: $BUCKET"
echo "Wrangler命令: $WRANGLER_BIN"
echo
echo "警告：将通过“删除并重建同名桶”实现彻底清空，这会清除桶内全部对象（包含所有前缀/目录层级）。"
echo "同时，桶级配置（如 CORS、生命周期、事件通知、自定义域名等）可能需要重新确认。"
echo

read -r -p "请输入桶名 '$BUCKET' 以确认继续: " confirm
if [[ "$confirm" != "$BUCKET" ]]; then
  echo "已取消：确认文本不匹配。"
  exit 1
fi

echo
echo "[1/3] 登录 Cloudflare（如已登录会复用会话）"
eval "$WRANGLER_BIN login"

echo
echo "[2/3] 删除桶: $BUCKET"
printf 'y\n' | eval "$WRANGLER_BIN r2 bucket delete \"$BUCKET\""

echo
echo "[3/3] 重建桶: $BUCKET"
eval "$WRANGLER_BIN r2 bucket create \"$BUCKET\""

echo
echo "完成：桶 '$BUCKET' 已清空（通过删除并重建）。"
