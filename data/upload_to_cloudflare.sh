#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUCKET="${BUCKET:-}"
PARALLEL="${PARALLEL:-8}"
MAX_RETRY="${MAX_RETRY:-3}"
LOG_FILE="${LOG_FILE:-$SCRIPT_DIR/upload_to_cloudflare.log}"
SKIP_LOGIN="${SKIP_LOGIN:-0}"
CONFIRM_EXEC=""

SOURCE_PATH=""
REMOTE_PREFIX=""

usage() {
  cat <<'USAGE'
用法:
  bash data/upload_to_cloudflare.sh --source <本地文件或目录> --remote-prefix <远端前缀>

参数:
  -s, --source         本地输入路径（文件或目录）
  -r, --remote-prefix  远端上传前缀（例如 android 或 wallpapers/android）
  -b, --bucket         R2 桶名（必填，或通过环境变量 BUCKET 提供）
  -p, --parallel       并发数（默认: 来自 PARALLEL 或 8）
  -m, --max-retry      单文件最大重试次数（默认: 来自 MAX_RETRY 或 3）
  -l, --log-file       日志文件路径（默认: data/upload_to_cloudflare.log）
      --skip-login     跳过 wrangler login
      --confirm yes    确认执行上传（非交互环境建议使用）
  -h, --help           显示帮助

示例:
  bash data/upload_to_cloudflare.sh \
    --source /Users/hefeng/sdcard/资源/phonewalls/android \
    --remote-prefix android \
    --bucket applewalls \
    --confirm yes
USAGE
}

normalize_prefix() {
  local p="$1"
  p="${p#/}"
  p="${p%/}"
  printf '%s' "$p"
}

join_key() {
  local prefix="$1"
  local rel="$2"
  if [[ -n "$prefix" ]]; then
    printf '%s/%s' "$prefix" "$rel"
  else
    printf '%s' "$rel"
  fi
}

if [[ $# -eq 0 ]]; then
  usage
  exit 1
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--source)
      SOURCE_PATH="${2:-}"
      shift 2
      ;;
    -r|--remote-prefix|--target)
      REMOTE_PREFIX="${2:-}"
      shift 2
      ;;
    -b|--bucket)
      BUCKET="${2:-}"
      shift 2
      ;;
    -p|--parallel)
      PARALLEL="${2:-}"
      shift 2
      ;;
    -m|--max-retry)
      MAX_RETRY="${2:-}"
      shift 2
      ;;
    -l|--log-file)
      LOG_FILE="${2:-}"
      shift 2
      ;;
    --skip-login)
      SKIP_LOGIN="1"
      shift
      ;;
    --confirm)
      CONFIRM_EXEC="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "错误：未知参数 -> $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$SOURCE_PATH" ]]; then
  echo "错误：必须指定 --source" >&2
  usage
  exit 1
fi

if [[ -z "$REMOTE_PREFIX" ]]; then
  echo "错误：必须指定 --remote-prefix" >&2
  usage
  exit 1
fi

if [[ -z "$BUCKET" ]]; then
  echo "错误：必须指定 --bucket（或设置环境变量 BUCKET）" >&2
  usage
  exit 1
fi

if [[ ! "$PARALLEL" =~ ^[1-9][0-9]*$ ]]; then
  echo "错误：--parallel 必须是正整数" >&2
  exit 1
fi

if [[ ! "$MAX_RETRY" =~ ^[1-9][0-9]*$ ]]; then
  echo "错误：--max-retry 必须是正整数" >&2
  exit 1
fi

if [[ ! -e "$SOURCE_PATH" ]]; then
  echo "错误：输入路径不存在 -> $SOURCE_PATH" >&2
  exit 1
fi

if [[ -d "$SOURCE_PATH" ]]; then
  SOURCE_PATH="${SOURCE_PATH%/}"
  SOURCE_IS_DIR="1"
else
  SOURCE_IS_DIR="0"
fi

REMOTE_PREFIX="$(normalize_prefix "$REMOTE_PREFIX")"

if command -v wrangler >/dev/null 2>&1; then
  WRANGLER_BIN="wrangler"
