"""
Vietnamese News Crawler for Stage 2 Dataset.

Fetch articles from VNExpress, TuoiTre, ThanhNien RSS feeds.
Extract paragraphs, strip diacritics for 30%, render images.

Usage:
    python crawl_vi_news.py --num_images 5000 --output vietnamese_ocr_s2
"""

import urllib.request
import json
import re
import random
import argparse
import unicodedata
import os
import io
import xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

# Import fonts from existing generator
import sys
sys.path.insert(0, str(Path(__file__).parent))
from generate_vietnamese_dataset_v3 import VERIFIED_FONTS, render

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

RSS_FEEDS = [
    "https://vnexpress.net/rss/tin-moi-nhat.rss",
    "https://vnexpress.net/rss/the-gioi.rss",
    "https://vnexpress.net/rss/thoi-su.rss",
    "https://vnexpress.net/rss/khoa-hoc.rss",
    "https://vnexpress.net/rss/giao-duc.rss",
    "https://vnexpress.net/rss/kinh-doanh.rss",
    "https://vnexpress.net/rss/phap-luat.rss",
    "https://vnexpress.net/rss/suc-khoe.rss",
    "https://vnexpress.net/rss/doi-song.rss",
    "https://vnexpress.net/rss/so-hoa.rss",
    "https://tuoitre.vn/rss/tin-moi-nhat.rss",
    "https://tuoitre.vn/rss/the-gioi.rss",
    "https://tuoitre.vn/rss/thoi-su.rss",
    "https://tuoitre.vn/rss/kinh-doanh.rss",
    "https://thanhnien.vn/rss/home.rss",
]


