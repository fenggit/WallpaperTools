#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import DefaultDict, Iterable

try:
    from PIL import Image, ImageFilter, ImageStat, UnidentifiedImageError

    PIL_AVAILABLE = True
except Exception:  # pragma: no cover - runtime dependency guard
    PIL_AVAILABLE = False

    class UnidentifiedImageError(Exception):
        pass


IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tiff"}
FORMAT_TO_SUFFIX = {
    "JPEG": ".jpg",
    "PNG": ".png",
    "WEBP": ".webp",
    "GIF": ".gif",
    "TIFF": ".tiff",
}
TARGET_BRANDS = {
    "google pixel",
    "harmonyos",
    "honor",
    "huawei",
    "huawei matepad",
    "motorola",
    "oneplus",
    "oppo",
    "realme",
    "samsung",
    "transsion",
    "vivo",
    "xiaomi",
}
STOPWORDS = {
    "wallpaper",
    "wallpapers",
    "stock",
    "official",
    "default",
    "image",
    "images",
    "img",
    "background",
    "backgrounds",
    "with",
    "the",
    "edition",
    "series",
    "new",
    "for",
    "and",
    "ytechb",
    "made",
    "by",
    "arthur",
    "leak",
    "leaked",
    "beta",
    "preview",
    "dev",
}
GENERIC_DESCRIPTOR_TOKENS = {
    "variant",
    "wallpaper",
    "wallpapers",
    "stock",
    "default",
    "image",
    "images",
    "img",
}
MEANINGLESS_ONLY = {"light", "dark"}
PRESERVED_END_TOKENS = {"iphone", "ipad", "mac", "dark", "light"}


@dataclass
class RenameItem:
    src: Path
    dst: Path
    auto_described: bool
    format_fixed: bool


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


def tokenize(value: str) -> list[str]:
    base = re.findall(r"[a-z0-9]+", value.lower())
    tokens: list[str] = []
    for token in base:
        tokens.extend(re.findall(r"[a-z]+|\d+", token))
    return tokens


def move_light_dark_to_end(tokens: list[str]) -> list[str]:
    specials = [token for token in tokens if token in {"light", "dark"}]
    rest = [token for token in tokens if token not in {"light", "dark"}]
    return rest + specials


def extract_preserved_end_token(stem: str) -> str | None:
    tokens = tokenize(stem)
    if not tokens:
        return None
    last = tokens[-1]
    if last in PRESERVED_END_TOKENS:
        return last
    return None


def compress_tokens(tokens: list[str], limit: int = 6) -> list[str]:
    deduped: list[str] = []
    for token in tokens:
        if not deduped or deduped[-1] != token:
            deduped.append(token)
    return deduped[:limit]


def nearest_color_name(rgb: tuple[int, int, int]) -> str:
    palette = {
        "black": (20, 20, 20),
        "gray": (120, 120, 120),
        "silver": (185, 185, 185),
        "white": (240, 240, 240),
        "red": (200, 45, 45),
        "orange": (225, 130, 35),
        "yellow": (230, 205, 75),
        "gold": (210, 170, 70),
        "green": (70, 155, 80),
        "mint": (120, 205, 180),
        "teal": (45, 150, 150),
        "cyan": (70, 180, 220),
        "blue": (55, 100, 205),
        "purple": (135, 80, 180),
        "pink": (225, 120, 175),
        "rose": (200, 120, 135),
        "brown": (120, 80, 50),
        "beige": (220, 205, 185),
    }
    best_name = "gray"
    best_distance = float("inf")
    r, g, b = rgb
    for name, (pr, pg, pb) in palette.items():
        distance = (r - pr) ** 2 + (g - pg) ** 2 + (b - pb) ** 2
        if distance < best_distance:
            best_distance = distance
            best_name = name
    return best_name


