---
name: wallpaper-caesium-compress-skill
description: Batch compress wallpaper images with CaesiumCLT. Chinese trigger phrases include "壁纸压缩", "壁纸 批量压缩", and "壁纸 转webp".
---

## output language
- 中文

# Caesium Batch Compress

## Trigger Phrases (中文)

- 壁纸压缩
- 壁纸 批量压缩
- 壁纸 转webp
- 壁纸 压缩 webp

Use this skill when the user wants to batch-compress wallpapers or other image folders with `caesiumclt`.

## What this skill does

- Compress a single file or a whole directory
- Accept a custom output directory
- Convert output format to `jpeg`, `png`, `gif`, `webp`, `tiff`, or keep `original`
- Compress with `--quality` or `--lossless`
- If no compression mode is provided, default to `--quality 82`
- If both `--width` and `--height` are omitted, default to `--width 700` with proportional height
- Recurse into subfolders and preserve directory structure by default for directories
- Print output files over `100KB`; those files are automatically recompressed with `--quality 70`

## Quick workflow

1. Check whether `caesiumclt` is installed with `caesiumclt --version`.
2. If it is missing on macOS and Homebrew is available, install it with `brew install caesiumclt`.
3. Collect the user's choices:
   - input path
   - output path
   - output format
   - compression mode: `quality` or `lossless`
4. Prefer the helper script in this skill instead of hand-building the command:

```bash
bash scripts/batch-compress.sh \
  --input "/path/to/input" \
  --output "/path/to/output" \
  --format webp \
  --quality 82
```

## Defaults

- If `--output` is omitted, output goes to `<input>-compressed` for directories
- Directory input uses recursive mode and keeps folder structure
- Overwrite policy defaults to `bigger`
- Output format defaults to `webp`
- Compression mode defaults to `--quality 82` when none is provided
- Resize defaults to `--width 700` when no size is provided (`height` stays proportional)
- Files larger than `100KB` after compression are automatically recompressed using `--quality 70`

## Common examples

Compress a brand folder into WebP with quality mode:

```bash
bash scripts/batch-compress.sh \
  --input "/Users/hefeng/sdcard/资源/phonewalls/xiaomi" \
  --output "/Users/hefeng/sdcard/资源/phonewalls/xiaomi-webp" \
  --format webp \
  --quality 82
```

Compress all subfolders with default settings:

```bash
bash scripts/batch-compress.sh \
  --input "/Users/hefeng/sdcard/资源/phonewalls/samsung"
```

Use quality mode instead of size targeting:

```bash
bash scripts/batch-compress.sh \
  --input "/Users/hefeng/sdcard/资源/phonewalls/vivo" \
  --output "/Users/hefeng/sdcard/资源/phonewalls/vivo-jpeg" \
  --format jpeg \
  --quality 82
```

## Notes

- Compression mode accepts at most one option: `--quality` or `--lossless`.
- `--max-size` is disabled in this skill.
- If none is provided, the helper script automatically uses `--quality 82`.
- After the first pass, files over `100KB` are printed and then recompressed with `--quality 70`.
- The helper script can try to install `caesiumclt` automatically on macOS through Homebrew if it is missing.
- For very large folders, start with `--dry-run` to confirm paths and options.
- After compression, the helper script reports only files larger than `100KB`, plus total output size.
- If the user asks for a global Codex skill install, copy this folder into `$CODEX_HOME/skills` or use the skill installer workflow.
