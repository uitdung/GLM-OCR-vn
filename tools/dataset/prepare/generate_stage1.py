"""
Vietnamese OCR Dataset Generator v3 — Final
=============================================

Đọc từ khó từ vietnamese_hard_words.txt (3.5K từ có dấu kép từ từ điển chính thức).
Sinh ảnh train chỉ chứa từ model hay sai. Dedup: không trùng nội dung text.

Cách dùng:
    # Clean version (cho publish)
    python generate_vietnamese_dataset_v3.py --num_train 10000 --no_augment

    # Augmented version (cho training)
    python generate_vietnamese_dataset_v3.py --num_train 10000 --augment_copies 3
"""

import argparse
import io
import json
import math
import os
import random
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

VERIFIED_FONTS = [
    # 5 họ font thực tế nhất trong tài liệu/web tiếng Việt (12 variant)
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/ariali.ttf",
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/timesbd.ttf",
    "C:/Windows/Fonts/timesi.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/calibrii.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
    "C:/Windows/Fonts/tahomabd.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
]


# ============================================================================
# LOAD WORDS
# ============================================================================


def load_hard_words():
    # data/dictionary/ — nằm ngoài prepare/, đi lên 2 cấp từ prepare/
    src = Path(__file__).resolve().parent.parent / "data" / "dictionary" / "vietnamese_words_clean.txt"
    with open(src, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

    singles = [w for w in words if " " not in w]
    phrases = [w for w in words if " " in w]

    # Từ đơn hoàn toàn không dấu (chỉ a-z) — dùng cho gen_plain_words
    plain_singles = [w for w in singles if re.match(r'^[a-z]+$', w)]

    groups = {
        "ă": [w for w in singles if any(c in w for c in "ắằẳẵặ")],
        "â": [w for w in singles if any(c in w for c in "ấầẩẫậ")],
        "ê": [w for w in singles if any(c in w for c in "ếềểễệ")],
        "ô": [w for w in singles if any(c in w for c in "ốồổỗộ")],
        "ơ": [w for w in singles if any(c in w for c in "ớờởỡợ")],
        "ư": [w for w in singles if any(c in w for c in "ứừửữự")],
        "ĩ": [w for w in singles if "ĩ" in w],
    }

    confusion = []
    for i, w1 in enumerate(singles):
        for w2 in singles[i + 1 :]:
            if len(w1) == len(w2) and sum(a != b for a, b in zip(w1, w2)) == 1:
                confusion.append((w1, w2))
                if len(confusion) >= 5000:
                    break
        if len(confusion) >= 5000:
            break

    return singles, phrases, groups, confusion, plain_singles


# ============================================================================
# ENGLISH WORDS — chống thêm dấu bừa vào text không phải tiếng Việt
# ============================================================================


ENGLISH_WORDS = [
    "hello", "world", "system", "data", "model", "code", "test", "file",
    "user", "name", "password", "email", "phone", "address", "search",
    "click", "button", "submit", "cancel", "delete", "update", "create",
    "open", "close", "save", "print", "copy", "paste", "edit", "view",
    "home", "about", "help", "settings", "account", "login", "logout",
    "register", "download", "upload", "share", "export", "import",
    "python", "java", "javascript", "html", "css", "json", "api", "url",
    "server", "client", "database", "network", "security", "error",
    "warning", "version", "install", "config", "default", "source",
    "project", "module", "function", "class", "method", "return",
    "string", "number", "array", "object", "null", "true", "false",
    "google", "facebook", "youtube", "github", "docker", "linux",
    "windows", "android", "iphone", "chrome", "firefox", "safari",
]


# ============================================================================
# RENDERING
# ============================================================================


def load_font(fp, sz):
    try:
        return ImageFont.truetype(fp, sz)
    except Exception:
        return ImageFont.load_default()


BG = [
    (255, 255, 255),
    (250, 248, 240),
    (245, 245, 245),
    (255, 253, 245),
    (240, 248, 255),
]


def render(text, fp, fs=24, bg=(255, 255, 255), tc=(0, 0, 0), pad=25, ls=8):
    font = load_font(fp, fs)
    lines = text.split("\n")
    lh = fs + ls
    mw = max((font.getbbox(l)[2] - font.getbbox(l)[0] for l in lines if l), default=100)
    img = Image.new("RGB", (max(mw + pad * 2, 120), len(lines) * lh + pad * 2), bg)
    d = ImageDraw.Draw(img)
    y = pad
    for l in lines:
        d.text((pad, y), l, fill=tc, font=font)
        y += lh
    return img


def wrap_text(text, font, max_width):
    """Tách text thành các dòng sao cho mỗi dòng không vượt max_width (pixel).

    Input text: có thể chưa có '\n' (câu liền mạch).
    Output: list[str] — các dòng đã wrap.
    """
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        candidate = (cur + " " + w).strip()
        if font.getbbox(candidate)[2] <= max_width or not cur:
            cur = candidate
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_wrapped(text, fp, fs=24, bg=(255, 255, 255), tc=(0, 0, 0),
                   pad=25, ls=8, max_width=900):
    """Render text thành ảnh, tự xuống dòng theo max_width (pixel).

    KHÔNG chèn '\n' vào text gốc — chỉ ảnh mới có xuống dòng.
    Ground-truth text giữ nguyên cấu trúc câu (liền mạch).
    """
    font = load_font(fp, fs)
    lines = wrap_text(text, font, max_width - pad * 2)
    lh = fs + ls
    img = Image.new("RGB", (max_width, len(lines) * lh + pad * 2), bg)
    d = ImageDraw.Draw(img)
    y = pad
    for l in lines:
        d.text((pad, y), l, fill=tc, font=font)
        y += lh
    return img


# ============================================================================
# AUGMENTATION
# ============================================================================





def augment(img, allow_none=True):
    """Augmentation NHẸ cho dấu tiếng Việt — dấu thanh rất nhỏ, cần chính xác tinh tế.

    Chỉ giữ 4 loại augmentation nhẹ (blur, noise, jpeg, rotate) ở cường độ thấp.
    Bỏ shadow/perspective/wave/elastic/glare/defocus — chúng làm mờ/méo dấu thanh.
    """
    choices = [
        "none", "none", "none", "none", "none",
        "none", "none", "none", "none", "none",
        "none", "none", "none",  # 65% clean — dấu TV cần chính xác tuyệt đối
        "blur", "blur",           # blur nhẹ
        "noise", "noise",         # noise thấp
        "jpeg", "jpeg",           # nén jpeg trung bình
        "rotate",                 # xoay nhẹ
    ]
    if not allow_none:
        choices = [c for c in choices if c != "none"]
    a = random.choice(choices)
    if a == "none":
        pass
    elif a == "blur":
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.6)))
    elif a == "noise":
        arr = np.array(img)
        intensity = random.randint(10, 25)  # thấp — dấu TV rất nhỏ
        n = np.random.randint(0, intensity, arr.shape, dtype=np.uint8)
        offset = intensity // 2
        img = Image.fromarray(
            np.clip(arr.astype(int) + n.astype(int) - offset, 0, 255).astype(np.uint8)
        )
    elif a == "jpeg":
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=random.randint(65, 85))
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
    elif a == "rotate":
        img = img.rotate(random.uniform(-2, 2), fillcolor=(255, 255, 255), expand=False)
    return img


