"""
Vietnamese OCR Dataset Generator v3 — Final
=============================================

Đọc từ khó từ vietnamese_hard_words.txt (20K+ từ có dấu kép từ từ điển chính thức).
Sinh ảnh train chỉ chứa từ model hay sai. Dedup: không trùng nội dung text.

Cách dùng:
    python generate_vietnamese_dataset_v3.py --num_samples 2000
"""

import os, json, random, argparse, io
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
# TẢI TỪ KHÓ TỪ FILE
# ============================================================================

def load_hard_words():
    """Đọc từ file đã lọc, tách từ đơn và cụm từ."""
    src = Path(__file__).parent / "vietnamese_hard_words.txt"
    with open(src, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]
    
    singles = [w for w in words if " " not in w]
    phrases = [w for w in words if " " in w]
    
    # Nhóm từ đơn theo loại dấu để gen_grouped_words
    groups = {
        "ă": [w for w in singles if any(c in w for c in "ắằẳẵặ")],
        "â": [w for w in singles if any(c in w for c in "ấầẩẫậ")],
        "ê": [w for w in singles if any(c in w for c in "ếềểễệ")],
        "ô": [w for w in singles if any(c in w for c in "ốồổỗộ")],
        "ơ": [w for w in singles if any(c in w for c in "ớờởỡợ")],
        "ư": [w for w in singles if any(c in w for c in "ứừửữự")],
        "ĩ": [w for w in singles if "ĩ" in w],
    }
    
    # Cặp dễ nhầm — chỉ khác 1 dấu
    confusion = []
    for i, w1 in enumerate(singles):
        for w2 in singles[i+1:]:
            # Cùng chiều dài, chỉ khác 1 ký tự
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
    try: return ImageFont.truetype(fp, sz)
    except: return ImageFont.load_default()

BG = [(255,255,255), (250,248,240), (245,245,245), (255,253,245), (240,248,255)]

def render(text, fp, fs=24, bg=(255,255,255), tc=(0,0,0), pad=25, ls=8):
    font = load_font(fp, fs)
    lines = text.split("\n")
    lh = fs + ls
    mw = max((font.getbbox(l)[2]-font.getbbox(l)[0] for l in lines if l), default=100)
    img = Image.new("RGB", (max(mw+pad*2,120), len(lines)*lh+pad*2), bg)
    d = ImageDraw.Draw(img)
    y = pad
    for l in lines:
        d.text((pad, y), l, fill=tc, font=font); y += lh
    return img

def augment(img):
    a = random.choice(["none","none","blur","noise","contrast_up","contrast_down","jpeg","rotate"])
    if a=="blur": img=img.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.2,0.8)))
    elif a=="noise":
        arr=np.array(img); n=np.random.randint(0,random.randint(5,15),arr.shape,dtype=np.uint8)
        img=Image.fromarray(np.clip(arr.astype(int)+n.astype(int)-7,0,255).astype(np.uint8))
    elif a=="contrast_up": img=ImageEnhance.Contrast(img).enhance(random.uniform(1.1,1.3))
    elif a=="contrast_down": img=ImageEnhance.Contrast(img).enhance(random.uniform(0.75,0.95))
    elif a=="jpeg":
        buf=io.BytesIO(); img.save(buf,format="JPEG",quality=random.randint(70,88))
        buf.seek(0); img=Image.open(buf).convert("RGB")
    elif a=="rotate": img=img.rotate(random.uniform(-1.5,1.5),fillcolor=(255,255,255),expand=False)
    return img

def pick(fonts): return random.choice(fonts)
def ri(a,b): return random.randint(a,b)

# ============================================================================
# DEDUP
# ============================================================================

_seen = set()

def unique(text):
    if text in _seen: return None
    _seen.add(text)
    return text


# ============================================================================
# GENERATORS
# ============================================================================

def gen_word_list(singles, fonts, img_dir, idx):
    """Danh sách từ đơn khó — 8-16 từ."""
    n = ri(8,16)
    words = random.sample(singles, min(n, len(singles)))
    random.shuffle(words)
    text = "  ".join(words)
    text = unique(text)
    if not text: return None
    fp, fs = pick(fonts), ri(18,28)
    img = augment(render(text, fp, fs, random.choice(BG)))
    f = f"txt_{idx:05d}.png"; img.save(img_dir/f)
    return {"messages":[{"role":"user","content":"<image>Text Recognition:"},{"role":"assistant","content":text}],"images":[f"vietnamese_ocr/{f}"]}

def gen_phrase_list(phrases, fonts, img_dir, idx):
    """2-4 cụm từ."""
    n = ri(2,4)
    sel = random.sample(phrases, min(n, len(phrases)))
    random.shuffle(sel)
    text = ", ".join(sel)
    text = unique(text)
    if not text: return None
    fp, fs = pick(fonts), ri(16,24)
    img = augment(render(text, fp, fs, random.choice(BG)))
    f = f"txt_{idx:05d}.png"; img.save(img_dir/f)
    return {"messages":[{"role":"user","content":"<image>Text Recognition:"},{"role":"assistant","content":text}],"images":[f"vietnamese_ocr/{f}"]}

