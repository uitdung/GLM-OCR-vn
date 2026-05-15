"""
Vietnamese OCR Dataset Generator v3 — Final
=============================================

Đọc từ khó từ vietnamese_hard_words.txt (3.5K từ có dấu kép từ từ điển chính thức).
Sinh ảnh train chỉ chứa từ model hay sai. Dedup: không trùng nội dung text.

Cách dùng:
    # Clean version (cho publish)
    python generate_vietnamese_dataset_v3.py --num_samples 10000 --no_augment

    # Augmented version (cho training)
    python generate_vietnamese_dataset_v3.py --num_samples 10000 --augment_copies 3
"""

import os, json, random, argparse, io, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np

VERIFIED_FONTS = [
    "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arialbi.ttf", "C:/Windows/Fonts/ariali.ttf",
    "C:/Windows/Fonts/calibri.ttf", "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/calibrii.ttf", "C:/Windows/Fonts/calibril.ttf",
    "C:/Windows/Fonts/calibrili.ttf", "C:/Windows/Fonts/calibriz.ttf",
    "C:/Windows/Fonts/cambria.ttc", "C:/Windows/Fonts/cambriab.ttf",
    "C:/Windows/Fonts/cambriai.ttf", "C:/Windows/Fonts/cambriaz.ttf",
    "C:/Windows/Fonts/Candara.ttf", "C:/Windows/Fonts/Candarab.ttf",
    "C:/Windows/Fonts/Candarai.ttf", "C:/Windows/Fonts/Candaral.ttf",
    "C:/Windows/Fonts/Candarali.ttf", "C:/Windows/Fonts/Candaraz.ttf",
    "C:/Windows/Fonts/CascadiaCode.ttf", "C:/Windows/Fonts/CascadiaMono.ttf",
    "C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/consolab.ttf",
    "C:/Windows/Fonts/consolai.ttf", "C:/Windows/Fonts/consolaz.ttf",
    "C:/Windows/Fonts/constan.ttf", "C:/Windows/Fonts/constanb.ttf",
    "C:/Windows/Fonts/constani.ttf", "C:/Windows/Fonts/constanz.ttf",
    "C:/Windows/Fonts/corbel.ttf", "C:/Windows/Fonts/corbelb.ttf",
    "C:/Windows/Fonts/corbeli.ttf", "C:/Windows/Fonts/corbell.ttf",
    "C:/Windows/Fonts/corbelli.ttf", "C:/Windows/Fonts/corbelz.ttf",
    "C:/Windows/Fonts/cour.ttf", "C:/Windows/Fonts/courbd.ttf",
    "C:/Windows/Fonts/couri.ttf",
    "C:/Windows/Fonts/LeelaUIb.ttf", "C:/Windows/Fonts/LeelawUI.ttf",
    "C:/Windows/Fonts/micross.ttf",
    "C:/Windows/Fonts/NotoSansKR-VF.ttf", "C:/Windows/Fonts/NotoSerifKR-VF.ttf",
    "C:/Windows/Fonts/pala.ttf", "C:/Windows/Fonts/palab.ttf",
    "C:/Windows/Fonts/palabi.ttf", "C:/Windows/Fonts/palai.ttf",
    "C:/Windows/Fonts/REFSAN.TTF",
    "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/segoeuii.ttf", "C:/Windows/Fonts/segoeuil.ttf",
    "C:/Windows/Fonts/segoeuisl.ttf", "C:/Windows/Fonts/segoeuiz.ttf",
    "C:/Windows/Fonts/seguibl.ttf", "C:/Windows/Fonts/seguibli.ttf",
    "C:/Windows/Fonts/seguisb.ttf", "C:/Windows/Fonts/seguisbi.ttf",
    "C:/Windows/Fonts/seguisli.ttf", "C:/Windows/Fonts/SegUIVar.ttf",
    "C:/Windows/Fonts/SitkaVF.ttf", "C:/Windows/Fonts/SitkaVF-Italic.ttf",
    "C:/Windows/Fonts/tahoma.ttf", "C:/Windows/Fonts/tahomabd.ttf",
    "C:/Windows/Fonts/times.ttf", "C:/Windows/Fonts/timesbd.ttf",
    "C:/Windows/Fonts/timesbi.ttf", "C:/Windows/Fonts/timesi.ttf",
    "C:/Windows/Fonts/verdana.ttf", "C:/Windows/Fonts/verdanab.ttf",
    "C:/Windows/Fonts/verdanai.ttf", "C:/Windows/Fonts/verdanaz.ttf",
]


# ============================================================================
# LOAD WORDS
# ============================================================================

