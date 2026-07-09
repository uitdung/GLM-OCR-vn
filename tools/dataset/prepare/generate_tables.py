"""
Generator ảnh TABLE tiếng Việt cho GLM-OCR
=============================================
Sinh bảng ngẫu nhiên (nhiều cấu trúc), render ảnh + ground-truth HTML.
Dùng prompt chuẩn official: "<image>Table Recognition:"
Output format ShareGPT — cùng schema với Stage 1.

Cách dùng:
    # Mặc định: 3000 ảnh table vào ./data/vietnamese_ocr_tables
    python prepare/generate_tables.py

    # Nhiều hơn + augment
    python prepare/generate_tables.py --num_train 5000 --augment_copies 2

Dataset sinh ra có thể ghép vào Stage 1 (merge JSON) hoặc train riêng.
"""

import argparse
import html
import io
import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# Import font + helpers từ generator Stage 1
import sys
sys.path.insert(0, str(Path(__file__).parent))
from generate_stage1 import (
    VERIFIED_FONTS,
    load_font,
    render,
    augment,
    BG,
    load_hard_words,
)

PROMPT = "<image>Table Recognition:"

OUT_DEFAULT = "../data/vietnamese_ocr_tables"


# ============================================================================
# DỮ LIỆU MẪU — vocab tiếng Việt để fill bảng
# ============================================================================
FIRST_NAMES = [
    "Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Phan", "Vũ", "Võ", "Đặng",
    "Bùi", "Đỗ", "Hồ", "Ngô", "Dương", "Lý", "Đinh", "Trịnh", "Châu",
]
GIVEN_NAMES = [
    "Văn Hùng", "Thị Hằng", "Minh Trí", "Quốc Anh", "Thị Kiều", "Hoàng Long",
    "Thị Hương", "Văn Nam", "Thị Nguyệt", "Minh Tú", "Quang Trung", "Thị Lan",
    "Hữu Phước", "Thị Mai", "Đức Anh", "Thị Hà", "Thanh Tùng", "Thị Bình",
    "Bảo Châu", "Gia Huy", "Thùy Trang", "Khánh Hoàn", "Mỹ Dung", "Tiến Dũng",
]
CITIES = ["Hà Nội", "Hồ Chí Minh", "Đà Nẵng", "Hải Phòng", "Cần Thơ",
          "Huế", "Nha Trang", "Vũng Tàu", "Quảng Ninh", "Biên Hòa"]
DEPTS = ["Kế toán", "Kỹ thuật", "Marketing", "Kinh doanh", "Nhân sự",
         "Tài chính", "Sản xuất", "IT", "Hành chính", "Mua hàng"]
PRODUCTS = [
    "Sách giáo khoa", "Vở tập viết", "Bút máy Thiên Long", "Thước kẻ trong",
    "Tẩy gôm", "Com-pa", "Sổ tay da", "Giấy photo A4", "Băng keo trong",
    "Kéo nhỏ", "Ghim bấm", "Bút đánh dấu",
]
SUBJECTS = ["Toán", "Ngữ văn", "Tiếng Anh", "Vật lý", "Hóa học", "Sinh học",
            "Lịch sử", "Địa lý", "Tin học", "Giáo dục thể chất"]
FOODS = [
    ("Phở bò", "Nước dùng bò hầm", "45.000đ"),
    ("Bún chả", "Thịt nướng than hoa", "50.000đ"),
    ("Bánh mì", "Thịt nguội pate", "25.000đ"),
    ("Cơm tấm", "Sườn nướng bưởi", "55.000đ"),
    ("Gỏi cuốn", "Tôm thịt rau thơm", "40.000đ"),
    ("Chè ba màu", "Đậu đỏ trân châu", "30.000đ"),
    ("Sinh tố bơ", "Sữa tươi đậu phộng", "35.000đ"),
    ("Cà phê sữa", "Phin nóng đậm đà", "28.000đ"),
    ("Trà đá chanh", "Đá cold brew mát lạnh", "18.000đ"),
    ("Bánh xèo", "Tôm thịt giá đỗ", "60.000đ"),
]
WEEKDAYS = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
MONTHS = ["Tháng 01", "Tháng 02", "Tháng 03", "Tháng 04", "Tháng 05", "Tháng 06",
          "Tháng 07", "Tháng 08", "Tháng 09", "Tháng 10", "Tháng 11", "Tháng 12"]