def image_style(img) -> str:
    small = img.resize((128, 128)).convert("RGB")
    gray = small.convert("L")
    edge = gray.filter(ImageFilter.FIND_EDGES)
    edge_mean = ImageStat.Stat(edge).mean[0]
    entropy = gray.entropy()

    sat_values = []
    for r, g, b in list(small.getdata())[::16]:
        mx = max(r, g, b)
        mn = min(r, g, b)
        sat_values.append(0 if mx == 0 else (mx - mn) / mx * 255)
    sat_mean = sum(sat_values) / max(1, len(sat_values))

    if edge_mean < 12:
        return "gradient"
    if sat_mean < 18:
        return "pattern" if edge_mean > 26 else "gradient"
    if entropy > 6.2 and edge_mean > 20:
        return "photo"
    if edge_mean > 30:
        return "pattern"
    return "abstract"


def auto_descriptor(image_path: Path) -> list[str]:
    if not PIL_AVAILABLE:
        raise RuntimeError("Pillow is required for content-based descriptors")

    img = Image.open(image_path).convert("RGB")
    small = img.resize((96, 96))
    palette = small.quantize(colors=6, method=Image.Quantize.MEDIANCUT).convert("RGB")
    colors = Counter(palette.getdata()).most_common(6)

    names: list[str] = []
    for rgb, _count in colors:
        name = nearest_color_name(rgb)
        if name not in names:
            names.append(name)
        if len(names) == 2:
            break

    if not names:
        names = ["gray"]

    style = image_style(img)
    tokens = compress_tokens(names + [style], limit=4)
    return move_light_dark_to_end(tokens)


def detect_suffix_by_magic(image_path: Path) -> str | None:
    try:
        with image_path.open("rb") as f:
            header = f.read(32)
    except OSError:
        return None

    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if header.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if header.startswith(b"II*\x00") or header.startswith(b"MM\x00*"):
        return ".tiff"
    if len(header) >= 12 and header[0:4] == b"RIFF" and header[8:12] == b"WEBP":
        return ".webp"
    return None


def detect_real_suffix(image_path: Path) -> str:
    current_suffix = image_path.suffix.lower()

    def prefer_existing_suffix(real_suffix: str) -> str:
        # Keep equivalent suffix variants when already correct (e.g. .jpeg vs .jpg).
        if real_suffix == ".jpg" and current_suffix in {".jpg", ".jpeg"}:
            return current_suffix
        if real_suffix == ".tiff" and current_suffix in {".tif", ".tiff"}:
            return current_suffix
        return real_suffix

    # Prefer magic bytes first to avoid relying on filename extensions.
    magic_suffix = detect_suffix_by_magic(image_path)
    if magic_suffix:
        return prefer_existing_suffix(magic_suffix)

    if PIL_AVAILABLE:
        try:
            with Image.open(image_path) as img:
                fmt = (img.format or "").upper()
            suffix = FORMAT_TO_SUFFIX.get(fmt)
            if suffix:
                return prefer_existing_suffix(suffix)
        except (UnidentifiedImageError, OSError, ValueError):
            pass

    # Fall back to current extension when format cannot be determined.
    return current_suffix


def alt_letter(index: int) -> str:
    # 1 -> a, 2 -> b, ... 26 -> z, 27 -> aa
    chars: list[str] = []
    n = index
    while n > 0:
        n, rem = divmod(n - 1, 26)
        chars.append(chr(ord("a") + rem))
    return "".join(reversed(chars))


def extract_index_hint(stem: str) -> str | None:
    matches = re.findall(r"(?:variant|wallpaper|wallpapers|wp|promo|image|img)[-_\s]*(\d+)\b", stem.lower())
    return matches[-1] if matches else None


def fallback_descriptor_from_name(image_path: Path) -> list[str]:
    hint = extract_index_hint(image_path.stem)
    if hint:
        return ["variant", hint.zfill(2)]

    numbers = [token for token in tokenize(image_path.stem) if token.isdigit()]
    if numbers:
        return ["variant", numbers[-1].zfill(2)]
    return ["variant"]


def is_generic_descriptor(tokens: list[str]) -> bool:
    if not tokens:
        return True
    return all(
        token in MEANINGLESS_ONLY or token.isdigit() or token in GENERIC_DESCRIPTOR_TOKENS
        for token in tokens
    )