def load_hard_words():
    src = Path(__file__).parent / "vietnamese_hard_words.txt"
    with open(src, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]

    singles = [w for w in words if " " not in w]
    phrases = [w for w in words if " " in w]

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
        for w2 in singles[i+1:]:
            if len(w1) == len(w2) and sum(a != b for a, b in zip(w1, w2)) == 1:
                confusion.append((w1, w2))
                if len(confusion) >= 5000:
                    break
        if len(confusion) >= 5000:
            break

    return singles, phrases, groups, confusion


# ============================================================================
# RENDERING
# ============================================================================

def load_font(fp, sz):
    try:
        return ImageFont.truetype(fp, sz)
    except Exception:
        return ImageFont.load_default()

BG = [(255,255,255), (250,248,240), (245,245,245), (255,253,245), (240,248,255)]

def render(text, fp, fs=24, bg=(255,255,255), tc=(0,0,0), pad=25, ls=8):
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


# ============================================================================
# AUGMENTATION
# ============================================================================

def _perspective_coeffs(src_pts, dst_pts):
    """Compute 8 perspective transform coefficients for PIL Image.transform.
    Maps dst_pts -> src_pts."""
    matrix = []
    result = []
    for (sx, sy), (dx, dy) in zip(src_pts, dst_pts):
        matrix.append([dx, dy, 1, 0, 0, 0, -dx * sx, -dy * sx])
        result.append(sx)
        matrix.append([0, 0, 0, dx, dy, 1, -dx * sy, -dy * sy])
        result.append(sy)
    coeffs = np.linalg.solve(np.array(matrix, dtype=np.float64), np.array(result, dtype=np.float64))
    return coeffs.tolist()