# ============================================================================
# RANDOM CAPITALIZE
# ============================================================================


def random_capitalize(text):
    """Ngau nhien viet hoa mot so tu de gia lap van ban thuc te."""
    mode = random.choice(
        [
            "none",
            "none",
            "none",
            "none",  # 40% giu nguyen
            "sentence",
            "sentence",  # 20% viet hoa dau cau
            "title",
            "title",  # 20% title case
            "all_caps",  # 10% toan bo 1-2 tu
            "name",  # 10% ten rieng
        ]
    )
    if mode == "none":
        return text
    elif mode == "sentence":
        lines = text.split("\n")
        lines = [l[0].upper() + l[1:] if l else l for l in lines]
        return "\n".join(lines)
    elif mode == "title":
        return " ".join(w[0].upper() + w[1:] if w else w for w in text.split(" "))
    elif mode == "all_caps":
        words = text.split(" ")
        n = random.randint(1, min(2, len(words)))
        for i in random.sample(range(len(words)), n):
            words[i] = words[i].upper()
        return " ".join(words)
    elif mode == "name":
        words = text.split(" ")
        n = random.randint(1, min(2, len(words)))
        for i in sorted(random.sample(range(len(words)), n)):
            words[i] = words[i][0].upper() + words[i][1:] if words[i] else words[i]
        return " ".join(words)
    return text


