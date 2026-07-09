"""
Font tester v2 — Test 73 font với các từ phức tạp nhất tiếng Việt.
Tập trung: nguyên âm kép + dấu kép (ắ ằ ẳ ẵ ặ, ấ ầ ẩ ẫ ậ, ứ ừ ử ữ ự...)

Cách dùng:
    python font_tester_v2.py
"""

import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

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
# TEST TEXT — Từ phức tạp nhất tiếng Việt
# ============================================================================

# Nguyên âm kép + dấu kép (HARDEST — 2 dấu trên 1 chữ)
HARDEST_CHARS = [
    # a + breve/mũ + dấu thanh (10 ký tự, 2 dấu chồng nhau)
    "ắ ằ ẳ ẵ ặ ấ ầ ẩ ẫ ậ",
    # e/o + mũ + dấu thanh
    "ế ề ể ễ ệ ố ồ ổ ỗ ộ",
    # o/u + sừng + dấu thanh
    "ớ ờ ở ỡ ợ ứ ừ ử ữ ự",
]

# Từ có nguyên âm kép + dấu kép — khó nhất tiếng Việt
HARDEST_WORDS = [
    # a-breve + dấu thanh
    "lắm rắm ngắn chằm thằn lằn mẵng đặc",
    "nhằn nhặn xẳng chắn đang vàng hằng nhẵn vằng",
    # a-circumflex + dấu thanh
    "nhất mật lực tần tấn thân chần hẩm rẫn",
    "bận vần nhẩn lẫm chẫm tất cẩn hẵn vẫn",
    # e-circumflex + dấu thanh
    "nghệ triệt diệt bệ nhệ kệch hiệu hiệp thiệp",
    # CHỮA: these had errors before
    "nghĩa ngợi ngữ ngờ ỡ ở hỷ xỷ lỳ khỷ",
    # o-circumflex + dấu thanh
    "đố số bộ đồ hồ chỗ đổ ổ độ",
    "lốp rổ đỗ ngỗ cổ phỗng bộ hộ",
    # o-horn + dấu thanh
    "cớ bớ lớn đỡ cứ tự dự mừng lừng",
    "hưởng rưỡi lưỡi khướu mười khựng",
    # u-horn + dấu thanh
    "từ tư tử tự chữ dự mựa thừa lừa",
]

# Nguyên âm ba + dấu (cực kỳ phức tạp)
TRIPLE_VOWEL_WORDS = [
    "khuyên quyển huyển thuyển khuynh quỳnh",
    "khuỷu khuyết huyệt khuyển khuyễn quyễu",
    "thuỵ khuỵ khuỵ súy khuyết thuyết thuyệt",
    "ngụy luỵ mỏi tuỵ thuỵ khuyễm huyền",
]

# Tên người + địa danh có dấu phức tạp
COMPLEX_NAMES = [
    "Huỳnh Ngọc Thuỳ Khuê Linh Khánh",
    "Nguyễn Thị Hồng Ngát Diễm My Hạnh",
    "Đặng Minh Quang Tuấn Dũng Hưởng",
    "Huỳnh Phú Hải Lưỡng Thiện Ngà",
    "Buôn Ma Thuột Đắk Lắk Đắk Nông Nghi Xuân",
    "Điện Biên Phủ Huế Quy Nhơn Tuy Hòa",
    "Pleiku Kon Tum Sóc Trăng Trà Vinh",
]

# Từ ghép phức tạp thực tế
COMPOUND_WORDS = [
    "độc lập tự do hạnh phúc bình đẳng",
    "chính quyền nghĩa vụ quốc phòng an ninh",
    "khoa học công nghệ thông tin viễn thông",
    "giáo dục đào tạo văn hóa nghệ thuật",
    "xây dựng kiến trúc quy hoạch đô thị",
    "tài chính ngân hàng chứng khoán bảo hiểm",
    "y tế sức khỏe bệnh viện điều trị phẫu thuật",
    "nông nghiệp lâm nghiệp ngư nghiệp thủy lợi",
]

