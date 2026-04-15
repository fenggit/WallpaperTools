#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
BUCKET="${BUCKET:-phwalls}"
PARALLEL="${PARALLEL:-8}"
MAX_RETRY="${MAX_RETRY:-3}"
LOG_FILE="${LOG_FILE:-$ROOT_DIR/data/upload_selected.log}"

DEFAULT_DIRS=(
  "google pixel"
  "harmonyos"
  "honor"
  "huawei"
  "huawei matepad"
  "motorola"
  "transsion infinix"
  "transsion tecno"
  "oneplus"
  "oppo"
  "realme"
  "samsung"
  "vivo"
  "xiaomi"
)

if [[ $# -gt 0 ]]; then
  DIRS=("$@")
else
  DIRS=("${DEFAULT_DIRS[@]}")
fi

for dir in "${DIRS[@]}"; do
  if [[ ! -d "$ROOT_DIR/$dir" ]]; then
    echo "错误：目录不存在 -> $dir"
    echo "用法: bash data/upload_selected_to_phwalls.sh [目录1] [目录2] ..."
    echo "示例: bash data/upload_selected_to_phwalls.sh 'google pixel' huawei xiaomi"
    exit 1
  fi
done

if command -v wrangler >/dev/null 2>&1; then
  WRANGLER_BIN="wrangler"
else
  WRANGLER_BIN="npx -y wrangler"
fi
export WRANGLER_BIN BUCKET MAX_RETRY

cd "$ROOT_DIR"

echo "项目目录: $ROOT_DIR"
echo "目标桶: $BUCKET"
echo "并发: $PARALLEL"
echo "重试次数: $MAX_RETRY"
echo "日志文件: $LOG_FILE"
echo "Wrangler命令: $WRANGLER_BIN"
echo "目录范围: ${DIRS[*]}"

echo
echo "[1/3] 登录 Cloudflare（如已登录可忽略）"
eval "$WRANGLER_BIN login"

echo
echo "[2/3] 预览文件数量"
file_count=$(find "${DIRS[@]}" -type f ! -name '.DS_Store' | wc -l | tr -d ' ')
echo "待上传文件数: $file_count"

echo
echo "[3/3] 开始上传..."
: > "$LOG_FILE"

find "${DIRS[@]}" -type f ! -name '.DS_Store' -print0 | \
xargs -0 -n1 -P"$PARALLEL" -I{} bash -c '
  f="$1"
  key="$1"
  for i in $(seq 1 "$MAX_RETRY"); do
    if $WRANGLER_BIN r2 object put "$BUCKET/$key" --file "$f" --remote >/dev/null 2>&1; then
      echo "OK   $key"
      exit 0
    fi
    sleep $((i * 2))
  done
  echo "FAIL $key" >&2
  exit 1
' _ {} 2>&1 | tee -a "$LOG_FILE"

echo
echo "上传完成"
echo "成功数: $(grep -c '^OK   ' "$LOG_FILE" || true)"
echo "失败数: $(grep -c '^FAIL ' "$LOG_FILE" || true)"
if grep -q '^FAIL ' "$LOG_FILE"; then
  echo "失败列表:"
  grep '^FAIL ' "$LOG_FILE"
fi
