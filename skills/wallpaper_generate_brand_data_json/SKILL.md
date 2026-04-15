---
name: wallpaper_generate_brand_data_json
description: Generate wallpaper brand data JSON files from brand/model/origin folder trees with configurable input/output paths and optional date mapping. Chinese trigger phrases include "壁纸生成json数据", "壁纸 生成 json", and "壁纸 数据 json".
---

# Wallpaper Generate Brand Data JSON

## Trigger Phrases (中文)

- 壁纸生成json数据
- 壁纸 生成 json
- 壁纸 数据 json
- 生成 壁纸 json

Generate `<brand>.json` files from wallpaper folders.

## Workflow

1. Confirm folder structure:
   - Multi-brand mode: `<input>/<brand>/<model>/origin/*`
   - Single-brand mode: `<input>/<model>/origin/*` with `--single-brand-name`
2. Run the script:

```bash
python3 scripts/generate_brand_json.py --input-path "/path/to/wallpaper-root"
```

3. Optional controls:
   - `--brands "vivo,oppo"` to process selected brands only.
   - `--output-dir "/path/to/output"` to choose output directory.
   - `--time-dir "/path/to/time-json-dir"` for `*-time.json` lookup.
   - `--date-file "/path/to/date.json"` in single-brand mode.
   - `--output-file "/path/to/brand.json"` in single-brand mode.

4. Verify output format:
   - JSON array of models: `{ name, date, item[] }`
   - `item` includes: `name`, `type`, `size`, `originPath`, `compressPath`
   - models are sorted by `date` from newest to oldest (`YYYY/MM` descending), then by model name

## Script

- Script path: `scripts/generate_brand_json.py`
- Input option aliases: `--input-path`, `--input-dir`, `--root`
- If `--brands` is omitted, auto-discover top-level brand folders
- `compressPath` uses `.webp` with the same relative filename stem