def augment(img, allow_none=True):
    """Augmentation cho OCR van ban - gia lap anh chuc thuc te."""
    choices = [
        "none", "none", "none",
        "blur",
        "noise",
        "contrast_up", "contrast_down",
        "jpeg",
        "rotate",
        "shadow",
        "glare",
        "perspective",
        "downscale",
        "wave",
        "elastic",
    ]
    if not allow_none:
        choices = [c for c in choices if c != "none"]
    a = random.choice(choices)
    if a == "none":
        pass
    elif a == "blur":
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 1.0)))
    elif a == "noise":
        arr = np.array(img)
        n = np.random.randint(0, random.randint(5, 20), arr.shape, dtype=np.uint8)
        img = Image.fromarray(np.clip(arr.astype(int) + n.astype(int) - 10, 0, 255).astype(np.uint8))
    elif a == "contrast_up":
        img = ImageEnhance.Contrast(img).enhance(random.uniform(1.1, 1.4))
    elif a == "contrast_down":
        img = ImageEnhance.Contrast(img).enhance(random.uniform(0.7, 0.95))
    elif a == "jpeg":
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=random.randint(60, 85))
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
    elif a == "rotate":
        img = img.rotate(random.uniform(-2, 2), fillcolor=(255, 255, 255), expand=False)
    elif a == "shadow":
        arr = np.array(img)
        h, w = arr.shape[:2]
        for _ in range(random.randint(1, 3)):
            x1 = random.randint(0, w // 2)
            y1 = random.randint(0, h // 2)
            x2 = x1 + random.randint(w // 4, w // 2)
            y2 = y1 + random.randint(h // 4, h // 2)
            darkness = random.randint(20, 60)
            arr[y1:y2, x1:x2] = np.clip(arr[y1:y2, x1:x2].astype(int) - darkness, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
    elif a == "glare":
        arr = np.array(img)
        h, w = arr.shape[:2]
        for _ in range(random.randint(1, 2)):
            x1 = random.randint(0, w // 2)
            y1 = random.randint(0, h // 2)
            x2 = x1 + random.randint(w // 4, w // 2)
            y2 = y1 + random.randint(h // 4, h // 2)
            brightness = random.randint(30, 80)
            arr[y1:y2, x1:x2] = np.clip(arr[y1:y2, x1:x2].astype(int) + brightness, 0, 255).astype(np.uint8)
        img = Image.fromarray(arr)
    elif a == "perspective":
        w, h = img.size
        offset = min(w, h) * random.uniform(0.02, 0.06)
        src_corners = [(0, 0), (w, 0), (w, h), (0, h)]
        dst_corners = [
            (random.uniform(0, offset), random.uniform(0, offset)),
            (w - random.uniform(0, offset), random.uniform(0, offset)),
            (w - random.uniform(0, offset), h - random.uniform(0, offset)),
            (random.uniform(0, offset), h - random.uniform(0, offset)),
        ]
        coeffs = _perspective_coeffs(src_corners, dst_corners)
        img = img.transform((w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC, fillcolor=(255, 255, 255))
    elif a == "downscale":
        w, h = img.size
        scale = random.uniform(0.25, 0.6)
        small = img.resize((max(int(w * scale), 16), max(int(h * scale), 16)), Image.BILINEAR)
        img = small.resize((w, h), Image.BILINEAR)
    elif a == "wave":
        # Mô phỏng chữ trên trang sách bị cong — dịch chuyển dạng sóng sin
        w, h = img.size
        arr = np.array(img)
        result = np.full_like(arr, 255)  # nền trắng
        amplitude = random.uniform(2, 12)  # độ lệch pixel
        freq = random.uniform(0.8, 2.0)   # số vòng sóng
        for y in range(h):
            dx = int(amplitude * math.sin(2 * math.pi * freq * y / h))
            src_start = max(0, -dx)
            src_end = min(w, w - dx)
            dst_start = max(0, dx)
            length = src_end - src_start
            if length > 0:
                result[y, dst_start:dst_start + length] = arr[y, src_start:src_end]
        img = Image.fromarray(result)
    elif a == "elastic":
        # Mô phỏng giấy nhăn/bẹp — biến dạng elastic ngẫu nhiên mượt
        w, h = img.size
        arr = np.array(img)
        result = np.full_like(arr, 255)
        scale = random.uniform(4, 10)
        sigma = random.uniform(3, 6)
        # Tạo displacement field ngẫu nhiên
        dx = np.random.uniform(-scale, scale, (h, w)).astype(np.float32)
        dy = np.random.uniform(-scale, scale, (h, w)).astype(np.float32)
        # Làm mượt: map [-scale,scale] → [0,255] → blur → map lại
        def _smooth_field(field, radius, s):
            u8 = ((field + s) / (2 * s) * 255).astype(np.uint8)
            u8 = np.array(Image.fromarray(u8).filter(ImageFilter.GaussianBlur(radius=radius)))
            return (u8.astype(np.float32) / 255) * (2 * s) - s
        dx = _smooth_field(dx, sigma, scale)
        dy = _smooth_field(dy, sigma, scale)
        # Áp dụng displacement
        y_idx, x_idx = np.mgrid[0:h, 0:w]
        x_new = np.clip(x_idx + dx.astype(int), 0, w - 1)
        y_new = np.clip(y_idx + dy.astype(int), 0, h - 1)
        result[y_idx, x_idx] = arr[y_new, x_new]
        img = Image.fromarray(result)
    return img


# ============================================================================
# RANDOM CAPITALIZE
# ============================================================================

def random_capitalize(text):
    """Ngau nhien viet hoa mot so tu de gia lap van ban thuc te."""
    mode = random.choice([
        "none", "none", "none", "none",   # 40% giu nguyen
        "sentence", "sentence",             # 20% viet hoa dau cau
        "title", "title",                   # 20% title case
        "all_caps",                          # 10% toan bo 1-2 tu
        "name",                              # 10% ten rieng
    ])
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
            {"role": "assistant", "content": text}
        ],
        "images": [f"images/{fname}"],
        "_original_text": original_text
    }


def gen_word_list(singles, fonts, img_dir, idx, no_augment=False):
    n = random.randint(8, 16)
    words = random.sample(singles, min(n, len(singles)))
    random.shuffle(words)
    text = "  ".join(words)
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
    w1, w2 = random.choice(confusion)
    templates = [
        f"{w1} khác {w2}", f"{w1} và {w2}", f"phân biệt {w1} với {w2}",
        f"không phải {w1} mà là {w2}", f"từ {w1} đến {w2}",
        f"{w1} hay {w2}", f"{w2} chứ không phải {w1}",
        f"viết đúng: {w1}, sai: {w2}", f"{w1} / {w2}",
    ]
    tmpl = random.choice(templates)
    extra = random.sample(singles, random.randint(2, 5))
    text = tmpl + "  " + "  ".join(extra)
    text = unique(text)
    if not text:
        return None
    return make_result(text, idx, img_dir, fonts, no_augment)


def gen_grouped_words(groups, fonts, img_dir, idx, no_augment=False):
    keys = random.sample(list(groups.keys()), min(random.randint(2, 3), len(groups)))
    words = []
    for k in keys:
        g = groups[k]
        words += random.sample(g, min(random.randint(3, 7), len(g)))
    random.shuffle(words)
    text = "  ".join(words)
    text = unique(text)
    if not text:
        return None
    return make_result(text, idx, img_dir, fonts, no_augment)


def gen_mixed_line(singles, phrases, fonts, img_dir, idx, no_augment=False):
    phrase = random.choice(phrases)
    words = random.sample(singles, random.randint(3, 6))
    random.shuffle(words)
    text = phrase + "\n" + "  ".join(words)
    text = unique(text)
    if not text:
        return None
    return make_result(text, idx, img_dir, fonts, no_augment)


def gen_dense_sentence(phrases, singles, fonts, img_dir, idx, no_augment=False):
    sel = random.sample(phrases, random.randint(2, 3))
    random.shuffle(sel)
    extra = random.sample(singles, random.randint(2, 4))
    text = ". ".join(sel) + ". " + " ".join(extra)
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
    parser.add_argument("--num_samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--no_augment", action="store_true",
                        help="Sinh anh sach, khong augmentation (cho version clean)")
    parser.add_argument("--augment_copies", type=int, default=1,
                        help="So ban augment cho moi text (1=khong tang, 2-3=tang dataset)")
    parser.add_argument("--test_ratio", type=float, default=0.1,
                        help="Ty le test set (default: 0.1 = 10%%)")
    args = parser.parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    out = Path(args.output_dir)
    img_dir = out / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    fonts = [f for f in VERIFIED_FONTS if os.path.exists(f)]

    print("Đang tải từ điển...")
    singles, phrases, groups, confusion = load_hard_words()
    print(f"✓ {len(fonts)} font")
    print(f"  {len(singles):,} từ đơn, {len(phrases):,} cụm từ, {len(confusion):,} cặp nhầm, {len(groups)} nhóm dấu")

    generators = [
        (lambda **kw: gen_word_list(singles, **kw),               20),
        (lambda **kw: gen_phrase_list(phrases, **kw),              20),
        (lambda **kw: gen_confusion_pair(confusion, singles, **kw), 15),
        (lambda **kw: gen_grouped_words(groups, **kw),             15),
        (lambda **kw: gen_mixed_line(singles, phrases, **kw),      15),
        (lambda **kw: gen_dense_sentence(phrases, singles, **kw),  15),
    ]

    tw = sum(w for _, w in generators)
    counts = {i: int(args.num_samples * w / tw) for i, (_, w) in enumerate(generators)}
    names = ["word_list", "phrase_list", "confusion", "grouped", "mixed", "dense"]

    print(f"\nPhân bổ {args.num_samples} samples:")
    for i, nm in enumerate(names):
        print(f"  {nm:20s}: {counts[i]:5d} ({counts[i] / args.num_samples * 100:.0f}%)")

    dataset = []
    idx = 0
    skipped = 0
    total_target = args.num_samples * args.augment_copies

    for gi, (gf, _) in enumerate(generators):
        n = counts[gi]
        generated = 0
        attempts = 0
        while generated < n and attempts < n * 3:
            attempts += 1
            try:
                result = gf(fonts=fonts, img_dir=img_dir, idx=idx, no_augment=args.no_augment)
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

    # Augment copies
    base_data = []
    if args.augment_copies > 1:
        base_data = list(dataset)
        print(f"\nSinh thêm {args.augment_copies - 1} bản augment cho {len(base_data)} ảnh gốc...")
        for copy_i in range(1, args.augment_copies):
            for item in base_data:
                orig = item["_original_text"]
                text = random_capitalize(orig)
                fp = random.choice(fonts)
                fs = random.randint(18, 28)
                bg = random.choice(BG)
                img = render(text, fp, fs, bg)
                img = augment(img, allow_none=False)
                fname = f"txt_{idx:05d}.png"
                img.save(img_dir / fname)
                dataset.append({
                    "messages": [
                        {"role": "user", "content": "<image>Text Recognition:"},
                        {"role": "assistant", "content": text}
                    ],
                    "images": [f"images/{fname}"],
                    "_original_text": orig
                })
                idx += 1
                if idx % 100 == 0:
                    print(f"  {idx}/{total_target}...")

    # Strip internal fields before saving
    for item in dataset:
        item.pop("_original_text", None)

    # Shuffle and split into train/test
    random.shuffle(dataset)
    n_test = max(1, int(len(dataset) * args.test_ratio))
    test_data = dataset[:n_test]
    train_data = dataset[n_test:]

    # Save train set
    train_path = out / "vietnamese_ocr_train.json"
    with open(train_path, "w", encoding="utf-8") as f:
        json.dump(train_data, f, ensure_ascii=False, indent=2)

    # Save test set
    test_path = out / "vietnamese_ocr_test.json"
    with open(test_path, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)

    # Also save combined (backward compat)
    all_path = out / "vietnamese_ocr.json"
    with open(all_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    total_base = len(base_data) if args.augment_copies > 1 else len(dataset)
    print(f"\n✅ Done! {len(dataset)} samples (gốc: {total_base}, bỏ qua {skipped} trùng)")
    print(f"   Ảnh: {img_dir}")
    print(f"   Train: {train_path} ({len(train_data)} samples)")
    print(f"   Test:  {test_path} ({len(test_data)} samples)")
    print(f"   All:   {all_path} ({len(dataset)} samples)")


if __name__ == "__main__":
    main()
