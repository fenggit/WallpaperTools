---
name: wallpaper-sync-skill
description: Sync five wallpaper skills from ~/.codex/skills into WallpaperTools/skills, then run git add/commit/push automatically. Chinese trigger phrases include "壁纸 同步skill", "壁纸 同步 skills", and "壁纸 技能同步提交".
---

# Wallpaper Sync Skill

## Trigger Phrases (中文)

- 壁纸 同步skill
- 壁纸 同步 skills
- 壁纸 技能同步提交
- 壁纸 同步并提交

Use this skill to sync the five wallpaper-related skills from `$HOME/.codex/skills` to `WallpaperTools/skills`, then commit and push changes in one run.

## Synced skill folders

- `wallpaper_generate_brand_data_json`
- `wallpaper-caesium-compress-skill`
- `wallpaper-download-brand-skill`
- `wallpaper-rename-skill`
- `wallpaper-upload-to-cloudflare-skill`

## Quick Start

```bash
bash scripts/sync_wallpaper_skills.sh
```

## Options

```bash
bash scripts/sync_wallpaper_skills.sh \
  --repo-root "/absolute/path/to/WallpaperTools" \
  --source-root "$HOME/.codex/skills" \
  --commit-message "chore(skills): sync wallpaper skills"
```

Dry run:

```bash
bash scripts/sync_wallpaper_skills.sh --dry-run
```

Sync and commit only (skip push):

```bash
bash scripts/sync_wallpaper_skills.sh --no-push
```
