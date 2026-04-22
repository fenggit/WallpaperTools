#!/usr/bin/env bash
set -euo pipefail

CODEX_DIR="${CODEX_DIR:-$HOME/.codex}"
HEFENG_DIR="$CODEX_DIR/hefeng"
AGORA_DIR="$CODEX_DIR/agora"

print_usage() {
  cat <<'EOF'
用法:
  bash scripts/switch_codex_account.sh
  bash scripts/switch_codex_account.sh hefeng
  bash scripts/switch_codex_account.sh agora
EOF
}

choose_account() {
  echo "请选择要切换的 Codex 账号:"
  echo "1) hefeng"
  echo "2) agora"
  read -r -p "请输入选项 [1-2]: " choice

  case "$choice" in
    1) echo "hefeng" ;;
    2) echo "agora" ;;
    *) echo "无效选项: $choice" >&2; exit 1 ;;
  esac
}

resolve_source_dir() {
  local account="$1"
  case "$account" in
    hefeng) echo "$HEFENG_DIR" ;;
    agora) echo "$AGORA_DIR" ;;
    *) echo "不支持的账号: $account" >&2; exit 1 ;;
  esac
}

restart_codex() {
  echo "正在退出 Codex..."
  osascript -e 'tell application "Codex" to quit' >/dev/null 2>&1 || true
  pkill -x "Codex" >/dev/null 2>&1 || true
  sleep 2
  echo "正在重启 Codex..."
  if open -a "Codex" >/dev/null 2>&1; then
    echo "Codex 已重新启动。"
  else
    echo "⚠️ 自动重启 Codex 失败，请手动打开 Codex。"
  fi
}

main() {
  local account="${1:-}"
  local source_dir=""

  if [[ -n "$account" ]]; then
    case "$account" in
      hefeng|agora) ;;
      -h|--help)
        print_usage
        exit 0
        ;;
      *)
        echo "参数错误: $account" >&2
        print_usage
        exit 1
        ;;
    esac
  else
    account="$(choose_account)"
  fi

  source_dir="$(resolve_source_dir "$account")"

  if [[ ! -d "$source_dir" ]]; then
    echo "账号目录不存在: $source_dir" >&2
    exit 1
  fi

  if ! command -v rsync >/dev/null 2>&1; then
    echo "未找到 rsync，请先安装 rsync 后再执行。" >&2
    exit 1
  fi

  echo "正在切换到: $account"
  echo "复制来源: $source_dir"
  echo "目标目录: $CODEX_DIR"

  rsync -a "$source_dir"/ "$CODEX_DIR"/

  echo "切换完成。"
  echo "提示: 切换账号后需要完全退出 Codex 并重启一次。"
  restart_codex
}

main "$@"