def gen_confusion_pair(confusion, singles, fonts, img_dir, idx):
    """Cặp từ dễ nhầm + thêm từ khó."""
    w1, w2 = random.choice(confusion)
    templates = [
        f"{w1} khác {w2}", f"{w1} và {w2}", f"phân biệt {w1} với {w2}",
        f"không phải {w1} mà là {w2}", f"từ {w1} đến {w2}",
        f"{w1} hay {w2}", f"{w2} chứ không phải {w1}",
        f"viết đúng: {w1}, sai: {w2}", f"{w1} / {w2}",
    ]
    tmpl = random.choice(templates)
    extra = random.sample(singles, ri(2,5))
    text = tmpl + "  " + "  ".join(extra)
    text = unique(text)
    if not text: return None
    fp, fs = pick(fonts), ri(20,30)
    img = augment(render(text, fp, fs, random.choice(BG)))
    f = f"txt_{idx:05d}.png"; img.save(img_dir/f)
    return {"messages":[{"role":"user","content":"<image>Text Recognition:"},{"role":"assistant","content":text}],"images":[f"vietnamese_ocr/{f}"]}

def gen_grouped_words(groups, fonts, img_dir, idx):
    """Từ nhóm theo loại dấu kép."""
    keys = random.sample(list(groups.keys()), min(ri(2,3), len(groups)))
    words = []
    for k in keys:
        g = groups[k]
        words += random.sample(g, min(ri(3,7), len(g)))
    random.shuffle(words)
    text = "  ".join(words)
    text = unique(text)
    if not text: return None
    fp, fs = pick(fonts), ri(20,28)
    img = augment(render(text, fp, fs, random.choice(BG)))
    f = f"txt_{idx:05d}.png"; img.save(img_dir/f)
    return {"messages":[{"role":"user","content":"<image>Text Recognition:"},{"role":"assistant","content":text}],"images":[f"vietnamese_ocr/{f}"]}

def gen_mixed_line(singles, phrases, fonts, img_dir, idx):
    """1 cụm từ + 3-6 từ đơn xen kẽ."""
    phrase = random.choice(phrases)
    words = random.sample(singles, ri(3,6))
    random.shuffle(words)
    text = phrase + "\n" + "  ".join(words)
    text = unique(text)
    if not text: return None
    fp, fs = pick(fonts), ri(18,26)
    img = augment(render(text, fp, fs, random.choice(BG)))
    f = f"txt_{idx:05d}.png"; img.save(img_dir/f)
    return {"messages":[{"role":"user","content":"<image>Text Recognition:"},{"role":"assistant","content":text}],"images":[f"vietnamese_ocr/{f}"]}

def gen_dense_sentence(phrases, singles, fonts, img_dir, idx):
    """2-3 cụm từ ghép thành đoạn."""
    sel = random.sample(phrases, ri(2,3))
    random.shuffle(sel)
    # Thêm vài từ đơn cho đặc
    extra = random.sample(singles, ri(2,4))
    text = ". ".join(sel) + ". " + " ".join(extra)
    text = unique(text)
    if not text: return None
    fp, fs = pick(fonts), ri(16,22)
    img = augment(render(text, fp, fs, random.choice(BG)))
    f = f"txt_{idx:05d}.png"; img.save(img_dir/f)
    return {"messages":[{"role":"user","content":"<image>Text Recognition:"},{"role":"assistant","content":text}],"images":[f"vietnamese_ocr/{f}"]}


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Vietnamese OCR Dataset Generator v3")
    parser.add_argument("--output_dir", type=str, default="./vietnamese_ocr")
    parser.add_argument("--num_samples", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed); np.random.seed(args.seed)

    out = Path(args.output_dir)
    img_dir = out / "vietnamese_ocr"
    img_dir.mkdir(parents=True, exist_ok=True)

    fonts = [f for f in VERIFIED_FONTS if os.path.exists(f)]
    
    print("Đang tải từ điển...")
    singles, phrases, groups, confusion = load_hard_words()
    print(f"✓ {len(fonts)} font")
    print(f"  {len(singles):,} từ đơn, {len(phrases):,} cụm từ, {len(confusion):,} cặp nhầm, {len(groups)} nhóm dấu")

    generators = [
        (lambda **kw: gen_word_list(singles, **kw),                    20),
        (lambda **kw: gen_phrase_list(phrases, **kw),                   20),
        (lambda **kw: gen_confusion_pair(confusion, singles, **kw),     15),
        (lambda **kw: gen_grouped_words(groups, **kw),                  15),
        (lambda **kw: gen_mixed_line(singles, phrases, **kw),           15),
        (lambda **kw: gen_dense_sentence(phrases, singles, **kw),       15),
    ]

    tw = sum(w for _,w in generators)
    counts = {i: int(args.num_samples*w/tw) for i,(_,w) in enumerate(generators)}
    names = ["word_list","phrase_list","confusion","grouped","mixed","dense"]

    print(f"\nPhân bổ {args.num_samples} samples:")
    for i,nm in enumerate(names):
        print(f"  {nm:20s}: {counts[i]:5d} ({counts[i]/args.num_samples*100:.0f}%)")

    dataset = []
    idx = 0
    skipped = 0
    for gi, (gf, _) in enumerate(generators):
        n = counts[gi]
        generated = 0
        attempts = 0
        while generated < n and attempts < n * 3:
            attempts += 1
            try:
                result = gf(fonts=fonts, img_dir=img_dir, idx=idx)
                if result:
                    dataset.append(result)
                    idx += 1
                    generated += 1
                else:
                    skipped += 1
            except Exception as e:
                skipped += 1
            if idx % 100 == 0 and idx > 0:
                print(f"  {idx}/{args.num_samples}... (bỏ qua {skipped} trùng)")

    jp = out / "vietnamese_ocr.json"
    with open(jp, "w", encoding="utf-8") as f: json.dump(dataset, f, ensure_ascii=False, indent=2)
    print(f"\n✅ {len(dataset)} samples (bỏ qua {skipped} trùng)")
    print(f"   Ảnh: {img_dir}")
    print(f"   JSON: {jp}")

if __name__ == "__main__":
    main()
