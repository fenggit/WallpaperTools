#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUCKET="${BUCKET:-phwalls}"
LOG_FILE="${LOG_FILE:-$ROOT_DIR/data/delete_remote_ds_store.log}"

if command -v wrangler >/dev/null 2>&1; then
  WRANGLER_BIN="wrangler"
else
  WRANGLER_BIN="npx -y wrangler"
fi

cd "$ROOT_DIR"

echo "项目目录: $ROOT_DIR"
echo "目标桶: $BUCKET"
echo "Wrangler命令: $WRANGLER_BIN"
echo "日志文件: $LOG_FILE"

echo
echo "[1/3] 登录 Cloudflare（如已登录可忽略）"
eval "$WRANGLER_BIN login"

echo
echo "[2/3] 收集本地 .DS_Store 对应的远端 key"
KEYS_FILE="$ROOT_DIR/data/.ds_store_keys.tmp"
find . -type f -name '.DS_Store' ! -path './data/*' ! -path './.git/*' | sed 's|^\./||' > "$KEYS_FILE"

key_count=$(wc -l < "$KEYS_FILE" | tr -d ' ')
echo "待删除 key 数量: $key_count"
if [[ "$key_count" == "0" ]]; then
  echo "未发现需要删除的 .DS_Store key。"
  rm -f "$KEYS_FILE"
  exit 0
fi

echo
echo "[3/3] 删除远端 .DS_Store"
: > "$LOG_FILE"

ok=0
fail=0
while IFS= read -r key; do
  [[ -z "$key" ]] && continue
  if $WRANGLER_BIN r2 object delete "$BUCKET/$key" --remote >/dev/null 2>&1; then
    echo "OK   $key" | tee -a "$LOG_FILE"
    ok=$((ok + 1))
  else
    echo "FAIL $key" | tee -a "$LOG_FILE"
    fail=$((fail + 1))
  fi
done < "$KEYS_FILE"

rm -f "$KEYS_FILE"

echo
echo "删除完成"
echo "成功数: $ok"
echo "失败数: $fail"
if [[ $fail -gt 0 ]]; then
  echo "失败列表:"
  grep '^FAIL ' "$LOG_FILE" || true
fi
