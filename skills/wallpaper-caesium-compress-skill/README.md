# caesium-batch-compress-skill

这个 skill 用来批量压缩指定目录下的图片，支持：

- 指定输入目录或单个文件
- 指定输出目录
- 指定输出格式：`jpeg`、`png`、`gif`、`webp`、`tiff`、`original`
- 指定压缩方式：`--quality`、`--lossless`（不使用 `--max-size`）
- 未指定压缩方式时，默认使用 `--quality 82`
- 目录递归压缩并保留目录结构
- 默认输出格式为 `webp`（可用 `--format` 覆盖）
- 默认压缩模式为 `--quality 82`（当未传 `--quality/--lossless`）
- 默认尺寸为 `--width 700`（当未传 `--width/--height`，高度自动同比）
- 压缩后会打印超过 `100KB` 的文件，并自动对这些文件二次压缩为 `--quality 70`

## 怎么触发

在 Codex 对话里，直接提到 skill 名称即可，推荐用这两种方式：

- `$caesium-batch-compress`
- `使用 caesium-batch-compress skill 批量压缩图片`

只要你的需求里明确出现这个 skill 名称，Codex 就会按这个 skill 的说明来执行。

## 触发示例

```text
用 $caesium-batch-compress 把 /Users/hefeng/sdcard/资源/phonewalls/xiaomi 批量压缩到 /Users/hefeng/sdcard/资源/phonewalls/xiaomi-webp，输出 webp，默认宽度 800。
```

```text
使用 caesium-batch-compress skill，压缩 /Users/hefeng/sdcard/资源/phonewalls/vivo，输出到 /Users/hefeng/sdcard/资源/phonewalls/vivo-jpeg，格式 jpeg，质量 82。
```

```text
用 $caesium-batch-compress 递归压缩 /Users/hefeng/sdcard/资源/phonewalls/samsung，保持原格式，输出到新目录。
```

## 直接运行脚本

安装到 Codex 目录后，可以直接运行：

```bash
bash /Users/hefeng/.codex/skills/caesium-batch-compress-skill/scripts/batch-compress.sh \
  --input "/Users/hefeng/sdcard/资源/phonewalls/xiaomi" \
  --output "/Users/hefeng/sdcard/资源/phonewalls/xiaomi-webp" \
  --format webp \
  --quality 82
```

## 自动安装说明

如果机器上还没有安装 `caesiumclt`，这个 skill 的脚本会先尝试自动执行：

```bash
brew install caesiumclt
```

如果 Homebrew 不可用，脚本会停止并提示手动安装。