def preserve_descriptor_if_possible(stem: str, model_slug: str, model_version: str | None) -> str | None:
    stem_slug = slugify(stem)
    if not stem_slug:
        return None

    if stem_slug.startswith(model_slug + "-"):
        desc = stem_slug[len(model_slug) + 1 :]
    elif model_version and stem_slug.startswith(f"android-{model_version}-"):
        desc = stem_slug[len(f"android-{model_version}-") :]
    else:
        return None

    desc_tokens = tokenize(desc)
    if not desc_tokens or is_generic_descriptor(desc_tokens):
        return None
    return desc


def cleaned_descriptor_tokens(stem: str, context: str) -> list[str]:
    raw_tokens = tokenize(stem)
    context_tokens = set(tokenize(context))

    tokens: list[str] = []
    for token in raw_tokens:
        if token in STOPWORDS:
            continue
        if token in context_tokens:
            continue
        tokens.append(token)

    tokens = compress_tokens(move_light_dark_to_end(tokens), limit=8)
    return tokens


def build_target_name(
    image_path: Path,
    model_slug: str,
    model_version: str | None,
    context: str,
    used_names: set[str],
    collisions: defaultdict[str, int],
    content_mode: str,
    normalized_suffix: str,
) -> tuple[str, bool]:
    descriptor_tokens: list[str]
    auto_described = False

    if content_mode == "force":
        # Force mode always derives names from visual content to avoid numeric/generic names.
        descriptor_tokens = auto_descriptor(image_path)
        auto_described = True
    else:
        preserved = preserve_descriptor_if_possible(image_path.stem, model_slug, model_version)
        if preserved:
            descriptor_tokens = tokenize(preserved)
        else:
            descriptor_tokens = cleaned_descriptor_tokens(stem=image_path.stem, context=context)

        need_content = is_generic_descriptor(descriptor_tokens)

        if need_content:
            if content_mode == "off":
                descriptor_tokens = fallback_descriptor_from_name(image_path)
            else:
                try:
                    descriptor_tokens = auto_descriptor(image_path)
                    auto_described = True
                except (UnidentifiedImageError, OSError, ValueError, RuntimeError):
                    descriptor_tokens = fallback_descriptor_from_name(image_path)

    descriptor_tokens = move_light_dark_to_end(descriptor_tokens)

    preserved_end_token = extract_preserved_end_token(image_path.stem)
    if preserved_end_token:
        descriptor_tokens = [token for token in descriptor_tokens if token != preserved_end_token]
        descriptor_tokens.append(preserved_end_token)

    descriptor = slugify("-".join(descriptor_tokens))
    if not descriptor:
        descriptor = "abstract"
        auto_described = True

    suffix = normalized_suffix
    base = f"{model_slug}-{descriptor}"
    candidate = f"{base}{suffix}"
    while candidate in used_names:
        collisions[base] += 1
        candidate = f"{base}-alt-{alt_letter(collisions[base])}{suffix}"
    used_names.add(candidate)
    return candidate, auto_described


def has_images(path: Path, recursive: bool) -> bool:
    iterator: Iterable[Path]
    iterator = path.rglob("*") if recursive else path.iterdir()
    return any(p.is_file() and p.suffix.lower() in IMAGE_SUFFIXES for p in iterator)


def infer_layout(root: Path) -> str:
    children = sorted(path for path in root.iterdir() if path.is_dir())
    if not children:
        return "top-level-model"

    direct_brand_hits = sum(1 for child in children if child.name.lower() in TARGET_BRANDS)

    brand_model_score = 0
    top_model_score = 0
    for child in children:
        if has_images(child, recursive=False):
            top_model_score += 1
            continue

        subdirs = [sub for sub in child.iterdir() if sub.is_dir()]
        if any(has_images(sub, recursive=True) for sub in subdirs):
            brand_model_score += 1

    if direct_brand_hits > 0 and brand_model_score > 0:
        return "brand-model"
    if brand_model_score > top_model_score:
        return "brand-model"
    return "top-level-model"


def iter_model_dirs(root: Path, layout: str) -> list[Path]:
    if layout == "brand-model":
        model_dirs: list[Path] = []
        for brand_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            for model_dir in sorted(path for path in brand_dir.iterdir() if path.is_dir()):
                model_dirs.append(model_dir)
        return model_dirs

    model_dirs = sorted(path for path in root.iterdir() if path.is_dir())
    if model_dirs:
        return model_dirs
    return [root]


