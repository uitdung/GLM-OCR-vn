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
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arialbi.ttf",
    "C:/Windows/Fonts/ariali.ttf",
    "C:/Windows/Fonts/calibri.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
    "C:/Windows/Fonts/calibrii.ttf",
    "C:/Windows/Fonts/calibril.ttf",
    "C:/Windows/Fonts/calibrili.ttf",
    "C:/Windows/Fonts/calibriz.ttf",
    "C:/Windows/Fonts/cambria.ttc",
    "C:/Windows/Fonts/cambriab.ttf",
    "C:/Windows/Fonts/cambriai.ttf",
    "C:/Windows/Fonts/cambriaz.ttf",
    "C:/Windows/Fonts/Candara.ttf",
    "C:/Windows/Fonts/Candarab.ttf",
    "C:/Windows/Fonts/Candarai.ttf",
    "C:/Windows/Fonts/Candaraz.ttf",
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/consolab.ttf",
    "C:/Windows/Fonts/consolai.ttf",
    "C:/Windows/Fonts/consolaz.ttf",
    "C:/Windows/Fonts/constan.ttf",
    "C:/Windows/Fonts/constanb.ttf",
    "C:/Windows/Fonts/constani.ttf",
    "C:/Windows/Fonts/constanz.ttf",
    "C:/Windows/Fonts/cour.ttf",
    "C:/Windows/Fonts/courbd.ttf",
    "C:/Windows/Fonts/couri.ttf",
    "C:/Windows/Fonts/pala.ttf",
    "C:/Windows/Fonts/palab.ttf",
    "C:/Windows/Fonts/palabi.ttf",
    "C:/Windows/Fonts/palai.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/segoeuii.ttf",
    "C:/Windows/Fonts/segoeuil.ttf",
    "C:/Windows/Fonts/segoeuisl.ttf",
    "C:/Windows/Fonts/segoeuiz.ttf",
    "C:/Windows/Fonts/seguibl.ttf",
    "C:/Windows/Fonts/seguibli.ttf",
    "C:/Windows/Fonts/seguisb.ttf",
    "C:/Windows/Fonts/seguisbi.ttf",
    "C:/Windows/Fonts/seguisli.ttf",
    "C:/Windows/Fonts/SegUIVar.ttf",
    "C:/Windows/Fonts/SitkaVF.ttf",
    "C:/Windows/Fonts/SitkaVF-Italic.ttf",
    "C:/Windows/Fonts/tahoma.ttf",
    "C:/Windows/Fonts/tahomabd.ttf",
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/timesbd.ttf",
    "C:/Windows/Fonts/timesbi.ttf",
    "C:/Windows/Fonts/timesi.ttf",
    "C:/Windows/Fonts/verdana.ttf",
    "C:/Windows/Fonts/verdanab.ttf",
    "C:/Windows/Fonts/verdanai.ttf",
    "C:/Windows/Fonts/verdanaz.ttf",
]


# ============================================================================
# LOAD WORDS
# ============================================================================


def load_hard_words():
    src = Path(__file__).parent / "dictionary" / "vietnamese_words_clean.txt"
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
    coeffs = np.linalg.solve(
        np.array(matrix, dtype=np.float64), np.array(result, dtype=np.float64)
    )
    return coeffs.tolist()