# ============================================================================
# RANDOM HELPERS
# ============================================================================
def r_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(GIVEN_NAMES)}"


def r_int(lo, hi):
    return str(random.randint(lo, hi))


def r_money(lo, hi, step=500):
    return f"{random.randint(lo // step, hi // step) * step:,}₫".replace(",", ".")


def r_phone():
    prefixes = ["090", "091", "093", "094", "097", "098", "086", "096"]
    return f"{random.choice(prefixes)} {random.randint(1000000, 9999999)}"


def r_date():
    return f"{random.randint(1, 28):02d}/{random.randint(1, 12):02d}/{random.randint(2020, 2026)}"


def r_grade():
    g = random.choice([9.5, 9.0, 8.5, 8.0, 7.5, 7.0, 6.5, 6.0, 5.5, 5.0])
    return f"{g:.1f}"


# ============================================================================
# TEMPLATE BẢNG — mỗi hàm trả về (title, headers, rows, aligns, kwargs)
# ============================================================================

def tpl_invoice():
    n = random.randint(3, 6)
    headers = ["STT", "Tên hàng hóa", "Đơn giá", "Số lượng", "Thành tiền"]
    rows = []
    total = 0
    for i in range(1, n + 1):
        p = random.choice(PRODUCTS)
        price = random.randint(5, 90) * 1000
        qty = random.randint(1, 12)
        amount = price * qty
        total += amount
        rows.append([str(i), p, f"{price:,}đ".replace(",", "."),
                     str(qty), f"{amount:,}đ".replace(",", ".")])
    total_row = ["", "TỔNG CỘNG", "", "", f"{total:,}đ".replace(",", ".")]
    title = random.choice(["HÓA ĐƠN BÁN HÀNG", "PHIẾU MUA HÀNG", "HÓA ĐƠN GTGT"])
    return title, headers, rows, ["c", "l", "r", "c", "r"], {"total_row": total_row}


def tpl_payroll():
    n = random.randint(4, 7)
    headers = ["Mã NV", "Họ và tên", "Phòng ban", "Lương CB", "Phụ cấp", "Thực lĩnh"]
    rows = []
    tot_cb = tot_pc = 0
    for i in range(n):
        cb = random.randint(12, 25) * 1000000
        pc = random.randint(10, 50) * 100000
        tot_cb += cb
        tot_pc += pc
        rows.append([f"NV-{random.randint(1, 99):03d}", r_name(),
                     random.choice(DEPTS), r_money(12000000, 25000000),
                     r_money(1000000, 5000000), r_money(13000000, 30000000)])
    total_row = ["", "TỔNG", "", f"{tot_cb:,}".replace(",", "."),
                 f"{tot_pc:,}".replace(",", "."), f"{tot_cb + tot_pc:,}".replace(",", ".")]
    return "BẢNG LƯƠNG NHÂN SỰ", headers, rows, \
        ["c", "l", "l", "r", "r", "r"], {"total_row": total_row}


def tpl_grades():
    n = random.randint(3, 9)
    # Số môn biến thiên: 2-4 môn, kéo theo cột ĐTB + Xếp loại
    subjects = random.sample(SUBJECTS, random.randint(2, 4))
    headers = ["Họ và tên"] + subjects + ["ĐTB", "Xếp loại"]
    rows = []
    for _ in range(n):
        marks = [random.choice([9, 8, 7, 6, 5]) + random.random()
                 for _ in subjects]
        avg = sum(marks) / len(marks)
        xl = "Giỏi" if avg >= 8.0 else "Khá" if avg >= 6.5 else "Trung bình"
        rows.append([r_name()] + [f"{m:.1f}" for m in marks]
                    + [f"{avg:.1f}", xl])
    aligns = ["l"] + ["c"] * len(subjects) + ["c", "c"]
    return "KẾT QUẢ HỌC TẬP HỌC KỲ I", headers, rows, aligns, {}


def tpl_schedule():
    n = random.randint(3, 6)  # số tiết
    n_days = random.randint(3, 6)
    days = random.sample(WEEKDAYS, n_days)
    headers = ["Tiết"] + days
    rows = []
    for t in range(1, n + 1):
        rows.append([str(t)] + [random.choice(SUBJECTS) for _ in days])
    return "THỜI KHÓA BIỂU TUẦN LỄ", headers, rows, \
        ["c"] + ["c"] * n_days, {}