# Toàn bộ 167 nguyên âm có dấu tiếng Việt (exhaustive)
ALL_VOWELS_WITH_MARKS = [
    "a á à ả ã ạ",
    "ă ắ ằ ẳ ẵ ặ",
    "â ấ ầ ẩ ẫ ậ",
    "e é è ẻ ẽ ẹ",
    "ê ế ề ể ễ ệ",
    "i í ì ỉ ĩ ị",
    "o ó ò ỏ õ ọ",
    "ô ố ồ ổ ỗ ộ",
    "ơ ớ ờ ở ỡ ợ",
    "u ú ù ủ ũ ụ",
    "ư ứ ừ ử ữ ự",
    "y ý ỳ ỷ ỹ ỵ",
]


def gen_test_image(font_path: str, output_path: str):
    font_name = os.path.basename(font_path)
    try:
        font = ImageFont.truetype(font_path, 20)
        font_title = ImageFont.truetype(font_path, 16)
        font_section = ImageFont.truetype(font_path, 18)
    except Exception:
        return False

    lines = []

    # Title
    lines.append((f"[{font_name}]", font_title, (180, 0, 0)))
    lines.append(("", font, (0, 0, 0)))

    # Section 1: Nguyên âm kép + dấu kép (2 dấu chồng)
    lines.append(
        (
            "▼ NGUYÊN ÂM KÉP + DẤU KÉP (2 dấu chồng nhau — khó nhất):",
            font_section,
            (0, 0, 150),
        )
    )
    for row in HARDEST_CHARS:
        lines.append((f"  {row}", font, (0, 0, 0)))

    lines.append(("", font, (0, 0, 0)))

    # Section 2: Từ phức tạp nhất
    lines.append(("▼ TỪ CÓ NGUYÊN ÂM KÉP + DẤU KÉP:", font_section, (0, 0, 150)))
    for row in HARDEST_WORDS:
        lines.append((f"  {row}", font, (0, 0, 0)))

    lines.append(("", font, (0, 0, 0)))

    # Section 3: Nguyên âm ba
    lines.append(("▼ NGUYÊN ÂM BA + DẤU:", font_section, (0, 0, 150)))
    for row in TRIPLE_VOWEL_WORDS:
        lines.append((f"  {row}", font, (0, 0, 0)))

    lines.append(("", font, (0, 0, 0)))

    # Section 4: Tên + địa danh
    lines.append(("▼ TÊN NGƯỜI + ĐỊA DANH:", font_section, (0, 0, 150)))
    for row in COMPLEX_NAMES:
        lines.append((f"  {row}", font, (0, 0, 0)))

    lines.append(("", font, (0, 0, 0)))

    # Section 5: Từ ghép thực tế
    lines.append(("▼ TỪ GHÉP THỰC TẾ:", font_section, (0, 0, 150)))
    for row in COMPOUND_WORDS:
        lines.append((f"  {row}", font, (0, 0, 0)))

    lines.append(("", font, (0, 0, 0)))

    # Section 6: Bảng nguyên âm đầy đủ
    lines.append(("▼ BẢNG NGUYÊN ÂM ĐẦY ĐỦ (167 biến thể):", font_section, (0, 0, 150)))
    for row in ALL_VOWELS_WITH_MARKS:
        lines.append((f"  {row}", font, (0, 0, 0)))

    # Render
    padding = 25
    line_h = 28

    max_w = 0
    for text, f, _ in lines:
        if text:
            bbox = f.getbbox(text)
            w = bbox[2] - bbox[0]
            max_w = max(max_w, w)

    img_w = max(max_w + padding * 2, 600)
    img_h = len(lines) * line_h + padding * 2

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    y = padding
    for text, f, color in lines:
        if text:
            draw.text((padding, y), text, fill=color, font=f)
        y += line_h

    img.save(output_path)
    return True


def main():
    out = Path(__file__).parent / "output"
    img_dir = out / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for font_path in VERIFIED_FONTS:
        if not os.path.exists(font_path):
            continue
        name = os.path.basename(font_path)
        safe = name.replace("/", "_").replace("\\", "_")
        if gen_test_image(font_path, str(img_dir / f"{safe}.png")):
            count += 1
            print(f"  ✅ {name}")
        else:
            print(f"  🚫 {name}")

    print(f"\n✅ {count} ảnh test → {img_dir}/")
    print(f"Mở folder để kiểm tra bằng mắt, xóa ảnh font bị lỗi.")


if __name__ == "__main__":
    main()
