# download-brand-wallpapers

这个 skill 用来批量下载某个手机品牌的原厂壁纸，并自动做后处理，适合像 `vivo`、`oneplus`、`realme`、`xiaomi` 这类品牌目录化整理。

它会帮助你完成：

- 收集品牌相关机型的壁纸来源
- 优先下载原始文件，而不是网页缩略图
- 按机型分目录保存
- 拉平嵌套目录
- 清理文件名中的 `YTECHB`
- 合并每个机型目录里的 `_source.txt` 为品牌级 `brand_source.txt`

## 怎么触发

在 Codex 对话里，直接写出 skill 名称即可，推荐：

- `$download-brand-wallpapers`
- `使用 download-brand-wallpapers skill 下载品牌壁纸`

只要请求里明确提到这个 skill，Codex 就会按这个技能包里的流程来处理。

## 触发示例

```text
用 $download-brand-wallpapers 下载 vivo 的原厂壁纸，到 /Users/hefeng/sdcard/资源/phonewalls/vivo。
```

```text
使用 download-brand-wallpapers skill，帮我抓取 oneplus 的 stock wallpapers，并整理到 /Users/hefeng/sdcard/资源/phonewalls/oneplus。
```

```text
用 $download-brand-wallpapers 只收集 realme 的壁纸来源，先不要下载文件，输出到 /Users/hefeng/sdcard/资源/phonewalls/realme。
```

## 直接运行脚本

完整流程：

```bash
python3 /Users/hefeng/.codex/skills/download-brand-wallpapers/scripts/download_brand_wallpapers.py \
  --brand vivo \
  --root /Users/hefeng/sdcard/资源/phonewalls/vivo
```

只做清理：

```bash
python3 /Users/hefeng/.codex/skills/download-brand-wallpapers/scripts/cleanup_brand_wallpapers.py \
  --root /Users/hefeng/sdcard/资源/phonewalls/vivo \
  --brand-name vivo
```

只收集来源：

```bash
python3 /Users/hefeng/.codex/skills/download-brand-wallpapers/scripts/collect_brand_sources.py \
  --brand vivo \
  --root /Users/hefeng/sdcard/资源/phonewalls/vivo
```

## 依赖提醒

这个 skill 的浏览器下载步骤通常依赖：

- `python3`
- `node`
- `Google Chrome`
- `playwright-core`

如果只做来源收集或清理，不一定需要全部依赖。
