#!/usr/bin/env python3
import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd: Path) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=str(cwd), check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and normalize wallpapers for any phone brand.")
    parser.add_argument("--brand", required=True, help="Brand name, for example vivo, oneplus, or realme.")
    parser.add_argument("--root", required=True, help="Brand output directory.")
    parser.add_argument("--skip-collect", action="store_true", help="Skip source collection.")
    parser.add_argument("--skip-download", action="store_true", help="Skip browser download.")
    parser.add_argument("--skip-cleanup", action="store_true", help="Skip cleanup and source merge.")
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    root = Path(args.root).resolve()
    root.mkdir(parents=True, exist_ok=True)

    if not args.skip_collect:
        run(
            [
                sys.executable,
                str(script_dir / "collect_brand_sources.py"),
                "--brand",
                args.brand,
                "--root",
                str(root),
            ],
            cwd=script_dir,
        )

    if not args.skip_download:
        run(
            [
                "node",
                str(script_dir / "browser_batch_download.js"),
                str(root),
            ],
            cwd=script_dir,
        )

    if not args.skip_cleanup:
        run(
            [
                sys.executable,
                str(script_dir / "cleanup_brand_wallpapers.py"),
                "--root",
                str(root),
                "--brand-name",
                args.brand.lower(),
            ],
            cwd=script_dir,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