def augment(img, allow_none=True):
    """Augmentation cho OCR van ban - gia lap anh chuc thuc te."""
    choices = [
        "none",
        "none",
        "none",
        "none",
        "none",  # 40% giữ nguyên — model học dấu rõ ràng
        "blur",
        "blur",  # giảm từ 3→2, blur nhẹ hơn
        "noise",
        "noise",  # giảm từ 4→2
        "contrast_down",
        "contrast_up",
        "jpeg",
        "jpeg",  # giảm từ 3→2
        "rotate",
        "rotate",  # giảm từ 3→2
        "shadow",
        "shadow",  # giảm từ 4→2
        "glare",  # giảm từ 3→1
        "perspective",
        "perspective",  # giảm từ 3→2
        "downscale",  # giảm từ 2→1
        "wave",  # hiếm
        "elastic",  # hiếm
        "motion_blur",  # giảm từ 2→1
        "defocus",  # giảm từ 2→1
    ]
    if not allow_none:
        choices = [c for c in choices if c != "none"]
    a = random.choice(choices)
    if a == "none":
        pass
    elif a == "blur":
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.8)))
    elif a == "noise":
        arr = np.array(img)
        intensity = random.randint(15, 35)  # noise vừa đủ, không che dấu
        n = np.random.randint(0, intensity, arr.shape, dtype=np.uint8)
        offset = intensity // 2
        img = Image.fromarray(
            np.clip(arr.astype(int) + n.astype(int) - offset, 0, 255).astype(np.uint8)
        )
    elif a == "contrast_up":
        img = ImageEnhance.Contrast(img).enhance(random.uniform(1.1, 1.5))
    elif a == "contrast_down":
        img = ImageEnhance.Contrast(img).enhance(random.uniform(0.65, 0.9))
    elif a == "jpeg":
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=random.randint(55, 80))
        buf.seek(0)
        img = Image.open(buf).convert("RGB")
    elif a == "rotate":
        img = img.rotate(random.uniform(-3, 3), fillcolor=(255, 255, 255), expand=False)
    elif a == "shadow":
        # Shadow thực tế: gradient mềm, chéo từ 1 hướng
        arr = np.array(img, dtype=np.float32)
        h, w = arr.shape[:2]
        for _ in range(random.randint(1, 2)):
            # Chọn hướng ánh sáng (shadow từ đối diện)
            direction = random.choice(["top", "bottom", "left", "right", "corner"])
            darkness = random.randint(30, 70)

            # Tạo mask gradient theo hướng (dùng numpy, không loop)
            mask = np.zeros((h, w), dtype=np.float32)
            if direction == "top":
                ys = np.linspace(1, 0, h)[:, np.newaxis]
                mask = np.clip(ys / random.uniform(0.4, 0.7), 0, 1)
                mask = np.broadcast_to(mask, (h, w)).copy()
            elif direction == "bottom":
                ys = np.linspace(0, 1, h)[:, np.newaxis]
                mask = np.clip(ys / random.uniform(0.4, 0.7), 0, 1)
                mask = np.broadcast_to(mask, (h, w)).copy()
            elif direction == "left":
                xs = np.linspace(1, 0, w)[np.newaxis, :]
                mask = np.clip(xs / random.uniform(0.4, 0.7), 0, 1)
                mask = np.broadcast_to(mask, (h, w)).copy()
            elif direction == "right":
                xs = np.linspace(0, 1, w)[np.newaxis, :]
                mask = np.clip(xs / random.uniform(0.4, 0.7), 0, 1)
                mask = np.broadcast_to(mask, (h, w)).copy()
            else:  # corner
                cx, cy = random.choice([(0, 0), (w, 0), (0, h), (w, h)])
                yy, xx = np.mgrid[0:h, 0:w]
                dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
                max_dist = math.sqrt(w**2 + h**2) * random.uniform(0.3, 0.6)
                mask = np.clip(1 - dist / max_dist, 0, 1)

            # Làm mượt mask để shadow có edge mềm
            mask = (
                np.array(
                    Image.fromarray((mask * 255).astype(np.uint8)).filter(
                        ImageFilter.GaussianBlur(radius=random.uniform(8, 25))
                    )
                ).astype(np.float32)
                / 255.0
            )

            # Áp dụng shadow
            shadow = (mask * darkness)[:, :, np.newaxis]
            arr = np.clip(arr - shadow, 0, 255)
        img = Image.fromarray(arr.astype(np.uint8))
    elif a == "glare":
        arr = np.array(img)
        h, w = arr.shape[:2]
        for _ in range(random.randint(1, 2)):
            x1 = random.randint(0, w // 2)
            y1 = random.randint(0, h // 2)
            x2 = x1 + random.randint(w // 4, w // 2)
            y2 = y1 + random.randint(h // 4, h // 2)
            brightness = random.randint(35, 70)
            arr[y1:y2, x1:x2] = np.clip(
                arr[y1:y2, x1:x2].astype(int) + brightness, 0, 255
            ).astype(np.uint8)
        img = Image.fromarray(arr)
    elif a == "perspective":
        w, h = img.size
        offset = min(w, h) * random.uniform(0.02, 0.07)
        src_corners = [(0, 0), (w, 0), (w, h), (0, h)]
        dst_corners = [
            (random.uniform(0, offset), random.uniform(0, offset)),
            (w - random.uniform(0, offset), random.uniform(0, offset)),
            (w - random.uniform(0, offset), h - random.uniform(0, offset)),
            (random.uniform(0, offset), h - random.uniform(0, offset)),
        ]
        coeffs = _perspective_coeffs(src_corners, dst_corners)
        img = img.transform(
            (w, h), Image.PERSPECTIVE, coeffs, Image.BICUBIC, fillcolor=(255, 255, 255)
        )
    elif a == "downscale":
        # Giảm nhẹ kích thước rồi phóng lại — mô phỏng ảnh chụp xa
        w, h = img.size
        scale = random.uniform(0.75, 0.92)  # nhẹ nhàng, vẫn đọc được
        small = img.resize(
            (max(int(w * scale), 16), max(int(h * scale), 16)), Image.BILINEAR
        )
        img = small.resize((w, h), Image.BILINEAR)
    elif a == "wave":
        # Mô phỏng chữ trên trang sách bị cong — dịch chuyển dạng sóng sin
        w, h = img.size
        arr = np.array(img)
        result = np.full_like(arr, 255)  # nền trắng
        amplitude = random.uniform(2, 10)  # độ lệch pixel
        freq = random.uniform(0.8, 2.0)  # số vòng sóng
        for y in range(h):
            dx = int(amplitude * math.sin(2 * math.pi * freq * y / h))
            src_start = max(0, -dx)
            src_end = min(w, w - dx)
            dst_start = max(0, dx)
            length = src_end - src_start
            if length > 0:
                result[y, dst_start : dst_start + length] = arr[y, src_start:src_end]
        img = Image.fromarray(result)
    elif a == "elastic":
        # Mô phỏng giấy nhăn/bẹp — biến dạng elastic ngẫu nhiên mượt
        w, h = img.size
        arr = np.array(img)
        result = np.full_like(arr, 255)
        scale = random.uniform(4, 9)
        sigma = random.uniform(3, 6)
        # Tạo displacement field ngẫu nhiên
        dx = np.random.uniform(-scale, scale, (h, w)).astype(np.float32)
        dy = np.random.uniform(-scale, scale, (h, w)).astype(np.float32)

        # Làm mượt: map [-scale,scale] → [0,255] → blur → map lại
        def _smooth_field(field, radius, s):
            u8 = ((field + s) / (2 * s) * 255).astype(np.uint8)
            u8 = np.array(
                Image.fromarray(u8).filter(ImageFilter.GaussianBlur(radius=radius))
            )
            return (u8.astype(np.float32) / 255) * (2 * s) - s

        dx = _smooth_field(dx, sigma, scale)
        dy = _smooth_field(dy, sigma, scale)
        # Áp dụng displacement
        y_idx, x_idx = np.mgrid[0:h, 0:w]
        x_new = np.clip(x_idx + dx.astype(int), 0, w - 1)
        y_new = np.clip(y_idx + dy.astype(int), 0, h - 1)
        result[y_idx, x_idx] = arr[y_new, x_new]
        img = Image.fromarray(result)
    elif a == "motion_blur":
        # Mô phỏng rung tay khi chụp — nhòe theo một hướng
        w, h = img.size
        arr = np.array(img, dtype=np.float32)
        result = np.zeros_like(arr)
        kernel_size = random.randint(5, 12)
        angle = random.uniform(0, 360)
        dx = math.cos(math.radians(angle))
        dy = math.sin(math.radians(angle))
        for i in range(kernel_size):
            t = i - kernel_size // 2
            shift_x = int(round(dx * t))
            shift_y = int(round(dy * t))
            shifted = np.zeros_like(arr)
            y_src_start = max(0, shift_y)
            y_dst_start = max(0, -shift_y)
            y_len = h - abs(shift_y)
            x_src_start = max(0, shift_x)
            x_dst_start = max(0, -shift_x)
            x_len = w - abs(shift_x)
            if y_len > 0 and x_len > 0:
                shifted[
                    y_src_start : y_src_start + y_len, x_src_start : x_src_start + x_len
                ] = arr[
                    y_dst_start : y_dst_start + y_len, x_dst_start : x_dst_start + x_len
                ]
            result += shifted
        result = np.clip(result / kernel_size, 0, 255).astype(np.uint8)
        img = Image.fromarray(result)
    elif a == "defocus":
        # Mô phỏng lệch tiêu cự — nhòe tròn (disk blur)
        radius = random.uniform(1.5, 3.0)
        img = img.filter(ImageFilter.GaussianBlur(radius=radius))
        # Giảm nét thêm một chút để giống out-of-focus thật
        arr = np.array(img, dtype=np.float32)
        noise = np.random.normal(0, random.uniform(3, 8), arr.shape)
        img = Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))
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
        f"{w1} khác {w2}",
        f"{w1} và {w2}",
        f"phân biệt {w1} với {w2}",
        f"không phải {w1} mà là {w2}",
        f"từ {w1} đến {w2}",
        f"{w1} hay {w2}",
        f"{w2} chứ không phải {w1}",
        f"viết đúng: {w1}, sai: {w2}",
        f"{w1} / {w2}",
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


def gen_plain_words(singles, plain_singles, fonts, img_dir, idx, no_augment=False):
    """Mix từ không dấu + có dấu để model học KHÔNG thêm dấu sai chỗ."""
    n_plain = random.randint(3, 6)
    n_diac = random.randint(2, 5)
    plain = random.sample(plain_singles, min(n_plain, len(plain_singles)))
    diac = random.sample(singles, min(n_diac, len(singles)))
    words = plain + diac
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
        default=2000,
        help="Số mẫu train (mặc định 2000)",
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
            (lambda **kw: gen_word_list(singles, **kw), 10),  # từ đơn đã đủ cover
            (lambda **kw: gen_phrase_list(phrases, **kw), 25),  # ↑ cụm từ
            (lambda **kw: gen_confusion_pair(confusion, singles, **kw), 15),
            (lambda **kw: gen_grouped_words(groups, **kw), 10),  # ↓ từ đơn dư
            (lambda **kw: gen_mixed_line(singles, phrases, **kw), 15),
            (
                lambda **kw: gen_dense_sentence(phrases, singles, **kw),
                25,
            ),  # ↑ nhiều phrase/sample
            (lambda **kw: gen_plain_words(singles, plain_singles, **kw), 10),  # chống bias thêm dấu
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
