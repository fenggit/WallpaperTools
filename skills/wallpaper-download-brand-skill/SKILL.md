---
name: wallpaper-download-brand-skill
description: Use this skill when the request is about downloading brand wallpapers in batch, including Chinese trigger phrases like "壁纸下载", "壁纸 批量下载", and "壁纸 抓取".
---

# Download Brand Wallpapers

## Trigger Phrases (中文)

- 壁纸下载
- 壁纸 批量下载
- 壁纸 抓取
- 下载 品牌壁纸

Use this skill when the user wants wallpapers for a phone brand such as `vivo`, `oneplus`, `realme`, `xiaomi`, or similar, and expects a repeatable workflow instead of one-off manual cleanup.

The bundled workflow does five things:

1. Collect wallpaper source links for any brand from YTECHB posts.
2. Download from original source links through browser download buttons instead of site preview thumbnails.
3. Keep one folder per model.
4. Move nested downloaded files up into the model folder root.
5. Remove `YTECHB` from filenames, merge all `_source.txt` files into `<brand>_source.txt`, then delete the per-model `_source.txt` files.

## Quick Start

Run the full workflow:

```bash
python3 scripts/download_brand_wallpapers.py \
  --brand vivo \
  --root /absolute/path/to/vivo
```

Run only the cleanup and source merge on an existing brand directory:

```bash
python3 scripts/cleanup_brand_wallpapers.py \
  --root /absolute/path/to/vivo \
  --brand-name vivo
```

Collect sources without downloading yet:

```bash
python3 scripts/collect_brand_sources.py \
  --brand vivo \
  --root /absolute/path/to/vivo
```

## Workflow

### 1. Collect Sources

Use [scripts/collect_brand_sources.py](./scripts/collect_brand_sources.py) to scan YTECHB sitemap entries for the requested brand and create:

- one model folder per detected phone model
- one `_source.txt` per model
- one `_manifest.tsv` at the brand root

The collector prefers direct download sources such as:

- `drive.google.com`
- `photos.app.goo.gl`
- `photos.google.com`
- `box.com`
- `dropbox.com`
- `androidfilehost.com`
- `mediafire.com`

It intentionally avoids ordinary article preview images so the workflow stays biased toward original-quality downloads.

### 2. Download Original Files

Use [scripts/browser_batch_download.js](./scripts/browser_batch_download.js) through the wrapper or directly with Node:

```bash
node scripts/browser_batch_download.js /absolute/path/to/vivo
```

This downloader uses real browser download events and download buttons such as `Download all` or `下载`. That matters because it keeps the workflow focused on original files and packaged wallpaper archives instead of compressed webpage thumbnails.

### 3. Normalize Output

Use [scripts/cleanup_brand_wallpapers.py](./scripts/cleanup_brand_wallpapers.py) to:

- move files out of nested subfolders and into the model root
- remove `YTECHB` from filenames
- merge per-model `_source.txt` files into `<brand>_source.txt`
- delete model-level `_source.txt`

If model-level `_source.txt` files are already gone, the cleanup script falls back to `_manifest.tsv` and reconstructs `<brand>_source.txt` from manifest data.

## Notes

- This skill is best when the user wants the same wallpaper workflow reused across multiple brands.
- The default download path assumes one brand root directory that contains one subdirectory per model.
- The browser downloader expects Google Chrome and Node to be available, plus `playwright-core`.
- The cleanup step does not delete archives by default. It focuses on folder flattening, filename cleanup, and source aggregation.

## Resources

### scripts/

- [scripts/download_brand_wallpapers.py](./scripts/download_brand_wallpapers.py): full pipeline runner
- [scripts/collect_brand_sources.py](./scripts/collect_brand_sources.py): brand-agnostic source collection
- [scripts/browser_batch_download.js](./scripts/browser_batch_download.js): browser-based original download step
- [scripts/cleanup_brand_wallpapers.py](./scripts/cleanup_brand_wallpapers.py): flatten folders, rename files, merge sources
