# Vietnamese Hard Words — Dataset & Generator

Danh sách từ vựng tiếng Việt có dấu phức tạp, dùng để sinh ảnh training cho GLM-OCR fine-tune.

## Tổng quan

| | Số lượng |
|---|---|
| **Tổng cộng** | 3,534 |
| Từ đơn (1 word) | 2,034 |
| Cụm từ (2-4 words) | 1,500 |

### Phân bố cụm từ

| Loại | Số lượng | Ví dụ |
|---|---|---|
| 2 từ | 500 | chuyên nghiệp, thuyên chuyển, buồn rười rượi |
| 3 từ | 126 | bệnh nghề nghiệp, phòng thường trực |
| 4 từ | 874 | ba chân bốn cẳng, bán sống bán chết |

### Phân bố dấu kép

| Nhóm dấu | Số từ chứa | Ví dụ |
|---|---|---|
| ă/â (ắ ằ ẳ ẵ ặ ấ ầ ẩ ẫ ậ) | 1,331 | ẳm, chuồng, lưỡi, nghiện |
| ô/ơ (ố ồ ổ ỗ ộ ớ ờ ở ỡ ợ) | 1,691 | ổng, rỗng, lượn, tướng |
| ê (ế ề ể ễ ệ) | 1,098 | kể, nghệ, trễ, tổ chức |
| ư (ứ ừ ử ữ ự) | 481 | đủ, dứt, nữ, hứa |
| ĩ | 111 | nghĩa, tĩnh, sĩ, vĩ |

---

## Sinh dataset

### Clean version (cho publish lên Kaggle/HuggingFace)

```bash
python generate_vietnamese_dataset_v3.py --num_samples 10000 --no_augment --output_dir ./vietnamese_ocr_clean
```

Output:
```
vietnamese_ocr_clean/
├── vietnamese_ocr.json    # 10,000 samples, ShareGPT format
└── images/                # 10,000 ảnh sạch, không augmentation
    ├── txt_00000.png
    ├── txt_00001.png
    └── ...
```

### Augmented version (cho training trên Colab)

```bash
python generate_vietnamese_dataset_v3.py --num_samples 10000 --augment_copies 3 --output_dir ./vietnamese_ocr_augmented
```

Output:
```
vietnamese_ocr_augmented/
├── vietnamese_ocr.json    # 30,000 samples
└── images/                # 30,000 ảnh (10K gốc + 20K augment)
    ├── txt_00000.png
    ├── txt_00001.png
    └── ...
```

Mỗi ảnh gốc được sinh thêm 2 bản augment với nhiễu khác nhau → model học được "cùng 1 chữ, nhiều dạng ảnh".

---

## Augmentation

Mỗi ảnh có **70% xác suất bị biến đổi** (30% giữ nguyên):

| Phép biến đổi | Giả lập | Chi tiết |
|---|---|---|
| Blur nhẹ | Ảnh mờ | Gaussian blur radius 0.3-1.0 |
| Noise | Ảnh chụp nhiễu | Random noise ±20 |
| Tương phản ± | Chống sáng/tối | Contrast 0.7-1.4 |
| Nén JPEG | Gửi qua Zalo/Email | Quality 60-85 |
| Xoay nhẹ ±2° | Ảnh chụp hơi nghiêng | |
| Bóng tối cục bộ | Bóng đổ | 1-3 vùng tối, giảm 20-60 |
| Chói sáng cục bộ | Flash, lóe sáng | 1-2 vùng sáng, tăng 30-80 |

## Chữ viết hoa

60% samples có chữ viết hoa (giả lập văn bản thực tế):

| Mode | Xác suất | Ví dụ |
|---|---|---|
| Giữ nguyên | 40% | `nghĩa lưỡi trường` |
| Viết hoa đầu câu | 20% | `Nghĩa lưỡi trường` |
| Title case | 20% | `Nghĩa Lưỡi Trường` |
| ALL CAPS 1-2 từ | 10% | `NGHĨA lưỡi TRƯỜNG` |
| Tên riêng | 10% | `nghĩa Lưỡi Trường` |