def collect_renames(root: Path, layout: str, recursive: bool, content_mode: str) -> list[RenameItem]:
    items: list[RenameItem] = []
    for model_dir in iter_model_dirs(root, layout):
        model_slug = slugify(model_dir.name)
        if not model_slug:
            continue

        version_match = re.search(r"\d+(?:\.\d+)?", model_dir.name)
        model_version = version_match.group(0).replace(".", "-") if version_match else None

        image_files = sorted(
            path
            for path in (model_dir.rglob("*") if recursive else model_dir.iterdir())
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )

        used_names_by_dir: dict[Path, set[str]] = {}
        collisions_by_dir: DefaultDict[Path, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))

        for image_path in image_files:
            parent_dir = image_path.parent
            if parent_dir not in used_names_by_dir:
                used_names_by_dir[parent_dir] = {p.name for p in parent_dir.iterdir() if p.is_file()}

            used_names = used_names_by_dir[parent_dir]
            used_names.discard(image_path.name)
            normalized_suffix = detect_real_suffix(image_path)
            format_fixed = normalized_suffix != image_path.suffix.lower()

            context = f"{model_dir.name} {parent_dir.name}"
            new_name, auto_described = build_target_name(
                image_path=image_path,
                model_slug=model_slug,
                model_version=model_version,
                context=context,
                used_names=used_names,
                collisions=collisions_by_dir[parent_dir],
                content_mode=content_mode,
                normalized_suffix=normalized_suffix,
            )
            dst = image_path.with_name(new_name)
            if dst != image_path:
                items.append(
                    RenameItem(
                        src=image_path,
                        dst=dst,
                        auto_described=auto_described,
                        format_fixed=format_fixed,
                    )
                )

    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Rename wallpaper files using brand-model-content naming.")
    parser.add_argument("--root", default="/Users/hefeng/sdcard/资源/phonewalls")
    parser.add_argument("--apply", action="store_true", help="Apply the rename instead of dry-run.")
    parser.add_argument("--sample", type=int, default=60, help="How many sample rows to print in dry-run mode.")
    parser.add_argument(
        "--layout",
        choices=["auto", "brand-model", "top-level-model"],
        default="auto",
        help="Directory layout. auto detects brand/model or top-level model folders.",
    )
    parser.add_argument(
        "--content-mode",
        choices=["prefer", "force", "off"],
        default="force",
        help="prefer: use content descriptors when name is generic; force: always use content descriptors; off: filename-only.",
    )
    parser.add_argument(
        "--recursive",
        dest="recursive",
        action="store_true",
        default=None,
        help="Scan images recursively under each model folder.",
    )
    parser.add_argument(
        "--non-recursive",
        dest="recursive",
        action="store_false",
        help="Only scan direct files under each model folder.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"root does not exist: {root}")

    layout = infer_layout(root) if args.layout == "auto" else args.layout
    recursive = (layout == "top-level-model") if args.recursive is None else args.recursive

    if args.content_mode == "force" and not PIL_AVAILABLE:
        raise SystemExit(
            "content-mode=force requires Pillow. Install with: python3 -m pip install --user pillow"
        )

    items = collect_renames(root=root, layout=layout, recursive=recursive, content_mode=args.content_mode)
    auto_count = sum(1 for item in items if item.auto_described)
    format_fixed_count = sum(1 for item in items if item.format_fixed)

    print(f"layout={layout}")
    print(f"recursive={recursive}")
    print(f"content_mode={args.content_mode}")
    print(f"pillow_available={PIL_AVAILABLE}")
    print(f"planned_renames={len(items)}")
    print(f"auto_described={auto_count}")
    print(f"format_fixed={format_fixed_count}")

    if not args.apply:
        for item in items[: args.sample]:
            flag = "auto" if item.auto_described else "name"
            print(f"[{flag}] {item.src} -> {item.dst.name}")
        return 0

    for item in items:
        if item.dst.exists() and item.dst != item.src:
            raise SystemExit(f"destination exists: {item.dst}")
    for item in items:
        item.src.rename(item.dst)
        flag = "auto" if item.auto_described else "name"
        print(f"[{flag}] {item.src} -> {item.dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
