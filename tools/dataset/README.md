# Vietnamese OCR Dataset — Generator & Fine-tune

Sinh ảnh training từ 3,534 từ/cụm từ tiếng Việt có dấu kép, dùng fine-tune GLM-OCR nhận diện dấu tiếng Việt.

## Dependencies

```bash
pip install Pillow numpy
```

## Các script

### 1. `font_tester_v2.py` — Test font

Render tất cả font hệ thống với từ có dấu kép, xuất ảnh kiểm tra font nào hiển thị đúng.

```bash
python font_tester_v2.py
```

Output: thư mục `font_test_output/` chứa ảnh test từng font.

### 2. `generate_vietnamese_dataset_v3.py` — Sinh dataset

Sinh ảnh + JSON (ShareGPT format) từ `vietnamese_hard_words.txt`.

```bash
# Mặc định: 2,000 ảnh có augmentation
python generate_vietnamese_dataset_v3.py

# 10,000 ảnh sạch (cho publish)
python generate_vietnamese_dataset_v3.py --num_samples 10000 --no_augment

# 10,000 gốc + 20,000 augment = 30,000 ảnh (cho training)
python generate_vietnamese_dataset_v3.py --num_samples 10000 --augment_copies 3
```

| Flag | Mặc định | Mô tả |
|---|---|---|
| `--output_dir` | `./vietnamese_ocr` | Thư mục output |
| `--num_samples` | `2000` | Số ảnh gốc |
| `--seed` | `42` | Random seed |
| `--no_augment` | off | Sinh ảnh sạch, không augmentation |
| `--augment_copies` | `1` | Số bản/ảnh gốc (`3` = gốc + 2 augment) |

Output:
```
vietnamese_ocr/
├── vietnamese_ocr.json    # ShareGPT format
└── images/
    ├── txt_00000.png
    └── ...
```

### 3. `finetune_glm_ocr_vn_1epoch.ipynb` — Fine-tune trên Colab

**Trước khi chạy:** Sinh dataset → zip → upload lên Google Drive.

```bash
python generate_vietnamese_dataset_v3.py --num_samples 2000
powershell Compress-Archive -Path vietnamese_ocr -DestinationPath vietnamese_ocr.zip -Force
```

Upload `vietnamese_ocr.zip` vào Google Drive `My Drive`, rồi mở notebook trên Colab và chạy theo từng bước.

## Dataset

**Word list:** `vietnamese_hard_words.txt` — 3,534 mục (2,034 từ đơn + 1,500 cụm từ), chứa dấu kép (ắ ằ ẳ ẵ ặ ấ ầ ẩ ẫ ậ ế ề ể ễ ệ ố ồ ổ ỗ ộ ớ ờ ở ỡ ợ ứ ừ ử ữ ự ĩ).

**6 loại sample (tỷ lệ đều 15-20%):**

| Loại | Mô tả | Ví dụ |
|---|---|---|
| word_list | 8-16 từ đơn | `lưỡi  trường  khuyết` |
| phrase_list | 2-4 cụm từ | `chuyên nghiệp, buồn rười rượi` |
| confusion | Cặp từ dễ nhầm | `chuồng khác chuộng  ngưỡn` |
| grouped | Từ cùng nhóm dấu | `ắc ằ ẳ ẵ ặ  …` |
| mixed | Cụm từ + từ đơn | `bán sống bán chết\nlưỡi ngưỡng` |
| dense | Cụm từ ghép đoạn | `chân trời góc bể. cổ lỗ sĩ.` |

**Augmentation (70% ảnh bị biến đổi):** blur, noise, contrast ±, JPEG nén, xoay ±2°, bóng tối, chói sáng.

**Viết hoa (60% samples):** giữ nguyên / hoa đầu câu / title case / ALL CAPS / tên riêng.

## Quy trình lọc word list

```
vietnam-dict-words.txt (36,534 từ)
  → filter_hard_words.py → 20,378 từ (chỉ giữ từ có dấu kép)
  → lọc tay (loại gạch nối, trùng, dài, ít giá trị) → 3,534 từ
```

## File

| File | Mô tả |
|---|---|
| `vietnamese_hard_words.txt` | Word list (3,534 từ) |
| `generate_vietnamese_dataset_v3.py` | Sinh ảnh + JSON |
| `font_tester_v2.py` | Test font tiếng Việt |
| `finetune_glm_ocr_vn_1epoch.ipynb` | Colab notebook fine-tune |
| `finetune_glm_ocr_vn.ipynb` | Colab notebook (bản cũ, nhiều epoch) |