def strip_vn(text):
    """Bỏ TẤT CẢ dấu tiếng Việt → chỉ còn a-z."""
    text = text.replace("đ", "d").replace("Đ", "D")
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def fetch_rss(url):
    """Lấy danh sách bài viết từ RSS feed."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=10)
        tree = ET.fromstring(resp.read())
        items = []
        for item in tree.iter("item"):
            link = None
            for child in item:
                if child.tag == "link":
                    link = child.text
                elif child.tag.endswith("}link"):
                    link = child.text
            if link:
                items.append(link)
        return items
    except Exception as e:
        print(f"  RSS error {url}: {e}")
        return []


def fetch_article(url):
    """Lấy nội dung text từ bài báo."""
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode("utf-8", errors="ignore")

        # Remove scripts, styles
        html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)

        # Extract <p> content
        paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, re.DOTALL | re.IGNORECASE)
        texts = []
        for p in paragraphs:
            # Strip HTML tags
            text = re.sub(r"<[^>]+>", "", p).strip()
            # Clean whitespace
            text = re.sub(r"\s+", " ", text)
            # Filter: phải dài, phải có chữ
            if len(text) > 50 and sum(1 for c in text if c.isalpha()) / max(len(text), 1) > 0.6:
                texts.append(text)
        return texts
    except Exception:
        return []


def chunk_paragraphs(paragraphs, min_lines=2, max_lines=10, min_words_per_line=8, max_words_per_line=25):
    """
    Gom đoạn văn thành chunks 2-10 dòng.
    Mỗi dòng 8-25 từ (để vừa ảnh).
    """
    chunks = []
    buffer = []

    for para in paragraphs:
        words = para.split()

        # Cắt đoạn dài thành nhiều dòng
        lines = []
        i = 0
        while i < len(words):
            remaining = len(words) - i
            hi = min(max_words_per_line, remaining)
            lo = min(min_words_per_line, remaining)
            chunk_len = random.randint(lo, hi)
            line = " ".join(words[i:i + chunk_len])
            lines.append(line)
            i += chunk_len

        for line in lines:
            buffer.append(line)
            if len(buffer) >= random.randint(min_lines, max_lines):
                chunks.append("\n".join(buffer))
                buffer = []

    # Flush buffer
    if len(buffer) >= min_lines:
        chunks.append("\n".join(buffer))

    return chunks


def main():
    parser = argparse.ArgumentParser(description="Vietnamese News Crawler for Stage 2")
    parser.add_argument("--num_images", type=int, default=5000, help="Số ảnh cần gen")
    parser.add_argument("--output", type=str, default="vietnamese_ocr_s2", help="Output dir")
    parser.add_argument("--strip_ratio", type=float, default=0.3, help="Tỷ lệ strip dấu")
    parser.add_argument("--num_test", type=int, default=100)
    parser.add_argument("--num_val", type=int, default=50)
    parser.add_argument("--augment_copies", type=int, default=1, help="Số bản augment (1=không)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    out = Path(args.output)
    img_dir = out / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    # Fonts
    fonts = [f for f in VERIFIED_FONTS if os.path.exists(f)]
    print(f"Fonts: {len(fonts)}")

    # ── Crawl ──
    print(f"\nCrawling {len(RSS_FEEDS)} RSS feeds...")
    all_article_urls = set()
    for rss_url in RSS_FEEDS:
        urls = fetch_rss(rss_url)
        all_article_urls.update(urls)
        print(f"  {rss_url.split('/')[2]}: {len(urls)} articles")
    print(f"Total unique URLs: {len(all_article_urls)}")

    # Fetch articles
    print(f"\nFetching articles...")
    all_paragraphs = []  # Raw paragraphs from news
    fetched = 0
    for url in list(all_article_urls):
        paras = fetch_article(url)
        all_paragraphs.extend(paras)
        fetched += 1
        if fetched % 50 == 0:
            print(f"  {fetched} articles → {len(all_paragraphs)} paragraphs")
        if len(all_paragraphs) >= args.num_images * 3:
            break

    print(f"\nCrawled: {fetched} articles, {len(all_paragraphs)} paragraphs")

    # ── Chunk thành 2-5 dòng ──
    chunks = chunk_paragraphs(all_paragraphs)
    random.shuffle(chunks)
    print(f"Chunks (2-5 lines): {len(chunks)}")

    # ── Strip dấu cho 30% ──
    texts = []
    for chunk in chunks:
        stripped = strip_vn(chunk)
        if stripped != chunk and random.random() < args.strip_ratio:
            texts.append(stripped)
        else:
            texts.append(chunk)

    # Trim to needed amount
    total_needed = args.num_images + args.num_test + args.num_val
    texts = texts[:total_needed]
    random.shuffle(texts)

    print(f"Dataset: {len(texts)} texts (strip ratio {args.strip_ratio:.0%})")

    # ── Gen ảnh ──
    print(f"\nGenerating {len(texts)} base images...")
    dataset = []
    idx = 0

    for text in texts:
        fp = random.choice(fonts)
        fs = random.randint(20, 32)
        bg = (255, 255, 255)
        img = render(text, fp, fs, bg)

        # Light augmentation (40% none)
        aug = random.choice(["none", "none", "blur", "noise", "jpeg", "rotate"])
        if aug == "blur":
            img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.8)))
        elif aug == "noise":
            arr = np.array(img)
            n = np.random.randint(0, 20, arr.shape, dtype=np.uint8)
            img = Image.fromarray(np.clip(arr.astype(int) + n.astype(int) - 10, 0, 255).astype(np.uint8))
        elif aug == "jpeg":
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=random.randint(60, 85))
            buf.seek(0)
            img = Image.open(buf).convert("RGB")
        elif aug == "rotate":
            img = img.rotate(random.uniform(-2, 2), fillcolor=(255, 255, 255))

        fname = f"txt_{idx:05d}.png"
        img.save(img_dir / fname)
        dataset.append({
            "messages": [
                {"role": "user", "content": "<image>Text Recognition:"},
                {"role": "assistant", "content": text},
            ],
            "images": [f"images/{fname}"],
        })
        idx += 1
        if idx % 500 == 0:
            print(f"  {idx}/{len(texts)}...")

    # Augment copies
    if args.augment_copies > 1:
        base = dataset[:]
        for c in range(1, args.augment_copies):
            for item in base:
                orig = item["messages"][1]["content"]
                fp = random.choice(fonts)
                fs = random.randint(20, 32)
                img = render(orig, fp, fs, (255, 255, 255))
                fname = f"txt_{idx:05d}.png"
                img.save(img_dir / fname)
                dataset.append({
                    "messages": [
                        {"role": "user", "content": "<image>Text Recognition:"},
                        {"role": "assistant", "content": orig},
                    ],
                    "images": [f"images/{fname}"],
                })
                idx += 1
            print(f"  Augment copy {c+1}/{args.augment_copies} ({idx} total)")

    # Split
    random.shuffle(dataset)
    test_data = dataset[:args.num_test]
    val_data = dataset[args.num_test:args.num_test + args.num_val]
    train_data = dataset[args.num_test + args.num_val:]

    for name, data in [
        ("vietnamese_ocr_s2.json", train_data),
        ("vietnamese_ocr_s2_val.json", val_data),
        ("vietnamese_ocr_s2_test.json", test_data),
    ]:
        with open(out / name, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)

    # Meta
    with open(out / "meta.json", "w") as f:
        json.dump({
            "num_train": len(train_data),
            "num_val": len(val_data),
            "num_test": len(test_data),
            "total": len(dataset),
            "stage": 2,
            "source": "vn_news",
            "strip_ratio": args.strip_ratio,
        }, f, indent=2)

    # Sample
    print(f"\n--- Samples ---")
    for item in random.sample(dataset, min(3, len(dataset))):
        text = item["messages"][1]["content"]
        print(f"  [{len(text)} chars] {text[:100]}...")

    print(f"\nDone: {len(train_data)} train, {len(val_data)} val, {len(test_data)} test")
    print(f"Saved to: {out}/")


if __name__ == "__main__":
    main()