def tpl_directory():
    n = random.randint(4, 10)
    # Chọn số cột hiển thị ngẫu nhiên
    possible = [
        (["STT", "Họ và tên", "Quê quán"],
         ["str(i)", "r_name()", "random.choice(CITIES)"], ["c", "l", "l"]),
        (["STT", "Họ và tên", "Năm sinh", "Quê quán"],
         ["str(i)", "r_name()", "r_int(1970, 2005)",
          "random.choice(CITIES)"], ["c", "l", "c", "l"]),
        (["STT", "Họ và tên", "Năm sinh", "Quê quán", "Số điện thoại"],
         ["str(i)", "r_name()", "r_int(1970, 2005)",
          "random.choice(CITIES)", "r_phone()"], ["c", "l", "c", "l", "c"]),
    ]
    headers, _, aligns = random.choice(possible)
    # build rows theo template cột đã chọn
    col_builders = {
        "STT": lambda i: str(i),
        "Họ và tên": lambda i: r_name(),
        "Năm sinh": lambda i: r_int(1970, 2005),
        "Quê quán": lambda i: random.choice(CITIES),
        "Số điện thoại": lambda i: r_phone(),
    }
    rows = [[col_builders[h](i) for h in headers] for i in range(1, n + 1)]
    title = random.choice(["DANH BẠ NHÂN SỰ", "DANH SÁCH CÁN BỘ",
                            "MỤC LỤC THÀNH VIÊN"])
    return title, headers, rows, aligns, {}


def tpl_menu():
    n = random.randint(4, 8)
    chosen = random.sample(FOODS, n)
    # 2 hoặc 3 cột (có/không mô tả)
    if random.random() < 0.5:
        headers = ["Món ăn", "Giá"]
        aligns = ["l", "r"]
        rows = [[f, p] for f, d, p in chosen]
        return "THỰC ĐƠN QUÁN ĂN", headers, rows, aligns, {}
    else:
        headers = ["Món ăn", "Mô tả", "Giá"]
        aligns = ["l", "l", "r"]
        rows = [[f, d, p] for f, d, p in chosen]
        return "THỰC ĐƠN QUÁN ĂN", headers, rows, aligns, {}


def tpl_sales():
    n = random.randint(4, 10)
    # số cột biến thiên: có/không % tăng, có/không quý
    variants = [
        (["Sản phẩm", "Số lượng", "Doanh thu"], ["l", "c", "r"], False),
        (["Sản phẩm", "Quý", "Doanh thu"], ["l", "c", "r"], False),
        (["Sản phẩm", "Quý", "Số lượng", "Doanh thu"], ["l", "c", "c", "r"], False),
        (["Sản phẩm", "Quý", "Số lượng", "Doanh thu", "% tăng"],
         ["l", "c", "c", "r", "r"], True),
    ]
    headers, aligns, with_pct = random.choice(variants)
    rows = []
    for _ in range(n):
        row = [random.choice(PRODUCTS)]
        if "Quý" in headers:
            row.append(f"Q{random.randint(1, 4)}/{random.randint(2024, 2026)}")
        if "Số lượng" in headers:
            row.append(r_int(500, 5000))
        if "Doanh thu" in headers:
            row.append(r_money(5000000, 80000000))
        if with_pct:
            pct = random.randint(-15, 40)
            sign = "+" if pct >= 0 else ""
            row.append(f"{sign}{pct}%")
        rows.append(row)
    return "BÁO CÁO DOANH THU", headers, rows, aligns, {}


TEMPLATES = [
    tpl_invoice, tpl_payroll, tpl_grades, tpl_schedule,
    tpl_directory, tpl_menu, tpl_sales,
]


# ============================================================================
# STYLE — random cho từng ảnh (chỉ đen-trắng-xám, không màu mè)
# ============================================================================
TEXT = (15, 15, 15)
GRID_COLORS = [(160, 160, 160), (130, 130, 130), (110, 110, 110), (100, 100, 100)]
ZEBRA_COLORS = [(247, 248, 250), (243, 246, 250), (240, 244, 248)]
HEADER_SHADE_COLORS = [(230, 232, 236), (225, 228, 232), (220, 223, 228)]


