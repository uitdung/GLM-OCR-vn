"""
Generate sources — 3 folder phẳng theo loại NỘI DUNG INPUT.
============================================================
    data/
    ├── text_single_line/   text tiếng Việt/Anh/mix, 1 dòng (7 generator nội bộ random)
    ├── text_multi_line/    đoạn văn crawl từ báo Việt (2-5 dòng)
    └── table/              ảnh bảng tiếng Việt (7 template, style randomized)

Mỗi folder chứa images/ + samples.json (KHÔNG chia train/val/test).
Mix tỉ lệ + split ở runtime bằng prepare/mix_dataset.py.

Cách dùng:
    # Gen tất cả 3 source với số lượng mặc định (1K/cái)
    python prepare/generate_sources.py

    # Gen riêng 1-2 source
    python prepare/generate_sources.py --only text_single_line table

    # Tùy chỉnh số lượng mỗi source
    python prepare/generate_sources.py --num_single 1000 --num_multi 1000 --num_table 1000

    # Ảnh sạch (no augment)
    python prepare/generate_sources.py --no_augment
"""

import argparse
import json
import random
from pathlib import Path

import numpy as np

import sys, os
sys.path.insert(0, str(Path(__file__).parent))
from generate_stage1 import (
    VERIFIED_FONTS,
    load_hard_words,
    random_capitalize,
    render,
    augment,
    BG,
    unique,
)
from generate_tables import make_table_sample

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEED = 42


# ============================================================================
# SOURCE 1: TEXT SINGLE LINE — gom 7 generator nội bộ (augment random)
# ============================================================================
def gen_text_single_line(count, fonts, img_dir, singles, phrases, groups,
                         confusion, plain_singles, no_augment, seed):
    """Sinh ảnh text 1 dòng. Augment tự ngẫu nhiên theo 7 kiểu nội bộ.

    7 generator nội bộ (random weight):
      word_list (1 từ), phrase_list, confusion (cặp từ), grouped (1 nhóm dấu),
      dense (nhiều cụm từ), plain_words (VN/EN mix)
    KHÔNG có mixed_line (vi phạm single-line do có '\n').
    Output: prompt "<image>Text Recognition:"
    """
    # Import 6 generator (đã bỏ gen_mixed_line — có '\n' vi phạm single-line)
    from generate_stage1 import (
        gen_word_list, gen_phrase_list, gen_confusion_pair, gen_grouped_words,
        gen_dense_sentence, gen_plain_words,
    )
    generators = [
        (lambda **kw: gen_word_list(singles, **kw), 10),
        (lambda **kw: gen_phrase_list(phrases, **kw), 15),
        (lambda **kw: gen_confusion_pair(confusion, singles, **kw), 20),
        (lambda **kw: gen_grouped_words(groups, **kw), 10),
        (lambda **kw: gen_dense_sentence(phrases, singles, **kw), 10),
        (lambda **kw: gen_plain_words(singles, plain_singles, **kw), 20),
    ]
    names = ["word_list", "phrase_list", "confusion", "grouped",
             "dense", "english_mix"]
    tw = sum(w for _, w in generators)
    counts = {i: int(count * w / tw) for i, (_, w) in enumerate(generators)}
    counts[len(generators) - 1] += count - sum(counts.values())

    print(f"\n  Phân bổ ({count:,}):")
    for i, nm in enumerate(names):
        print(f"    {nm:13s}: {counts[i]:5d} ({counts[i]/count*100:.0f}%)")

    samples = []
    idx = 0
    skipped = 0
    for gi, (gf, _) in enumerate(generators):
        n = counts[gi]
        gen = 0
        attempts = 0
        while gen < n and attempts < n * 3:
            attempts += 1
            try:
                r = gf(fonts=fonts, img_dir=img_dir, idx=idx,
                       no_augment=no_augment)
                if r:
                    samples.append(r)
                    idx += 1
                    gen += 1
                else:
                    skipped += 1
            except Exception:
                skipped += 1
                idx += 1
            if idx % 500 == 0 and idx > 0:
                print(f"    gen progress: {idx}/{count}...")
    print(f"  ✓ {len(samples):,} mẫu ({skipped} skip)")
    return samples