---

## Quy trình lọc word list

### Nguồn gốc

Bắt đầu từ `vietnam-dict-words.txt` (36,534 từ) — từ điển tiếng Việt đầy đủ.

### Bước 1: Lọc lần 1 — Chỉ giữ từ có dấu kép

Chạy `filter_hard_words.py` để lọc từ `vietnam-dict-words.txt`:
- Giữ lại những từ chứa ít nhất 1 dấu kép: ắ ằ ẳ ẵ ặ ấ ầ ẩ ẫ ậ ế ề ể ễ ệ ố ồ ổ ỗ ộ ớ ờ ở ỡ ợ ứ ừ ử ữ ự ĩ
- Kết quả: 20,378 từ (2,054 từ đơn + 18,324 cụm từ)

### Bước 2: Lọc lần 2 — Loại bỏ nhiễu

Từ 20,378 → 3,534, loại bỏ:

| Loại bỏ | Số lượng | Lý do |
|---|---|---|
| Từ mượn có gạch nối | 20 | ắc-coóc, tuốc-nơ-vít, rốc-két... |
| Cụm từ trùng lặp | 1 | "cách mạng khoa học - kĩ thuật" x2 |
| Cụm từ có gạch nối / viết tắt | 4 | "hình thái kinh tế - xã h", "marx-lenin"... |
| Cụm từ 5+ từ | 96 | "định luật bảo toàn và chuyển hoá năng lượng"... |
| Cụm 2 từ ít giá trị | ~14,300 | Chỉ giữ 500/14,798 — ưu tiên cụm mà cả 2 từ đều có dấu kép |
| Cụm 3 từ ít giá trị | ~1,293 | Giữ 126 cụm có nhiều dấu nhất |

### Tiêu chí giữ lại

**Từ đơn:** Giữ toàn bộ 2,034 từ — đây là giá trị chính, mỗi từ đều chứa dấu kép.

**Cụm từ:** Ưu tiên theo `diacritic_score` = số từ trong cụm có chứa dấu kép. Cụm có nhiều dấu hơn được giữ trước:
- ✅ "buồn rười rượi" (3/3 từ có dấu) → giữ
- ✅ "chuyên nghiệp" (2/2 từ có dấu) → giữ
- ❌ "phương hướng" (1/2 từ có dấu) → bỏ (khi cần giảm)

---

## 6 loại sample generator

| Loại | Tỷ lệ | Mô tả | Ví dụ |
|---|---|---|---|
| word_list | 20% | 8-16 từ đơn ngẫu nhiên | `lưỡi trường khuyết nghĩa` |
| phrase_list | 20% | 2-4 cụm từ | `chuyên nghiệp, buồn rười rượi` |
| confusion | 15% | Cặp từ dễ nhầm + từ phụ | `chuồng khác chuộng lưỡi ngưỡng` |
| grouped | 15% | Từ nhóm theo loại dấu | `ắ ằ ẳ ẵ ặ` nhóm |
| mixed | 15% | Cụm từ + từ đơn xen kẽ | `bán sống bán chết\nlưỡi ngưỡng` |
| dense | 15% | 2-3 cụm từ ghép đoạn | `chân trời góc bể. cổ lỗ sĩ.` |

---

## File liên quan

| File | Mô tả |
|---|---|
| `vietnamese_hard_words.txt` | Danh sách từ cuối cùng (3,534 từ) |
| `generate_vietnamese_dataset_v3.py` | Generator — sinh ảnh + JSON từ word list |
| `filter_hard_words.py` | Script lọc lần 1 (từ điển gốc → hard words) |
| `finetune_glm_ocr_vn_1epoch.ipynb` | Colab notebook finetune (epoch-by-epoch) |