# ============================================================================
# DEDUP
# ============================================================================

_seen = set()


def unique(text):
    if text in _seen:
        return None
    _seen.add(text)
    return text


# ============================================================================
# GENERATORS
# ============================================================================


def make_result(text, idx, img_dir, fonts, no_augment):
    """Helper: render text, augment, capitalize, save image, return sample."""
    original_text = text
    text = random_capitalize(text)
    fp = random.choice(fonts)
    fs = random.randint(18, 28)
    bg = random.choice(BG)
    img = render(text, fp, fs, bg)
    if not no_augment:
        img = augment(img)
    fname = f"txt_{idx:05d}.png"
    img.save(img_dir / fname)
    return {
        "messages": [
            {"role": "user", "content": "<image>Text Recognition:"},
            {"role": "assistant", "content": text},
        ],
        "images": [f"images/{fname}"],
        "_original_text": original_text,
    }


def gen_word_list(singles, fonts, img_dir, idx, no_augment=False):
    """Mỗi ảnh chỉ 1 từ đơn tiếng Việt — tránh LLM suy luận ngữ pháp."""
    text = random.choice(singles)
    text = unique(text)
    if not text:
        return None
    return make_result(text, idx, img_dir, fonts, no_augment)


def gen_phrase_list(phrases, fonts, img_dir, idx, no_augment=False):
    n = random.randint(2, 4)
    sel = random.sample(phrases, min(n, len(phrases)))
    random.shuffle(sel)
    text = ", ".join(sel)
    text = unique(text)
    if not text:
        return None
    return make_result(text, idx, img_dir, fonts, no_augment)


def gen_confusion_pair(confusion, singles, fonts, img_dir, idx, no_augment=False):
    """Cặp 2 từ khác nhau 1 ký tự, cách nhau bởi dấu phẩy. Ngắn gọn, không câu."""
    w1, w2 = random.choice(confusion)
    text = f"{w1}, {w2}"
    text = unique(text)
    if not text:
        return None
    return make_result(text, idx, img_dir, fonts, no_augment)


def gen_grouped_words(groups, fonts, img_dir, idx, no_augment=False):
    """6-10 từ CÙNG 1 nhóm dấu (vd: chỉ 'ă' hoặc chỉ 'ê'). Tập trung 1 loại dấu."""
    key = random.choice(list(groups.keys()))
    g = groups[key]
    words = random.sample(g, min(random.randint(6, 10), len(g)))
    random.shuffle(words)
    text = " ".join(words)
    text = unique(text)
    if not text:
        return None
    return make_result(text, idx, img_dir, fonts, no_augment)


def gen_dense_sentence(phrases, singles, fonts, img_dir, idx, no_augment=False):
    """5-8 cụm từ tiếng Việt, cách nhau bởi dấu phẩy. Nhiều cụm hơn phrase_list."""
    sel = random.sample(phrases, min(random.randint(5, 8), len(phrases)))
    random.shuffle(sel)
    text = ", ".join(sel)
    text = unique(text)
    if not text:
        return None
    return make_result(text, idx, img_dir, fonts, no_augment)


