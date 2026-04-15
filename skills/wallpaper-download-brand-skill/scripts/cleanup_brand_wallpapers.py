#!/usr/bin/env python3
import argparse
import csv
import os
import re
import shutil
from pathlib import Path


MEDIA_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".heic",
    ".mp4",
    ".webm",
    ".mov",
    ".m4v",
}


def clean_name(name: str) -> str:
    stem, ext = os.path.splitext(name)
    stem = re.sub(r"(?i)[ _-]*ytechb(?:\.com)?\b", "", stem)
    stem = re.sub(r"(?i)\(\s*ytechb(?:\.com)?\s*\)", "", stem)
    stem = stem.replace("_", " ")
    stem = re.sub(r"\s{2,}", " ", stem).strip(" -_")
    return (stem or "file") + ext.lower()


def unique_dest(dest: Path, src: Path) -> Path:
    if not dest.exists():
        return dest
    try:
        if dest.read_bytes() == src.read_bytes():
            return dest
    except Exception:
        pass
    stem, ext = os.path.splitext(dest.name)
    i = 2
    while True:
        cand = dest.with_name(f"{stem} {i}{ext}")
        if not cand.exists():
            return cand
        i += 1


def merge_sources_from_model_files(root: Path, brand_name: str) -> int:
    source_files = sorted(root.glob("*/*_source.txt"))
    if not source_files:
        source_files = sorted(root.rglob("_source.txt"))
    out = root / f"{brand_name}_source.txt"
    with out.open("w", encoding="utf-8") as fh:
        for src in source_files:
            model = src.parent.name
            fh.write(f"[{model}]\n")
            text = src.read_text(encoding="utf-8", errors="ignore").strip()
            if text:
                fh.write(text + "\n")
            fh.write("\n")
    for src in source_files:
        src.unlink(missing_ok=True)
    return len(source_files)


def merge_sources_from_manifest(root: Path, brand_name: str) -> bool:
    manifest = root / "_manifest.tsv"
    if not manifest.exists():
        return False
    rows = list(csv.DictReader(manifest.open(encoding="utf-8"), delimiter="\t"))
    if not rows:
        return False
    out = root / f"{brand_name}_source.txt"
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            model = (row.get("model") or "").strip()
            src = (row.get("source_url") or row.get("drive_url") or "").strip()
            article = (row.get("article_url") or "").strip()
            if not model:
                continue
            fh.write(f"[{model}]\n")
            if src:
                fh.write(src + "\n")
            if article:
                fh.write("article: " + article + "\n")
            fh.write("\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Flatten model folders and merge wallpaper sources.")
    parser.add_argument("--root", required=True, help="Brand root directory.")
    parser.add_argument("--brand-name", help="Brand name for <brand>_source.txt. Defaults to root folder name.")
    args = parser.parse_args()

    root = Path(args.root)
    brand_name = args.brand_name or root.name

    moved = 0
    renamed = 0
    removed_dirs = 0

    for model_dir in sorted([p for p in root.iterdir() if p.is_dir()]):
        nested_files = [p for p in model_dir.rglob("*") if p.is_file() and p.parent != model_dir]
        for src in nested_files:
            if src.name == "_source.txt":
                continue
            dest = model_dir / clean_name(src.name)
            final = unique_dest(dest, src)
            if final.exists() and src.exists():
                try:
                    if final.read_bytes() == src.read_bytes():
                        src.unlink()
                        continue
                except Exception:
                    pass
            shutil.move(str(src), str(final))
            moved += 1
            if final.name != src.name or final.parent != src.parent:
                renamed += 1

        for f in [p for p in model_dir.iterdir() if p.is_file() and p.name != "_source.txt"]:
            cleaned = clean_name(f.name)
            dest = model_dir / cleaned
            if dest != f:
                final = unique_dest(dest, f)
                if final.exists() and final != f:
                    try:
                        if final.read_bytes() == f.read_bytes():
                            f.unlink()
                            continue
                    except Exception:
                        pass
                f.rename(final)
                renamed += 1

        for sub in sorted(
            [p for p in model_dir.rglob("*") if p.is_dir() and p != model_dir],
            key=lambda p: len(p.parts),
            reverse=True,
        ):
            try:
                sub.rmdir()
                removed_dirs += 1
            except OSError:
                pass

    source_files_merged = merge_sources_from_model_files(root, brand_name)
    if not source_files_merged:
        merge_sources_from_manifest(root, brand_name)

    print(f"moved={moved}")
    print(f"renamed={renamed}")
    print(f"removed_dirs={removed_dirs}")
    print(f"remaining_source_files={sum(1 for _ in root.rglob('_source.txt'))}")
    print(f"remaining_ytechb={sum(1 for p in root.rglob('*') if p.is_file() and 'ytechb' in p.name.lower())}")
    print(f"remaining_nested_dirs={sum(1 for p in root.rglob('*') if p.is_dir() and p.parent != root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