# ============================================================================
# SOURCE 2: TEXT MULTI LINE — crawl báo Việt
# ============================================================================
def gen_text_multi_line(count, fonts, img_dir, no_augment, seed,
                         force_refresh=False):
    """Sinh ảnh text nhiều dòng từ báo Việt (crawl VNExpress/Tuổi Trẻ/Thanh Niên).

    Mỗi ảnh = 1 đoạn text thật từ báo, ảnh tự xuống dòng theo chiều rộng.
    Ground-truth KHÔNG có '\\n' — giữ nguyên cấu trúc câu (liền mạch, chỉ space).
    Text GIỮ NGUYÊN dấu tiếng Việt (chuẩn) — KHÔNG strip dấu.
    Có CACHE paragraphs → lần sau không phải fetch internet lại (dùng force_refresh để cào lại).
    Output: prompt "<image>Text Recognition:"
    """
    from crawl_stage2 import crawl_news_texts
    from generate_stage1 import render_wrapped
    texts = crawl_news_texts(count, min_lines=2, max_lines=5, verbose=True,
                             force_refresh=force_refresh)
    print(f"\n  Render ảnh cho {len(texts)} đoạn báo...")
    samples = []
    idx = 0
    for text in texts:
        # Ground-truth: collapse mọi '\\n' thành space → câu liền mạch,
        # tránh phá cấu trúc câu tiếng Việt
        gt = " ".join(text.split())
        fp = random.choice(fonts)
        fs = random.randint(20, 32)
        # max_width random để ảnh có chiều rộng đa dạng
        mw = random.randint(700, 1100)
        img = render_wrapped(gt, fp, fs, (255, 255, 255), max_width=mw)
        if not no_augment:
            img = augment(img)
        fname = f"ml_{idx:05d}.png"
        img.save(img_dir / fname)
        samples.append({
            "messages": [
                {"role": "user", "content": "<image>Text Recognition:"},
                {"role": "assistant", "content": gt},
            ],
            "images": [f"images/{fname}"],
        })
        idx += 1
        if idx % 500 == 0:
            print(f"    render progress: {idx}/{len(texts)}...")
    print(f"  ✓ {len(samples):,} mẫu")
    return samples


# ============================================================================
# SOURCE 3: TABLE — 7 template style randomized
# ============================================================================
def gen_table(count, fonts, img_dir, no_augment, seed):
    """Sinh ảnh bảng. 7 template (invoice/payroll/grades/schedule/directory/menu/sales)
    random với style đen-trắng-xám (grid/zebra/header-shade bật-tắt random).

    Output: prompt "<image>Table Recognition:"
    """
    print(f"\n  Gen {count:,} ảnh bảng (7 template × style random)...")
    samples = []
    idx = 0
    skipped = 0
    while len(samples) < count:
        try:
            r = make_table_sample(idx, img_dir, fonts, no_augment)
            if r:
                r.pop("_raw", None)   # strip internal field
                samples.append(r)
                idx += 1
                if idx % 500 == 0:
                    print(f"    gen progress: {idx}/{count}...")
            else:
                skipped += 1
                idx += 1
        except Exception:
            skipped += 1
            idx += 1
        if skipped > count * 2:
            print(f"    ⚠ quá nhiều skip ({skipped}), dừng")
            break
    print(f"  ✓ {len(samples):,} mẫu ({skipped} skip)")
    return samples


