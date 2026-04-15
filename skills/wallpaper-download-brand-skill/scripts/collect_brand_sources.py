#!/usr/bin/env python3
import argparse
import csv
import html
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Sequence

import requests


SITEMAP_INDEX = "https://www.ytechb.com/sitemap_index.xml"
SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/146.0.0.0 Safari/537.36"
        )
    }
)

SKIP_WORDS = (
    "book",
    "pad",
    "tablet",
    "smart tv",
    "tv",
    "laptop",
    "monitor",
    "band",
    "watch",
    "buds",
    "earbuds",
    "smartwatch",
)


def fetch_text(url: str) -> str:
    response = SESSION.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def parse_xml_locs(xml_text: str) -> List[str]:
    root = ET.fromstring(xml_text)
    return [node.text.strip() for node in root.findall(".//{*}loc") if node.text]


def sitemap_urls() -> List[str]:
    urls = parse_xml_locs(fetch_text(SITEMAP_INDEX))
    return [url for url in urls if re.search(r"/post-sitemap\d+\.xml$", url)]


def candidate_posts(brand: str) -> List[str]:
    results: List[str] = []
    pattern = re.compile(
        rf"https://www\.ytechb\.com/(?:download|download-new)-.*{re.escape(brand)}.*(?:wallpaper|wallpapers)/?$",
        re.IGNORECASE,
    )
    for sitemap in sitemap_urls():
        for loc in parse_xml_locs(fetch_text(sitemap)):
            if pattern.match(loc):
                results.append(loc.rstrip("/"))
    return sorted(set(results))


def clean_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def extract_title(page_html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", page_html, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    title = html.unescape(match.group(1))
    return clean_spaces(re.sub(r"\s*\|\s*YTECHB\s*$", "", title, flags=re.IGNORECASE))


def is_phone_wallpaper_post(title: str, url: str, brand: str) -> bool:
    low = f"{title} {url}".lower()
    if "wallpaper" not in low:
        return False
    if brand.lower() not in low:
        return False
    if any(word in low for word in SKIP_WORDS):
        return False
    return True


def normalize_model_name(title: str) -> str:
    model = title
    model = re.sub(r"^\s*download[:\s-]*", "", model, flags=re.IGNORECASE)
    model = re.sub(r"\s*\[[^\]]+\]", "", model)
    model = re.sub(
        r"\s*\((?:official|google drive|telegram|android|iphone|ios|apk link)[^)]*\)",
        "",
        model,
        flags=re.IGNORECASE,
    )
    model = re.sub(r"\s+stock wallpapers?.*$", "", model, flags=re.IGNORECASE)
    model = re.sub(r"\s+wallpapers?.*$", "", model, flags=re.IGNORECASE)
    model = clean_spaces(model)
    return model.rstrip(" -")


def source_links(page_html: str) -> List[str]:
    pattern = (
        r"https://(?:drive\.google\.com|photos\.app\.goo\.gl|photos\.google\.com|"
        r"app\.box\.com|www\.androidfilehost\.com|androidfilehost\.com|"
        r"www\.dropbox\.com|dropbox\.com|mediafire\.com)[^\s\"'<>]+"
    )
    urls = re.findall(pattern, page_html)
    cleaned = []
    for url in urls:
        url = html.unescape(url.rstrip(").,"))
        if url not in cleaned:
            cleaned.append(url)
    return cleaned


def source_status(links: Sequence[str]) -> str:
    if any("drive.google.com" in url for url in links):
        return "has_drive_link"
    if any("photos.app.goo.gl" in url or "photos.google.com" in url for url in links):
        return "has_google_photos_link"
    if links:
        return "has_other_source_link"
    return "no_source_link"


def write_sources(target_dir: Path, links: Sequence[str]) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "_source.txt").write_text("\n".join(links) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect wallpaper sources for any phone brand.")
    parser.add_argument("--brand", required=True, help="Brand keyword, for example vivo or oneplus.")
    parser.add_argument("--root", required=True, help="Brand output directory.")
    args = parser.parse_args()

    brand = clean_spaces(args.brand.lower())
    target_root = Path(args.root)
    target_root.mkdir(parents=True, exist_ok=True)
    manifest_path = target_root / "_manifest.tsv"

    rows = []
    seen_models = set()
    posts = candidate_posts(brand)
    print(f"Found {len(posts)} candidate posts for {brand}.", flush=True)

    for index, url in enumerate(posts, start=1):
        try:
            page_html = fetch_text(url)
        except Exception as exc:
            rows.append((brand, "", url, "", f"fetch_error: {exc}"))
            print(f"[{index}/{len(posts)}] fetch failed: {url} -> {exc}", flush=True)
            continue

        title = extract_title(page_html)
        if not is_phone_wallpaper_post(title, url, brand):
            continue

        model = normalize_model_name(title)
        if not model:
            continue
        model_key = model.lower()
        if model_key in seen_models:
            continue
        seen_models.add(model_key)

        links = source_links(page_html)
        folder_name = re.sub(r'[\\/:*?"<>|]+', "_", model)
        model_dir = target_root / folder_name
        write_sources(model_dir, links)

        status = source_status(links)
        rows.append((brand, model, url, links[0] if links else "", status))
        print(f"[{index}/{len(posts)}] {model} -> {status}", flush=True)
        time.sleep(0.2)

    with manifest_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["brand", "model", "article_url", "source_url", "status"])
        writer.writerows(rows)

    print(f"Manifest written to: {manifest_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