def gen_plain_words(singles, plain_singles, fonts, img_dir, idx, no_augment=False):
    """Mix từ English + VN không dấu + VN có dấu, cách nhau 1 dấu cách.

    Dạy model: KHÔNG thêm dấu vào English hoặc VN không dấu.
    Đây là generator quan trọng nhất để chống hallucination bias.
    """
    n_en = random.randint(2, 5)
    n_plain_vn = random.randint(2, 4)
    n_diac = random.randint(2, 5)
    en = random.sample(ENGLISH_WORDS, min(n_en, len(ENGLISH_WORDS)))
    plain_vn = random.sample(plain_singles, min(n_plain_vn, len(plain_singles)))
    diac = random.sample(singles, min(n_diac, len(singles)))
    words = en + plain_vn + diac
    random.shuffle(words)
    text = " ".join(words)
    text = unique(text)
    if not text:
        return None
    return make_result(text, idx, img_dir, fonts, no_augment)


def gen_paragraph(singles, phrases, plain_singles, fonts, img_dir, idx, no_augment=False):
    """Sinh đoạn văn 3-5 dòng cho Stage 2 — mô phỏng tài liệu nhiều dòng."""
    lines = []
    for _ in range(random.randint(3, 5)):
        # Mỗi dòng: mix từ có dấu + không dấu, 6-12 từ
        n_total = random.randint(6, 12)
        n_plain = random.randint(0, min(3, n_total // 2))
        n_diac = n_total - n_plain
        plain = random.sample(plain_singles, min(n_plain, len(plain_singles)))
        diac = random.sample(singles, min(n_diac, len(singles)))
        words = plain + diac
        random.shuffle(words)
        lines.append(" ".join(words))
    text = "\n".join(lines)
    text = unique(text)
    if not text:
        return None
    return make_result(text, idx, img_dir, fonts, no_augment)


# ============================================================================
# MAIN
# ============================================================================


def main():
    parser = argparse.ArgumentParser(description="Vietnamese OCR Dataset Generator v3")
    parser.add_argument("--output_dir", type=str, default="./vietnamese_ocr")
    parser.add_argument(
        "--num_train",
        type=int,
        default=20000,
        help="Số mẫu train (mặc định 20000 — giảm từ 50K, tăng chất lượng)",
    )
    parser.add_argument(
        "--num_test",
        type=int,
        default=100,
        help="Số mẫu test (mặc định 100, val cố định 100)",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--no_augment",
        action="store_true",
        help="Sinh anh sach, khong augmentation (cho version clean)",
    )
    parser.add_argument(
        "--augment_copies",
        type=int,
        default=1,
        help="So ban augment cho moi text (1=khong tang, 2-3=tang dataset)",
    )
    parser.add_argument(
        "--stage2",
        action="store_true",
        help="Stage 2: chỉ sinh đoạn văn paragraph cho document-level training",
    )
    args = parser.parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    out = Path(args.output_dir)
    img_dir = out / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    fonts = [f for f in VERIFIED_FONTS if os.path.exists(f)]

    print("Đang tải từ điển...")
    singles, phrases, groups, confusion, plain_singles = load_hard_words()
    print(f"✓ {len(fonts)} font")
    print(
        f"  {len(singles):,} từ đơn, {len(phrases):,} cụm từ, {len(confusion):,} cặp nhầm, {len(groups)} nhóm dấu, {len(plain_singles):,} từ không dấu"
    )

    if args.stage2:
        generators = [
            (lambda **kw: gen_paragraph(singles, phrases, plain_singles, **kw), 100),
        ]
    else:
        generators = [
            (lambda **kw: gen_word_list(singles, **kw), 10),
            (lambda **kw: gen_phrase_list(phrases, **kw), 15),
            (lambda **kw: gen_confusion_pair(confusion, singles, **kw), 20),  # ↑ cao nhất — fine discrimination
            (lambda **kw: gen_grouped_words(groups, **kw), 10),
            (lambda **kw: gen_mixed_line(singles, phrases, **kw), 15),
            (
                lambda **kw: gen_dense_sentence(phrases, singles, **kw),
                10,
            ),  # ↓ từ 25%
            (lambda **kw: gen_plain_words(singles, plain_singles, **kw), 20),  # ↑ từ 10% — anti-bias mạnh
        ]

    N_VAL = 100  # val cố định
    num_samples = args.num_train + args.num_test + N_VAL

    tw = sum(w for _, w in generators)
    counts = {i: int(num_samples * w / tw) for i, (_, w) in enumerate(generators)}
    names = ["paragraph"] if args.stage2 else ["word_list", "phrase_list", "confusion", "grouped", "mixed", "dense", "plain_words"]

    print(
        f"\nPhân bổ {num_samples} samples (train {args.num_train} + val {N_VAL} + test {args.num_test}):"
    )
    for i, nm in enumerate(names):
        print(f"  {nm:20s}: {counts[i]:5d} ({counts[i] / num_samples * 100:.0f}%)")

    dataset = []
    idx = 0
    skipped = 0
    total_target = num_samples * args.augment_copies

    for gi, (gf, _) in enumerate(generators):
        n = counts[gi]
        generated = 0
        attempts = 0
        while generated < n and attempts < n * 3:
            attempts += 1
            try:
                result = gf(
                    fonts=fonts, img_dir=img_dir, idx=idx, no_augment=args.no_augment
                )
                if result:
                    dataset.append(result)
                    idx += 1
                    generated += 1
                else:
                    skipped += 1
            except Exception:
                skipped += 1
            if idx % 100 == 0 and idx > 0:
                print(f"  {idx}/{total_target}... (bỏ qua {skipped} trùng)")

    # Augment copies — chỉ augment train, không augment val/test
    base_data = []
    if args.augment_copies > 1:
        n_keep = args.num_test + N_VAL  # 300 mẫu cuối giữ nguyên (val+test)
        train_data = dataset[:-n_keep] if n_keep < len(dataset) else []
        base_data = train_data
        n_aug_total = len(train_data) * (args.augment_copies - 1)
        print(
            f"\nSinh thêm {args.augment_copies - 1} bản augment cho {len(train_data)} ảnh train (val/test giữ nguyên)..."
        )
        for copy_i in range(1, args.augment_copies):
            for item in train_data:
                orig = item["_original_text"]
                text = random_capitalize(orig)
                fp = random.choice(fonts)
                fs = random.randint(18, 28)
                bg = random.choice(BG)
                img = render(text, fp, fs, bg)
                img = augment(img, allow_none=False)
                fname = f"txt_{idx:05d}.png"
                img.save(img_dir / fname)
                dataset.append(
                    {
                        "messages": [
                            {"role": "user", "content": "<image>Text Recognition:"},
                            {"role": "assistant", "content": text},
                        ],
                        "images": [f"images/{fname}"],
                        "_original_text": orig,
                    }
                )
                idx += 1
                if idx % 100 == 0:
                    print(f"  {idx}/{total_target}...")

    # Strip internal fields before saving
    for item in dataset:
        item.pop("_original_text", None)

    # Save combined dataset
    out_path = out / "vietnamese_ocr.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    # Save meta (notebook đọc để biết cách split)
    meta_path = out / "meta.json"
    meta = {
        "num_train": args.num_train,
        "num_val": N_VAL,
        "num_test": args.num_test,
        "total": len(dataset),
        "augment_copies": args.augment_copies,
        "seed": args.seed,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    total_base = len(base_data) if args.augment_copies > 1 else len(dataset)
    print(
        f"\n✅ Done! {len(dataset)} samples (gốc: {total_base}, bỏ qua {skipped} trùng)"
    )
    print(f"   Ảnh: {img_dir}")
    print(f"   Data: {out_path} ({len(dataset)} samples)")
    print(f"   Meta: {meta_path}")


if __name__ == "__main__":
    main()
