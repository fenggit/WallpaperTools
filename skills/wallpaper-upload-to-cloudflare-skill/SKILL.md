---
name: wallpaper-upload-to-cloudflare-skill
description: Upload wallpaper files or folders to Cloudflare R2 with configurable source path, bucket, and remote prefix. Chinese trigger phrases include "壁纸上传", "壁纸 上传 cloudflare", and "壁纸 上传 r2".
---

## output language
- 中文

# Upload To Cloudflare

## Trigger Phrases (中文)

- 壁纸上传
- 壁纸 上传 cloudflare
- 壁纸 上传 r2
- 壁纸 上传到 r2

Use this skill to upload a local file/folder to Cloudflare R2 with a custom remote key prefix.

## Workflow

1. Ask and confirm before execution (required every time):
- ask the user to confirm current bucket and remote prefix
- ask the user to confirm the source path
- do not execute upload until the user explicitly confirms

2. Validate required inputs:
- local source path (`--source`)
- remote prefix in R2 (`--remote-prefix`)
- target bucket (`--bucket`, required)

3. Run the bundled script (pass explicit confirmation in non-interactive mode):
```bash
bash scripts/upload_to_cloudflare.sh \
  --source "/absolute/local/path" \
  --remote-prefix "android" \
  --bucket "applewalls" \
  --confirm yes
```

4. Use optional controls when needed:
- `--parallel <N>`: set upload concurrency
- `--max-retry <N>`: set retry count per file
- `--log-file <path>`: write upload logs
- `--skip-login`: skip `wrangler login`

## Notes

- Preserve relative structure under the source directory when uploading.
- Require confirmation before upload; without confirmation the script exits.
- Delete `.DS_Store` files in the source path before uploading.
- Use `wrangler` if installed; otherwise the script falls back to `npx -y wrangler`.