# ============================================================================
# MAIN
# ============================================================================
def save_source(samples, name, base_dir):
    """Lưu samples vào base_dir/<name>/<name>.json."""
    out = base_dir / name
    (out / "images").mkdir(parents=True, exist_ok=True)
    with open(out / f"{name}.json", "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)
    return len(samples)


def main():
    parser = argparse.ArgumentParser(
        description="Gen 3 source phẳng: text_single_line, text_multi_line, table"
    )
    parser.add_argument("--only", nargs="*", default=None,
                        choices=["text_single_line", "text_multi_line", "table"],
                        help="Chỉ gen source được liệt kê (mặc định = cả 3)")
    parser.add_argument("--num_single", type=int, default=1000,
                        help="Số ảnh text_single_line (mặc định 1000)")
    parser.add_argument("--num_multi", type=int, default=1000,
                        help="Số ảnh text_multi_line (mặc định 1000)")
    parser.add_argument("--num_table", type=int, default=1000,
                        help="Số ảnh table (mặc định 1000)")
    parser.add_argument("--no_augment", action="store_true",
                        help="Sinh ảnh sạch, không augmentation")
    parser.add_argument("--refresh_news", action="store_true",
                        help="Cào lại báo (bỏ cache). Mặc định load cache nếu có.")
    parser.add_argument("--output_dir", type=str, default=str(DATA_DIR))
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    base_dir = Path(args.output_dir)
    fonts = [f for f in VERIFIED_FONTS if os.path.exists(f)]
    only = args.only or ["text_single_line", "text_multi_line", "table"]

    print("=" * 60)
    print("  GENERATE SOURCES (3 folder phẳng)")
    print("=" * 60)
    print(f"  Base dir:     {base_dir}")
    print(f"  Sources:      {only}")
    print(f"  N single/multi/table: {args.num_single}/{args.num_multi}/{args.num_table} (mặc định 1000/cái)")
    print(f"  Augment:      {'OFF' if args.no_augment else 'ON'}")
    print(f"  Fonts:        {len(fonts)}")

    # Load wordlist cho text_single_line
    singles = phrases = groups = confusion = plain_singles = None
    if "text_single_line" in only:
        print("\nĐang tải từ điển...")
        singles, phrases, groups, confusion, plain_singles = load_hard_words()
        print(f"  ✓ {len(singles):,} từ đơn, {len(phrases):,} cụm từ, "
              f"{len(confusion):,} cặp nhầm, {len(groups)} nhóm dấu")

    # ---- TEXT SINGLE LINE ----
    if "text_single_line" in only:
        print(f"\n[1/3] TEXT SINGLE LINE ({args.num_single:,} ảnh)")
        src_dir = base_dir / "text_single_line"
        img_dir = src_dir / "images"
        img_dir.mkdir(parents=True, exist_ok=True)
        random.seed(args.seed + 1)
        np.random.seed(args.seed + 1)
        samples = gen_text_single_line(
            args.num_single, fonts, img_dir,
            singles, phrases, groups, confusion, plain_singles,
            args.no_augment, args.seed + 1,
        )
        n = save_source(samples, "text_single_line", base_dir)
        print(f"  → {src_dir} ({n:,} mẫu saved)")

    # ---- TEXT MULTI LINE (crawl báo) ----
    if "text_multi_line" in only:
        print(f"\n[2/3] TEXT MULTI LINE ({args.num_multi:,} ảnh, crawl báo Việt)")
        src_dir = base_dir / "text_multi_line"
        img_dir = src_dir / "images"
        img_dir.mkdir(parents=True, exist_ok=True)
        random.seed(args.seed + 2)
        np.random.seed(args.seed + 2)
        try:
            samples = gen_text_multi_line(
                args.num_multi, fonts, img_dir,
                args.no_augment, args.seed + 2,
            )
            n = save_source(samples, "text_multi_line", base_dir)
            print(f"  → {src_dir} ({n:,} mẫu saved)")
        except Exception as e:
            print(f"  ⚠ Crawl báo lỗi (có thể do mạng): {e}")
            print(f"    Bỏ qua text_multi_line. Chạy riêng: --only text_multi_line")

    # ---- TABLE ----
    if "table" in only:
        print(f"\n[3/3] TABLE ({args.num_table:,} ảnh)")
        src_dir = base_dir / "table"
        img_dir = src_dir / "images"
        img_dir.mkdir(parents=True, exist_ok=True)
        random.seed(args.seed + 3)
        np.random.seed(args.seed + 3)
        samples = gen_table(args.num_table, fonts, img_dir,
                            args.no_augment, args.seed + 3)
        n = save_source(samples, "table", base_dir)
        print(f"  → {src_dir} ({n:,} mẫu saved)")

    print(f"\n{'=' * 60}")
    print(f"  ✅ DONE")
    print(f"  Output: {base_dir}/{{text_single_line,text_multi_line,table}}/")
    print(f"\n💡 Tiếp theo — mix theo tỉ lệ:")
    print(f"   python prepare/mix_dataset.py --info")
    print(f"   python prepare/mix_dataset.py \\")
    print(f"     --ratio text_single_line:1000 \\")
    print(f"     --ratio text_multi_line:1000 \\")
    print(f"     --ratio table:1000")


if __name__ == "__main__":
    main()
