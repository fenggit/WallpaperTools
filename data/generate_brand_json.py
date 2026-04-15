#!/usr/bin/env python3
"""
Generate wallpaper brand JSON files from a directory tree.

Expected structure (default mode):
  <input-root>/<brand>/<model>/origin/*
  <input-root>/<brand>/<model>/compress/*

Output format:
  <brand>.json -> [{"name": <model>, "date": "YYYY/MM", "item": [...]}, ...]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

EXT_TO_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".heic": "image/heic",
    ".tiff": "image/tiff",
}

IGNORE_TOP_LEVEL = {
    ".git",
    ".venv",
    ".wrangler",
    "__pycache__",
    "data",
    "skills",
    "phwalls-time",
    "phwalls-data-json",
    "applewalls-time",
}


def format_size(num_bytes: int) -> str:
    if num_bytes >= 1024**2:
        value = num_bytes / (1024**2)
        return f"{value:.2f}".rstrip("0").rstrip(".") + " MB"
    if num_bytes >= 1024:
        value = num_bytes / 1024
        return f"{value:.2f}".rstrip("0").rstrip(".") + " KB"
    return f"{num_bytes} B"


def parse_brand_list(value: str) -> List[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def discover_brands(root: Path) -> List[str]:
    brands: List[str] = []
    for entry in sorted(root.iterdir(), key=lambda p: p.name.lower()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        if entry.name in IGNORE_TOP_LEVEL:
            continue
        brands.append(entry.name)
    return brands


def resolve_time_file(time_dir: Path, brand_name: str) -> Path | None:
    candidates = [f"{brand_name}-time.json"]

    first_word = brand_name.split(" ")[0].strip()
    if first_word and first_word != brand_name:
        candidates.append(f"{first_word}-time.json")

    if brand_name.startswith("transsion "):
        candidates.append("transsion-time.json")

    seen = set()
    for filename in candidates:
        if filename in seen:
            continue
        seen.add(filename)
        path = time_dir / filename
        if path.is_file():
            return path
    return None


def load_dates(time_dir: Path, brand_name: str) -> Dict[str, str]:
    time_file = resolve_time_file(time_dir, brand_name)
    if not time_file:
        return {}
    with time_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_dates_from_file(date_file: Path | None) -> Dict[str, str]:
    if not date_file:
        return {}
    with date_file.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_items(model_dir: Path, brand_name: str, model_name: str) -> List[dict]:
    origin_dir = model_dir / "origin"
    if not origin_dir.is_dir():
        return []

    items: List[dict] = []
    for entry in sorted(origin_dir.rglob("*"), key=lambda p: str(p).lower()):
        if not entry.is_file():
            continue
        if entry.name.startswith("."):
            continue

        ext = entry.suffix.lower()
        if ext not in EXT_TO_MIME:
            continue

        rel_path = entry.relative_to(origin_dir)
        compress_rel_path = rel_path.with_suffix(".webp")
        item = {
            "name": entry.stem,
            "type": EXT_TO_MIME[ext],
            "size": format_size(entry.stat().st_size),
            "originPath": f"{brand_name}/{model_name}/origin/{rel_path.as_posix()}",
            "compressPath": f"{brand_name}/{model_name}/compress/{compress_rel_path.as_posix()}",
        }
        items.append(item)

    return items


def sort_key_by_date(entry: dict) -> Tuple[int, int, int, str]:
    """Sort by YYYY/MM ascending (older first); invalid/missing dates last."""
    date_str = entry.get("date", "")
    try:
        year_str, month_str = date_str.split("/")
        return (0, int(year_str), int(month_str), entry.get("name", ""))
    except (ValueError, AttributeError):
        return (1, 9999, 12, entry.get("name", ""))


def generate_brand_dir(brand_dir: Path, brand_name: str, dates: Dict[str, str], out_file: Path) -> None:
    result: List[dict] = []

    for model_entry in sorted(brand_dir.iterdir(), key=lambda p: p.name.lower()):
        if not model_entry.is_dir():
            continue
        if model_entry.name.startswith("."):
            continue

        model_name = model_entry.name
        items = build_items(model_entry, brand_name, model_name)
        if not items:
            print(f"[WARN] no origin images in: {brand_name}/{model_name}")

        result.append(
            {
                "name": model_name,
                "date": dates.get(model_name, ""),
                "item": items,
            }
        )

    result.sort(key=sort_key_by_date)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[OK] {brand_name}: {len(result)} models -> {out_file}")


def generate_brand(root: Path, output_dir: Path, time_dir: Path, brand_name: str) -> None:
    brand_dir = root / brand_name
    if not brand_dir.is_dir():
        print(f"[SKIP] directory not found: {brand_dir}")
        return
    dates = load_dates(time_dir, brand_name)
    out_file = output_dir / f"{brand_name}.json"
    generate_brand_dir(brand_dir=brand_dir, brand_name=brand_name, dates=dates, out_file=out_file)


def resolve_default_output_dir(root: Path) -> Path:
    candidates = [
        root / "phwalls-data-json",
        root / "data" / "data-json",
        root.parent / "phwalls-data-json",
        root.parent / "data" / "data-json",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return root / "data-json"


def resolve_default_time_dir(root: Path) -> Path:
    candidates = [
        root / "phwalls-time",
        root / "data" / "device-time",
        root.parent / "phwalls-time",
        root.parent / "data" / "device-time",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return root / "device-time"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate brand JSON files from wallpaper folders.")
    parser.add_argument(
        "--input-path",
        "--input-dir",
        "--root",
        dest="input_path",
        help="Input path. Default mode expects brand folders under this path.",
    )
    parser.add_argument(
        "--brands",
        help="Comma-separated brand folder names. If omitted, auto-discover.",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for generated JSON files.",
    )
    parser.add_argument(
        "--output-file",
        help="Output file path for single-brand mode.",
    )
    parser.add_argument(
        "--time-dir",
        help="Directory containing *-time.json files.",
    )
    parser.add_argument(
        "--date-file",
        help="Exact date mapping JSON file for single-brand mode.",
    )
    parser.add_argument(
        "--single-brand-name",
        help="Treat --input-path as one brand directory and generate one JSON for this brand.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input_path:
        raise SystemExit("Please provide --input-path (or --input-dir / --root).")

    root = Path(args.input_path).expanduser().resolve()
    output_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else resolve_default_output_dir(root)
    )
    output_file = Path(args.output_file).expanduser().resolve() if args.output_file else None
    time_dir = (
        Path(args.time_dir).expanduser().resolve()
        if args.time_dir
        else resolve_default_time_dir(root)
    )
    date_file = Path(args.date_file).expanduser().resolve() if args.date_file else None

    if not root.is_dir():
        raise SystemExit(f"Input path not found: {root}")
    if date_file and not date_file.is_file():
        raise SystemExit(f"Date file not found: {date_file}")

    print(f"input_path={root}")
    print(f"output_dir={output_dir}")

    if args.single_brand_name:
        brand_name = args.single_brand_name.strip()
        if not brand_name:
            raise SystemExit("--single-brand-name cannot be empty.")
        dates = load_dates_from_file(date_file) if date_file else load_dates(time_dir, brand_name)
        out_file = output_file if output_file else (output_dir / f"{brand_name}.json")
        print(f"single_brand_name={brand_name}")
        if date_file:
            print(f"date_file={date_file}")
        else:
            print(f"time_dir={time_dir}")
        print(f"output_file={out_file}")
        generate_brand_dir(brand_dir=root, brand_name=brand_name, dates=dates, out_file=out_file)
    else:
        brands = parse_brand_list(args.brands) if args.brands else discover_brands(root)
        if not brands:
            raise SystemExit("No brand directories found to process.")
        print(f"time_dir={time_dir}")
        print(f"brands={brands}")
        for brand_name in brands:
            generate_brand(root=root, output_dir=output_dir, time_dir=time_dir, brand_name=brand_name)

    print("Done.")


if __name__ == "__main__":
    main()