def rand_style():
    """Chọn kiểu trình bày table random. Tất cả style đậm sang đen — không màu mè.

    Tỉ lệ:
      - 20% borderless: KHÔNG có đường kẻ nào (grid dọc/ngang/khung đều off)
      - 80% còn lại: grid/border random như trước
    """
    # 20% borderless — tất cả line/border tắt, giống bảng thực tế không kẻ
    if random.random() < 0.20:
        return {
            "grid_horizontal": False,
            "grid_vertical": False,
            "border": False,
            "grid_color": random.choice(GRID_COLORS),
            "zebra": random.random() < 0.3,
            "zebra_color": random.choice(ZEBRA_COLORS),
            "header_shade": random.random() < 0.3,
            "header_color": random.choice(HEADER_SHADE_COLORS),
            "total_shade": random.random() < 0.3,
            "borderless": True,
        }
    return {
        "grid_horizontal": random.random() < 0.7,
        "grid_vertical": random.random() < 0.7,
        "grid_color": random.choice(GRID_COLORS),
        "border": random.random() < 0.6,
        "zebra": random.random() < 0.4,
        "zebra_color": random.choice(ZEBRA_COLORS),
        "header_shade": random.random() < 0.5,
        "header_color": random.choice(HEADER_SHADE_COLORS),
        "total_shade": random.random() < 0.5,
        "borderless": False,
    }


