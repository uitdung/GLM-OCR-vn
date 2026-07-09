"""
Preview: Render ảnh dạng TABLE tiếng Việt
==========================================
Tạo 6 ảnh table mẫu với nhiều phong cách (invoice, schedule, stats, matrix...)
dùng lại VERIFIED_FONTS + style từ generate_stage1.

Cách dùng:
    python prepare/render_table_preview.py

Output: table_preview/  (6 ảnh PNG để bạn xem thử)
"""

import sys
from pathlib import Path

# Import font + helpers từ generator
sys.path.insert(0, str(Path(__file__).parent))
from generate_stage1 import VERIFIED_FONTS, load_font

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "table_preview"
OUT.mkdir(parents=True, exist_ok=True)

# --- Style presets ---
HEADER_BG = (60, 90, 160)       # xanh đậm
HEADER_FG = (255, 255, 255)
ROW_ALT = (244, 247, 252)       # xanh nhạt xen kẽ
GRID = (180, 180, 180)
TEXT = (30, 30, 30)
TOTAL_BG = (255, 242, 204)      # vàng nhạt


def _fmt_ts(t):
    h = t // 60
    m = t % 60
    return f"{h:02d}:{m:02d}"


def draw_table(
    fname,
    title,
    headers,
    rows,
    *,
    font_path=VERIFIED_FONTS[0],
    fs=20,
    col_align=None,
    total_row=None,
    highlight_col=None,
    bg=(255, 255, 255),
):
    """Vẽ 1 ảnh table đơn giản, đẹp mắt.

    Args:
        title:      tiêu đề in đậm bên trên
        headers:    list[str]
        rows:       list[list[str]]
        col_align:  list['l'|'c'|'r'] — default toàn 'l'
        total_row:  row cuối highlight vàng (vd tổng tiền)
        highlight_col: index cột cần tô xanh nhạt nổi bật
    """
    n_cols = len(headers)
    if col_align is None:
        col_align = ["l"] * n_cols

    title_font = load_font(VERIFIED_FONTS[1], fs + 6)   # bold
    h_font = load_font(VERIFIED_FONTS[1], fs)            # bold
    f_font = load_font(font_path, fs)

    pad = 24
    cell_h = fs + 18
    title_h = fs + 40 if title else 0
    row_h = cell_h

    # Probe max width mỗi cột
    def tw(font, s):
        return font.getbbox(s)[2] - font.getbbox(s)[0]

    col_w = []
    for i, h in enumerate(headers):
        w = tw(h_font, h)
        for r in rows:
            w = max(w, tw(f_font, str(r[i])))
        col_w.append(w + 36)

    img_w = sum(col_w) + pad * 2
    img_h = title_h + cell_h + row_h * len(rows) + pad + (row_h if total_row else 0)

    img = Image.new("RGB", (img_w, img_h), bg)
    d = ImageDraw.Draw(img)

    # Title
    y = pad // 2
    if title:
        d.text((pad, y), title, fill=TEXT, font=title_font)
        y = title_h

    # Column x positions
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

    # Header row
    d.rectangle([pad, y, img_w - pad, y + cell_h], fill=HEADER_BG)
    for i, h in enumerate(headers):
        d.text((align_x(i, h, h_font), y + 9), h, fill=HEADER_FG, font=h_font)
    y += cell_h

    # Data rows
    for ri, row in enumerate(rows):
        bg_row = ROW_ALT if ri % 2 == 1 else (255, 255, 255)
        if highlight_col is not None and highlight_col >= 0:
            # tô nguyên bg hơi xanh
            bg_row = bg_row
        d.rectangle([pad, y, img_w - pad, y + row_h], fill=bg_row)
        # highlight 1 ô
        if highlight_col is not None:
            d.rectangle(
                [xs[highlight_col], y, xs[highlight_col + 1], y + row_h],
                fill=(220, 235, 255),
            )
        for i, cell in enumerate(row):
            d.text((align_x(i, cell, f_font), y + 9), str(cell), fill=TEXT, font=f_font)
        y += row_h

    # Total row (optional)
    if total_row:
        d.rectangle([pad, y, img_w - pad, y + row_h], fill=TOTAL_BG)
        for i, cell in enumerate(total_row):
            d.text((align_x(i, cell, h_font), y + 9), str(cell), fill=TEXT, font=h_font)
        y += row_h

    # Grid lines
    # horizontal
    yy = pad // 2 + title_h
    d.line([pad, yy, img_w - pad, yy], fill=GRID)
    # vertical between columns + outer
    for x in xs:
        d.line([x, pad // 2 + title_h, x, y], fill=GRID)
    d.line([img_w - pad, pad // 2 + title_h, img_w - pad, y], fill=GRID)

    img.save(OUT / fname)
    print(f"  ✅ {fname:30s} {img.size}")
    return img


def main():
    print(f"Rendering table previews → {OUT}\n")

    # 1) Hóa đơn / phiếu thu
    draw_table(
        "01_invoice.png",
        "HÓA ĐƠN BÁN HÀNG",
        ["STT", "Tên hàng", "Đơn giá", "Số lượng", "Thành tiền"],
        [
            ["1", "Sách giáo khoa", "45.000đ", "3", "135.000đ"],
            ["2", "Vở tập viết", "12.000đ", "10", "120.000đ"],
            ["3", "Bút máy Thiên Long", "28.000đ", "5", "140.000đ"],
            ["4", "Thước kẻ trong", "8.500đ", "8", "68.000đ"],
        ],
        col_align=["c", "l", "r", "c", "r"],
        total_row=["", "TỔNG CỘNG", "", "", "463.000đ"],
    )

    # 2) Thời khóa biểu
    draw_table(
        "02_schedule.png",
        "THỜI KHÓA BIỂU — TUẦN 12",
        ["Tiết", "Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu"],
        [
            ["1", "Toán", "Ngữ văn", "Toán", "Hóa học", "Ngữ văn"],
            ["2", "Toán", "Ngữ văn", "Toán", "Hóa học", "Ngữ văn"],
            ["3", "Vật lý", "Tiếng Anh", "Lịch sử", "Sinh học", "Địa lý"],
            ["4", "Vật lý", "Tiếng Anh", "Lịch sử", "Sinh học", "Địa lý"],
        ],
        col_align=["c", "c", "c", "c", "c", "c"],
    )

    # 3) Bảng thống kê điểm
    draw_table(
        "03_grades.png",
        "KẾT QUẢ HỌC TẬP — HỌC KỲ I",
        ["Họ và tên", "Toán", "Ngữ văn", "Tiếng Anh", "ĐTB", "Xếp loại"],
        [
            ["Nguyễn Thị Hằng", "8.5", "9.0", "7.8", "8.4", "Giỏi"],
            ["Trần Văn Hùng", "7.2", "6.8", "8.1", "7.4", "Khá"],
            ["Lê Thị Kiều", "9.1", "8.9", "8.5", "8.8", "Giỏi"],
            ["Phạm Quốc Anh", "6.5", "5.9", "7.0", "6.5", "Trung bình"],
        ],
        col_align=["l", "c", "c", "c", "c", "c"],
        highlight_col=5,
    )

    # 4) Ma trận so sánh (không grid dày, style tối giản)
    draw_table(
        "04_comparison.png",
        "SO SÁNH CÁC MODEL OCR",
        ["Model", "Tham số", "Word Acc", "Char Acc", "Tốc độ"],
        [
            ["GLM-OCR (gốc)", "1.1B", "26.8%", "77.3%", "Nhanh"],
            ["GLM-OCR + Stage 1", "1.1B", "87.8%", "97.4%", "Nhanh"],
            ["Qwen2-VL-2B", "2.0B", "91.2%", "98.1%", "Trung bình"],
            ["TrOCR-base", "0.3B", "54.3%", "85.2%", "Rất nhanh"],
        ],
        col_align=["l", "c", "c", "c", "c"],
        highlight_col=1,
    )

    # 5) Bảng lương / nhân sự (nhiều số, dấu phân cách)
    draw_table(
        "05_payroll.png",
        "BẢNG LƯƠNG THÁNG 06/2026",
        ["Mã NV", "Họ tên", "Phòng ban", "Lương CB", "Phụ cấp", "Thực lĩnh"],
        [
            ["NV-001", "Vũ Thị Hương", "Kế toán", "15.000.000", "2.500.000", "17.500.000"],
            ["NV-014", "Đặng Hoàng Long", "Kỹ thuật", "18.000.000", "3.000.000", "21.000.000"],
            ["NV-027", "Bùi Thị Nguyệt", "Marketing", "14.000.000", "1.800.000", "15.800.000"],
            ["NV-033", "Ngô Minh Trí", "Kinh doanh", "16.500.000", "4.200.000", "20.700.000"],
        ],
        col_align=["c", "l", "l", "r", "r", "r"],
        total_row=["", "TỔNG", "", "63.500.000", "11.500.000", "75.000.000"],
    )

    # 6) Bảng giá thực đơn (font serif)
    draw_table(
        "06_menu.png",
        "THỰC ĐƠN — QUÁN NƯỚC MÍT",
        ["Món", "Mô tả", "Giá"],
        [
            ["Nước mía tươi", "Ép lạnh, thêm chanh", "25.000đ"],
            ["Sinh tố bơ", "Sữa tươi + đậu phộng", "45.000đ"],
            ["Chè ba màu", "Đậu đỏ + trân châu", "35.000đ"],
            ["Bánh mì thịt nướng", "Thịt heo nướng than hoa", "40.000đ"],
        ],
        col_align=["l", "l", "r"],
        font_path=VERIFIED_FONTS[3],   # times.ttf — serif cho menu
        highlight_col=2,
    )

    print(f"\n✅ Đã tạo {len(list(OUT.glob('*.png')))} ảnh tại: {OUT}")
    print("   Mở thử để xem phong cách. Nếu ưng ý, tôi sẽ tích hợp vào dataset generator.")


if __name__ == "__main__":
    main()
