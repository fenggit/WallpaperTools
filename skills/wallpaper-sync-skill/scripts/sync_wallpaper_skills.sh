#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bash scripts/sync_wallpaper_skills.sh [options]

Options:
  --repo-root <path>       WallpaperTools repo root (default: inferred from script path)
  --source-root <path>     Skill source root (default: $HOME/.codex/skills)
  --commit-message <text>  Git commit message (default: chore(skills): sync wallpaper skills)
  --no-push                Commit only, do not push
  --dry-run                Print actions only, do not modify files
  -h, --help               Show this help
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SOURCE_ROOT="${HOME}/.codex/skills"
COMMIT_MESSAGE="chore(skills): sync wallpaper skills"
DO_PUSH=1
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-root)
      REPO_ROOT="$2"
      shift 2
      ;;
    --source-root)
      SOURCE_ROOT="$2"
      shift 2
      ;;
    --commit-message)
      COMMIT_MESSAGE="$2"
      shift 2
      ;;
    --no-push)
      DO_PUSH=0
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

SKILLS_DST="$REPO_ROOT/skills"
SYNC_SKILLS=(
  "wallpaper_generate_brand_data_json"
  "wallpaper-caesium-compress-skill"
  "wallpaper-download-brand-skill"
  "wallpaper-rename-skill"
  "wallpaper-upload-to-cloudflare-skill"
)

if [[ ! -d "$REPO_ROOT/.git" ]]; then
  echo "Not a git repository: $REPO_ROOT" >&2
  exit 1
fi

for skill in "${SYNC_SKILLS[@]}"; do
  if [[ ! -d "$SOURCE_ROOT/$skill" ]]; then
    echo "Missing source skill directory: $SOURCE_ROOT/$skill" >&2
    exit 1
  fi
done

echo "Source root : $SOURCE_ROOT"
echo "Repo root   : $REPO_ROOT"
echo "Destination : $SKILLS_DST"

if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "[DRY RUN] Would sync:"
  printf '  - %s\n' "${SYNC_SKILLS[@]}"
  exit 0
fi

mkdir -p "$SKILLS_DST"
for skill in "${SYNC_SKILLS[@]}"; do
  mkdir -p "$SKILLS_DST/$skill"
  rsync -a --delete \
    --exclude ".DS_Store" \
    --exclude "__pycache__/" \
    --exclude "*.pyc" \
    "$SOURCE_ROOT/$skill/" "$SKILLS_DST/$skill/"
done

git -C "$REPO_ROOT" add skills

if git -C "$REPO_ROOT" diff --cached --quiet; then
  echo "No staged changes after sync. Nothing to commit."
  exit 0
fi

git -C "$REPO_ROOT" commit -m "$COMMIT_MESSAGE"

if [[ "$DO_PUSH" -eq 1 ]]; then
  branch="$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)"
  if git -C "$REPO_ROOT" rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
    git -C "$REPO_ROOT" push
  else
    git -C "$REPO_ROOT" push -u origin "$branch"
  fi
fi

echo "Sync completed."