# ============================================================================
# RENDER ẢNH TABLE
# ============================================================================
def draw_table(title, headers, rows, col_align,
               font_path=VERIFIED_FONTS[0], fs=20,
               total_row=None, highlight_col=None, style=None,
               include_header=True):
    """Render ảnh table PIL, trả về (img, style).

    Args:
        include_header: True = render dòng header; False = bỏ header (chỉ data rows).
    """
    if style is None:
        style = rand_style()
    n_cols = len(headers)
    title_font = load_font(VERIFIED_FONTS[1], fs + 6)
    h_font = load_font(VERIFIED_FONTS[1], fs)   # bold
    f_font = load_font(font_path, fs)

    pad = 24
    cell_h = fs + 18
    title_h = fs + 40 if title else 0
    row_h = cell_h

    def tw(font, s):
        return font.getbbox(s)[2] - font.getbbox(s)[0]

    # col_w: lấy max width giữa header (nếu có) và rows
    col_w = []
    for i, h in enumerate(headers):
        w = tw(h_font, h) if include_header else 0
        for r in rows:
            w = max(w, tw(f_font, str(r[i])))
        col_w.append(w + 36)

    img_w = sum(col_w) + pad * 2
    header_rows = 1 if include_header else 0
    n_extra = 1 if total_row else 0
    img_h = title_h + cell_h * header_rows + row_h * len(rows) + pad + row_h * n_extra

    img = Image.new("RGB", (img_w, img_h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    gc = style["grid_color"]

    y = pad // 2
    if title:
        d.text((pad, y), title, fill=TEXT, font=title_font)
        y = title_h

    xs = [pad]
    for w in col_w:
        xs.append(xs[-1] + w)

    def align_x(i, text, font):
        w = tw(font, text)
        if col_align[i] == "c":
            return xs[i] + (col_w[i] - w) // 2
        if col_align[i] == "r":
            return xs[i] + col_w[i] - w - 18
        return xs[i] + 18

    # Header row (chỉ khi include_header=True)
    if include_header:
        if style["header_shade"]:
            d.rectangle([pad, y, img_w - pad, y + cell_h], fill=style["header_color"])
        for i, h in enumerate(headers):
            d.text((align_x(i, h, h_font), y + 9), h, fill=TEXT, font=h_font)
        y += cell_h

    # Data rows
    for ri, row in enumerate(rows):
        if style["zebra"] and ri % 2 == 1:
            d.rectangle([pad, y, img_w - pad, y + row_h], fill=style["zebra_color"])
        for i, cell in enumerate(row):
            d.text((align_x(i, cell, f_font), y + 9), str(cell), fill=TEXT, font=f_font)
        # horizontal grid line giữa các row
        if style["grid_horizontal"]:
            d.line([pad, y, img_w - pad, y], fill=gc, width=1)
        y += row_h

    # Total row (optional) — chỉ shade xám nhạt, ko vàng
    if total_row:
        if style["total_shade"]:
            d.rectangle([pad, y, img_w - pad, y + row_h], fill=style["header_color"])
        for i, cell in enumerate(total_row):
            d.text((align_x(i, cell, h_font), y + 9), str(cell), fill=TEXT, font=h_font)
        if style["grid_horizontal"]:
            d.line([pad, y, img_w - pad, y], fill=gc, width=1)
        y += row_h

    # Vertical grid lines + border ngoài
    yy0 = pad // 2 + title_h
    if include_header and style["grid_horizontal"]:
        d.line([pad, yy0, img_w - pad, yy0], fill=gc)  # dưới header
    if style["grid_vertical"]:
        for x in xs:
            d.line([x, yy0, x, y], fill=gc, width=1)
    if style["border"]:
        d.rectangle([pad, yy0, img_w - pad, y], outline=gc, width=1)
    if style["grid_horizontal"]:
        d.line([pad, y, img_w - pad, y], fill=gc, width=1)  # đáy

    return img, style


# ============================================================================
# GROUND TRUTH HTML (đúng format ví dụ bạn gửi + official prompt)
# ============================================================================
def to_html(title, headers, rows, total_row=None, include_header=True):
    """Sinh HTML table giống officedocument.

    Args:
        include_header: nếu False thì KHÔNG xuất dòng <tr> header, chỉ data rows.
    """
    parts = [f'<table border="1">']
    # Header (chỉ khi include_header)
    if include_header:
        parts.append("<tr>" + "".join(f"<td>{html.escape(str(h))}</td>" for h in headers) + "</tr>")
    # Rows
    for row in rows:
        parts.append(
            "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>"
        )
    if total_row:
        parts.append(
            "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in total_row) + "</tr>"
        )
    parts.append("</table>")
    return "".join(parts)


# ============================================================================
# WRAPPER: 1 sample
# ============================================================================
def make_table_sample(idx, img_dir, fonts, no_augment, template_name=None):
    """Sinh 1 bảng random → ảnh + HTML → sample ShareGPT. Trả về dict hoặc None.

    Args:
        template_name: tên template ('invoice','payroll','grades',...).
                       None = random trong tất cả template.
    """
    # Map tên → hàm template
    tpl_map = {t.__name__[4:]: t for t in TEMPLATES}
    if template_name:                      # <--- thêm
        if template_name not in tpl_map:   # <--- thêm
            raise ValueError(
                f"Template '{template_name}' không tồn tại. "
                f"Có: {list(tpl_map)}")    # <--- thêm
        template = tpl_map[template_name]  # <--- thêm
    else:                                  # <--- thêm
        template = random.choice(TEMPLATES)
    title, headers, rows, aligns, extra = template()
    title = ""

    fp = random.choice(fonts)
    fs = random.choice([16, 18, 20, 22])
    style = rand_style()
    # 10% ảnh có header, 90% không (bỏ dòng header)
    include_header = random.random() < 0.10
    img, _ = draw_table(
        title, headers, rows, aligns,
        font_path=fp, fs=fs,
        total_row=extra.get("total_row"),
        highlight_col=None,   # bỏ highlight màu mè
        style=style,
        include_header=include_header,
    )
    if not no_augment:
        img = augment(img)
    fname = f"tbl_{idx:05d}.png"
    img.save(img_dir / fname)

    html_gt = to_html(title, headers, rows, extra.get("total_row"),
                      include_header=include_header)

    # Lưu cả raw data để re-augment sau
    raw = {
        "title": title, "headers": headers, "rows": rows,
        "aligns": aligns, "total_row": extra.get("total_row"),
        "highlight_col": extra.get("highlight_col"),
        "include_header": include_header,
    }
    return {
        "messages": [
            {"role": "user", "content": PROMPT},
            {"role": "assistant", "content": html_gt},
        ],
        "images": [f"images/{fname}"],
        "_raw": raw,
    }


# ============================================================================
# MAIN
# ============================================================================
N_VAL = 100  # giữ constant với Stage 1


def main():
    parser = argparse.ArgumentParser(description="Tạo dataset TABLE tiếng Việt")
    parser.add_argument("--output_dir", type=str, default=OUT_DEFAULT)
    parser.add_argument("--num_train", type=int, default=3000)
    parser.add_argument("--num_test", type=int, default=200)
    parser.add_argument("--num_val", type=int, default=N_VAL)
    parser.add_argument("--augment_copies", type=int, default=1)
    parser.add_argument("--no_augment", action="store_true")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    out = Path(args.output_dir)
    img_dir = out / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    fonts = [f for f in VERIFIED_FONTS if __import__("os").path.exists(f)]
    print(f"✓ {len(fonts)} font • {len(TEMPLATES)} template bảng")
    print(f"  Templates: {[t.__name__[4:] for t in TEMPLATES]}")

    total_target = args.num_train + args.num_test + args.num_val
    idx = 0
    dataset = []
    print(f"\nĐang sinh {total_target:,} bảng (train {args.num_train:,}, "
          f"val {args.num_val}, test {args.num_test}) ...")

    while idx < total_target:
        try:
            sample = make_table_sample(idx, img_dir, fonts, args.no_augment)
            if sample:
                dataset.append(sample)
                idx += 1
                if idx % 200 == 0:
                    print(f"  {idx}/{total_target}...")
        except Exception as e:
            print(f"  skip #{idx}: {e}")

    # Augment copies cho tập train (giữ nguyên val/test)
    if args.augment_copies > 1:
        n_keep = args.num_test + args.num_val
        train_data = dataset[:-n_keep] if n_keep < len(dataset) else []
        print(f"\nSinh {args.augment_copies - 1} bản augment cho {len(train_data)} bảng train ...")
        for copy_i in range(1, args.augment_copies):
            for item in train_data:
                raw = item["_raw"]
                fp = random.choice(fonts)
                fs = random.choice([16, 18, 20, 22])
                img, _ = draw_table(
                    raw["title"], raw["headers"], raw["rows"], raw["aligns"],
                    font_path=fp, fs=fs,
                    total_row=raw["total_row"], highlight_col=None,
                    style=rand_style(),
                    include_header=raw.get("include_header", True),
                )
                img = augment(img, allow_none=False)
                fname = f"tbl_{idx:05d}.png"
                img.save(img_dir / fname)
                dataset.append({
                    "messages": [
                        {"role": "user", "content": PROMPT},
                        {"role": "assistant", "content": to_html(
                            raw["title"], raw["headers"], raw["rows"], raw["total_row"],
                            include_header=raw.get("include_header", True))},
                    ],
                    "images": [f"images/{fname}"],
                    "_raw": raw,
                })
                idx += 1
                if idx % 200 == 0:
                    print(f"  {idx}/{len(train_data) * args.augment_copies + n_keep}...")

    # Strip internal _raw trước khi save
    for item in dataset:
        item.pop("_raw", None)

    # Shuffle rồi chia train/val/test
    random.seed(args.seed)
    random.shuffle(dataset)
    n_test = args.num_test
    n_val = args.num_val
    test = dataset[:n_test]
    val = dataset[n_test:n_test + n_val]
    train = dataset[n_test + n_val:]

    out_path = out / "vietnamese_ocr_tables.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    with open(out / "vietnamese_ocr_tables_train.json", "w", encoding="utf-8") as f:
        json.dump(train, f, ensure_ascii=False, indent=2)
    with open(out / "vietnamese_ocr_tables_val.json", "w", encoding="utf-8") as f:
        json.dump(val, f, ensure_ascii=False, indent=2)
    with open(out / "vietnamese_ocr_tables_test.json", "w", encoding="utf-8") as f:
        json.dump(test, f, ensure_ascii=False, indent=2)

    meta = {
        "num_train": len(train),
        "num_val": len(val),
        "num_test": len(test),
        "total": len(dataset),
        "augment_copies": args.augment_copies,
        "seed": args.seed,
        "task": "table",
        "prompt": PROMPT,
        "templates": [t.__name__[4:] for t in TEMPLATES],
    }
    with open(out / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Đã sinh {len(dataset):,} bảng")
    print(f"   Train: {len(train):,} | Val: {len(val)} | Test: {len(test)}")
    print(f"   Output: {out}")
    print(f"\n💡 Để ghép vào Stage 1, merge các file JSON:")
    print(f"   vietnamese_ocr/vietnamese_ocr_train.json + "
          f"vietnamese_ocr_tables/vietnamese_ocr_tables_train.json")


if __name__ == "__main__":
    main()
