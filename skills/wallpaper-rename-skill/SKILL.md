---
name: wallpaper-rename-skill
description: Use this skill when renaming wallpaper image files with consistent brand-model and description rules. Chinese trigger phrases include "壁纸重命名", "壁纸 改名", and "壁纸 文件名规范".
---

# Wallpaper Filename Rules

## Trigger Phrases (中文)

- 壁纸重命名
- 壁纸 改名
- 壁纸 文件名规范
- 壁纸 命名规则

Use this skill when the user wants wallpaper filenames normalized across device folders.

## Core rules

- Lowercase the full filename, including the extension.
- Ensure extension and real image format are consistent (for example, PNG content must end with `.png`; JPEG can be `.jpg`/`.jpeg`).
- Replace spaces, underscores, and other non-alphanumeric separators with `-`.
- Collapse repeated `-` into a single `-`.
- Remove leading and trailing `-`.
- If the description includes `light` or `dark`, place it at the end of the description.
- If the original filename ends with `iphone`, `ipad`, `mac`, `dark`, or `light`, preserve that ending token in the renamed filename.
- Use meaningful, content-based descriptors; avoid numeric-only descriptors such as `1`, `2`, `3`, or `wallpaper-01`.

## Naming pattern

The wallpaper folder name is the brand model.

Build the filename as:

`brand-model-wallpaper-description.ext`

Where:

- `brand-model` matches the normalized folder name
- `wallpaper-description` is a short description of the wallpaper's visible trait
- `.ext` uses lowercase while keeping the original format type

## Description guidance

The wallpaper description can come from online reference material or from inspecting the image content directly, but it should stay concise.

Use short, visual descriptors such as:

- `abstract-blue-gradient`
- `promo-3-dark`
- `promo-3-light`
- `branch-orbs-light`
- `mountain-purple-shadow`
- `flower-orange-closeup`

Avoid:

- generic names like `wallpaper-1`
- long sentence-like descriptions
- repeating the extension in the stem
- mixing uppercase, `_`, or extra punctuation

## Quick workflow

1. Normalize the folder name to the brand-model slug.
2. Get the wallpaper description from a trusted online source or by identifying the image content directly.
3. Keep the description short, trait-based, and content-driven.
4. If `light` or `dark` is part of the description, move it to the end.
5. For large batches, prefer the helper script in `scripts/rename-wallpapers.py`.
6. Rename the file to `brand-model-wallpaper-description.ext`.
7. Normalize extension case and correct it when it does not match the actual image format.

## Helper script

Use the bundled script for bulk renaming.

Install Pillow first (needed for content-based descriptors):

```bash
python3 -m pip install --user pillow
```

Default run (auto layout detection):

```bash
python3 scripts/rename-wallpapers.py --root /Users/hefeng/sdcard/资源/phonewalls
```

Note: default `content-mode` is `force`, so names are generated from wallpaper content.

Dry-run first:

```bash
python3 scripts/rename-wallpapers.py --root /Users/hefeng/sdcard/资源/phonewalls --sample 80
```

Apply changes:

```bash
python3 scripts/rename-wallpapers.py --root /Users/hefeng/sdcard/资源/phonewalls --apply
```

The script:

- supports both `brand/model` and `top-level model` directory layouts
- can scan recursively under each model folder
- reuses useful words from current names when possible
- auto-generates content descriptors (color + style) when names are generic (like `variant-01`)
- fixes extension/real-format mismatches (for example, PNG content incorrectly named `.jpg`)
- moves `light` and `dark` to the end of the description

Useful options:

```bash
# Force content descriptors from image analysis
python3 scripts/rename-wallpapers.py --root /Users/hefeng/sdcard/资源/phonewalls/android --layout top-level-model --recursive --content-mode force

# Disable content analysis (filename-only mode)
python3 scripts/rename-wallpapers.py --root /Users/hefeng/sdcard/资源/phonewalls --content-mode off
```

## Examples

- Folder: `google-pixel-10-pro-xl`
  File: `google-pixel-10-pro-xl-abstract-blue-gradient.jpg`

- Folder: `google-pixel-3`
  File: `google-pixel-3-promo-3-dark.png`

- Folder: `realme-gt-neo-6-se`
  File: `realme-gt-neo-6-se-cyan-orange-flow.webp`

- Folder: `nothing-phone-2`
  File: `nothing-phone-2-branch-orbs-light.jpg`

## Notes

- If the current folder name is not already normalized, normalize the folder name first and then align the filename prefix with it.