else
  WRANGLER_BIN="npx -y wrangler"
fi

export WRANGLER_BIN BUCKET MAX_RETRY SOURCE_PATH SOURCE_IS_DIR REMOTE_PREFIX

echo "输入路径: $SOURCE_PATH"
echo "输入类型: $([[ "$SOURCE_IS_DIR" == "1" ]] && echo 目录 || echo 文件)"
echo "远端前缀: $REMOTE_PREFIX"
echo "桶名: $BUCKET"
echo "并发: $PARALLEL"
echo "重试次数: $MAX_RETRY"
echo "日志文件: $LOG_FILE"
echo "Wrangler命令: $WRANGLER_BIN"

echo
echo "[确认] 本次上传目标"
echo "  桶名: $BUCKET"
echo "  远端前缀: $REMOTE_PREFIX"
echo "  本地输入: $SOURCE_PATH"
if [[ "$CONFIRM_EXEC" == "yes" ]]; then
  echo "已通过参数确认: --confirm yes"
else
  if [[ -t 0 ]]; then
    read -r -p "请确认以上桶和路径，输入 yes 继续: " input_confirm
    if [[ "$input_confirm" != "yes" ]]; then
      echo "已取消上传。"
      exit 1
    fi
  else
    echo "错误：未确认执行。请在命令中添加 --confirm yes，或在交互终端输入确认。" >&2
    exit 1
  fi
fi

echo
echo "[预处理] 清理 .DS_Store"
if [[ "$SOURCE_IS_DIR" == "1" ]]; then
  ds_count="$(find "$SOURCE_PATH" -type f -name '.DS_Store' | wc -l | tr -d ' ')"
  if [[ "$ds_count" -gt 0 ]]; then
    find "$SOURCE_PATH" -type f -name '.DS_Store' -delete
    echo "已删除 .DS_Store: $ds_count 个"
  else
    echo "未发现 .DS_Store"
  fi
else
  if [[ "$(basename "$SOURCE_PATH")" == ".DS_Store" ]]; then
    rm -f "$SOURCE_PATH"
    echo "输入文件是 .DS_Store，已删除并结束。"
    exit 0
  else
    echo "输入为单文件，跳过目录级清理"
  fi
fi

if [[ "$SKIP_LOGIN" != "1" ]]; then
  echo
  echo "[1/3] 登录 Cloudflare（如已登录可忽略）"
  eval "$WRANGLER_BIN login"
else
  echo
  echo "[1/3] 跳过登录（--skip-login）"
fi

echo
echo "[2/3] 预览将上传的文件"
if [[ "$SOURCE_IS_DIR" == "1" ]]; then
  find "$SOURCE_PATH" -type f ! -name '.DS_Store' | while IFS= read -r f; do
    rel="${f#"$SOURCE_PATH"/}"
    key="$(join_key "$REMOTE_PREFIX" "$rel")"
    echo "$f -> $key"
  done
else
  rel="$(basename "$SOURCE_PATH")"
  key="$(join_key "$REMOTE_PREFIX" "$rel")"
  echo "$SOURCE_PATH -> $key"
fi

echo
echo "[3/3] 开始上传..."
: > "$LOG_FILE"

if [[ "$SOURCE_IS_DIR" == "1" ]]; then
  find "$SOURCE_PATH" -type f ! -name '.DS_Store' -print0
else
  printf '%s\0' "$SOURCE_PATH"
fi | xargs -0 -P"$PARALLEL" -I{} bash -c '
  f="$1"
  if [[ "$SOURCE_IS_DIR" == "1" ]]; then
    rel="${f#"$SOURCE_PATH"/}"
  else
    rel="$(basename "$f")"
  fi

  if [[ -n "$REMOTE_PREFIX" ]]; then
    key="$REMOTE_PREFIX/$rel"
  else
    key="$rel"
  fi

  for i in $(seq 1 "$MAX_RETRY"); do
    if eval "$WRANGLER_BIN r2 object put \"$BUCKET/$key\" --file \"$f\" --remote" >/dev/null 2>&1; then
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
