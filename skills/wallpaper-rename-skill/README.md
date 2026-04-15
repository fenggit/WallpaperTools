# wallpaper-filename-rules

这个 skill 用来统一壁纸图片文件命名规则。

## 规则

1. 文件名（包含后缀）统一小写
2. 后缀名必须和真实图片格式一致（例如 PNG 内容必须是 `.png`）
3. 用 `-` 代替 `_`、空格和其他字符
4. 文件名格式：`品牌型号-壁纸描述`
5. 壁纸文件夹就是品牌型号
6. 壁纸描述优先按图片内容识别，名称要简洁且有意义
7. 如果壁纸描述里有 `light` 或 `dark`，统一放在文件名最后
8. 如果原文件名最后是 `iphone`、`ipad`、`mac`、`dark`、`light`，重命名后会保留这个结尾词
9. 避免 `1/2/3`、`wallpaper-01` 这类纯编号命名

例如：

- 不好：`Google_Pixel_10_Pro_XL.jpg`
- 最好：`google-pixel-10-pro-xl-abstract-blue-gradient.jpg`
- 明暗顺序：`nothing-phone-2-branch-orbs-light.jpg`

## 怎么触发

在 Codex 对话里直接提到 skill 名称即可：

- `$wallpaper-filename-rules`
- `使用 wallpaper-filename-rules skill 统一壁纸命名`

## 脚本

这个 skill 现在自带批量重命名脚本：

- `scripts/rename-wallpapers.py`

先安装依赖（用于图片内容描述）：

```bash
python3 -m pip install --user pillow
```

先 dry-run 预览：

```bash
python3 /Users/hefeng/.codex/skills/wallpaper-filename-rules/scripts/rename-wallpapers.py \
  --root /Users/hefeng/sdcard/资源/phonewalls \
  --sample 80
```

确认后正式执行：

```bash
python3 /Users/hefeng/.codex/skills/wallpaper-filename-rules/scripts/rename-wallpapers.py \
  --root /Users/hefeng/sdcard/资源/phonewalls \
  --apply
```

常用参数：

- `--layout auto|brand-model|top-level-model`（默认 `auto`）
- `--recursive/--non-recursive`（默认在 top-level-model 下递归）
- `--content-mode prefer|force|off`
  - 默认是 `force`（强制按壁纸内容命名）

示例（Android 版本目录在同一级时推荐）：

```bash
python3 /Users/hefeng/.codex/skills/wallpaper-filename-rules/scripts/rename-wallpapers.py \
  --root /Users/hefeng/sdcard/资源/phonewalls/android \
  --layout top-level-model \
  --recursive \
  --content-mode force \
  --sample 120
```

## 触发示例

```text
用 $wallpaper-filename-rules 把 /Users/hefeng/sdcard/资源/phonewalls/google pixel/Google Pixel 10 Pro XL 目录下的壁纸文件名统一一下，按品牌型号+壁纸描述命名，文件名连同后缀都小写。
```

```text
使用 wallpaper-filename-rules skill，检查 /Users/hefeng/sdcard/资源/phonewalls/realme 下的壁纸命名，把文件名主体改成全小写，并把空格、下划线和特殊字符都替换成连字符。
```

## 命名示例

- `google-pixel-10-pro-xl-abstract-blue-gradient.jpg`
- `google-pixel-3-branch-orbs-dark.png`
- `nothing-phone-2-branch-orbs-light.jpg`
- `realme-gt-neo-6-se-cyan-orange-flow.webp`
