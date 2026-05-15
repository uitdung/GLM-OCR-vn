# Hướng dẫn Fine-tune GLM-OCR cho tiếng Việt

Flow hoàn chỉnh từ sinh data → train → test local.

---

## Mục lục

1. [Cài đặt](#1-cài-đặt)
2. [Sinh dataset](#2-sinh-dataset)
3. [Fine-tune trên Google Colab](#3-fine-tune-trên-google-colab)
4. [Test local](#4-test-local)
5. [So sánh original vs finetuned](#5-so-sánh-original-vs-finetuned)
6. [Dùng qua Ollama](#6-dùng-qua-ollama)
7. [Cấu hình training](#7-cấu-hình-training)
8. [Chi tiết dataset](#8-chi-tiết-dataset)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Cài đặt

```bash
pip install Pillow numpy transformers torch editdistance
```

Ngoài ra cần cài [LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) nếu train local (không dùng Colab).

---

## 2. Sinh dataset

```bash
python generate_vietnamese_dataset_v3.py --num_samples 20000 --augment_copies 3 --test_ratio 0.1
```

### Các tham số

| Tham số | Mặc định | Mô tả |
|---|---|---|
| `--output_dir` | `./vietnamese_ocr` | Thư mục output |
| `--num_samples` | `2000` | Số ảnh gốc (unique texts) |
| `--augment_copies` | `1` | Số bản/ảnh gốc (`3` = 1 gốc + 2 augment) |
| `--test_ratio` | `0.1` | Tỷ lệ test set (10%) |
| `--seed` | `42` | Random seed |
| `--no_augment` | off | Sinh ảnh sạch, không augmentation |

### Khuyến nghị cấu hình

| Mục đích | Lệnh |
|---|---|
| **Train chất lượng cao** | `--num_samples 20000 --augment_copies 3 --test_ratio 0.1` |
| **Nhanh, test thử** | `--num_samples 5000 --augment_copies 2 --test_ratio 0.1` |
| **Ảnh sạch (publish)** | `--num_samples 10000 --no_augment` |

### Output

```
vietnamese_ocr/
├── vietnamese_ocr.json          # Tất cả samples (backward compat)
├── vietnamese_ocr_train.json    # 90% — dùng để train
├── vietnamese_ocr_test.json     # 10% — dùng để đánh giá
└── images/
    ├── txt_00000.png
    ├── txt_00001.png
    └── ...
```

### 14 loại augmentation

Model học chịu được biến dạng thực tế qua các loại augmentation:

| Loại | Mô phỏng |
|---|---|
| blur | Ảnh mờ (Gaussian) |
| noise | Nhiễu ngẫu nhiên |
| contrast ± | Sáng/tối quá mức |
| jpeg | Nén JPEG (ảnh chụp lại) |
| rotate | Xoay nhẹ ±2° |
| shadow | Bóng đen ngẫu nhiên |
| glare | Vùng chói sáng |
| perspective | Méo phối cảnh (chụp nghiêng) |
| downscale | Giảm resolution rồi phóng lại |
| wave | Cong dạng sóng (trang sách gập) |
| elastic | Nhăn/bẹp mượt (giấy nhàu) |
| motion_blur | Nhòe do rung tay khi chụp |
| defocus | Nhòe do lệch tiêu cự (out of focus) |

### Upload lên Google Drive

```bash
# PowerShell
Compress-Archive -Path vietnamese_ocr -DestinationPath vietnamese_ocr.zip -Force
```

Upload `vietnamese_ocr.zip` vào Google Drive `My Drive` root.

---

## 3. Fine-tune trên Google Colab

Mở `finetune_glm_ocr_vn_1epoch.ipynb` trên Colab (GPU T4 16GB).

### Flow từng bước

```
Bước 1-6: Setup (chỉ 1 lần đầu)
  ├── 1. Check GPU
  ├── 2. Mount Drive & extract dataset
  ├── 3. Install LLaMA-Factory
  ├── 4. Download model gốc
  ├── 5. Register dataset
  └── 6. Write training config

Bước 7: Train ← lặp lại mỗi epoch
  └── Tự động detect checkpoint cũ để resume

Bước 8: Merge & Đánh giá ← chạy sau mỗi epoch
  ├── Merge LoRA weights
  ├── Chạy eval trên test set
  ├── Hiển thị bảng PROGRESS ACROSS ALL EPOCHS
  └── Tự động lưu kết quả lên Drive

Bước 10: Save model cuối cùng
```

### Quyết định train thêm hay dừng

Sau mỗi lần chạy eval, đọc bảng kết quả:

| DA% | Hành động |
|---|---|
| < 80% | Train thêm epoch |
| 80-90% | Train thêm, tập trung vào nhóm yếu |
| 90-95% | Có thể dừng, cân nhắc gen data mới |
| ≥ 95% | **Save model** → chuyển sang test local |

Nếu epoch mới toàn 🔴 → **overfitting**, dùng checkpoint epoch trước.

### Cấu hình training hiện tại

```yaml
finetuning_type: lora
lora_rank: 16
lora_alpha: 32
lora_dropout: 0.05
lora_target: all

learning_rate: 5.0e-5
lr_scheduler_type: constant_with_warmup   # LR ổn định khi resume
warmup_ratio: 0.05
num_train_epochs: 1                        # train từng epoch

val_size: 0.0                              # Dùng test set riêng thay vì val split
```

---

## 4. Test local

Sau khi train xong, tải thư mục model từ Drive (`glm-ocr-vn`) về máy.

### Tham số `test_local.py`

| Tham số | Mặc định | Mô tả |
|---|---|---|
| `--model_path` | *(bắt buộc)* | Đường dẫn đến model đã merge |
| `--image` | *(bắt buộc)* | File ảnh, thư mục, hoặc nhiều file |
| `--task` | `text` | Loại OCR: `text`, `table`, `formula` |
| `--show_image` | off | Hiển thị ảnh (cần GUI) |

### Ví dụ

```bash
# Test 1 ảnh
npm run test:image -- --model_path ./glm-ocr-vn --image test.png

# Test nhiều ảnh
npm run test:image -- --model_path ./glm-ocr-vn --image img1.png img2.png img3.png

# Test toàn bộ thư mục
npm run test:image -- --model_path ./glm-ocr-vn --image ./test_images/

# Đổi loại task
npm run test:image -- --model_path ./glm-ocr-vn --image table.png --task table
```

### Yêu cầu

- **GPU**: ~4GB VRAM (model 0.9B rất nhẹ)
- **Không GPU**: Tự fallback CPU (chậm hơn nhưng vẫn chạy)
- Model cần đủ file: `config.json`, `model.safetensors` (hoặc `model-001.safetensors` + `model.safetensors.index.json`), `tokenizer.json`, `tokenizer_config.json`, `chat_template.jinja`, `processor_config.json`, `generation_config.json`

---

## 5. So sánh original vs finetuned

Chạy trên test set để xem fine-tune cải thiện bao nhiêu.

### Tham số `compare_models.py`

| Tham số | Mặc định | Mô tả |
|---|---|---|
| `--ft_path` | `./glm-ocr-vn` | Đường dẫn model finetuned |
| `--test_json` | `./vietnamese_ocr/vietnamese_ocr_test.json` | File test set JSON |
| `--n` | `0` | Số ảnh test. `0` = tất cả, `5` = nhanh |

### Ví dụ

```bash
# Test toàn bộ test set (chính xác nhất, chậm)
npm run test:compare

# Test nhanh 5 ảnh (seed=42 cố định, tái lập được)
npm run test:compare -- --n 5

# Test 100 ảnh
npm run test:compare -- --n 100

# Chỉ định model và test set khác
npm run test:compare -- --ft_path ./my-model --test_json ./data/test.json
```

Script tự động:
1. Download model gốc từ HuggingFace (`zai-org/GLM-OCR`) nếu chưa có
2. Load model finetuned từ `--ft_path`
3. Chạy inference trên N ảnh từ test set
4. Hiển thị so sánh + bảng diacritic accuracy theo nhóm dấu

Output mẫu:
```
============================================================
  Metric                 Original    Finetuned        Δ
============================================================
  Word Acc                 26.8%       87.8%   +61.0%
  Char Acc                 77.3%       97.4%   +20.1%

  Diacritic Acc (FT)       84.2%  (32/38)

  Nhóm dấu               Accuracy     Chi tiết
  ──────────────────── ────────── ────────────
  ă (ắằẳẵặ)                100.0%  (3/3)
  â (ấầẩẫậ)                100.0%  (4/4)
  ê (ếềểễệ)                 77.8%  (7/9)
  ô (ốồổỗộ)                 77.8%  (7/9)
  ơ (ớờởỡợ)                 83.3%  (5/6)
  ư (ứừửữự)                100.0%  (5/5)
  đ                         50.0%  (1/2)
============================================================
```

---

## 6. Dùng qua Ollama

Chạy model finetuned qua Ollama — nhanh, tiện, không cần code.

### Tạo model Ollama

```bash
# Copy preprocessor_config.json (Ollama cần file này)
cp glm-ocr-vn/processor_config.json glm-ocr-vn/preprocessor_config.json

# Tạo model (chạy từ trong thư mục model)
cd glm-ocr-vn && ollama create glm-ocr-vn -f Modelfile
```

### Test qua API

```bash
# Chạy inference qua Ollama API
python -c "
import base64, json, requests
img_b64 = base64.b64encode(open('test.png', 'rb').read()).decode()
resp = requests.post('http://localhost:11434/api/generate', json={
    'model': 'glm-ocr-vn',
    'prompt': 'Text Recognition:',
    'images': [img_b64],
    'stream': False,
})
print(resp.json()['response'])
"
```

### Test qua Python script

```bash
pip install glmocr
```

Tạo `config.yaml`:
```yaml
pipeline:
  ocr_api:
    api_host: localhost
    api_port: 11434
    api_path: /api/generate
    model: glm-ocr-vn
    api_mode: ollama_generate
```

```bash
glmocr parse test.png --config config.yaml
```

### Quản lý model

```bash
# Xem danh sách model
ollama list

# Xem chi tiết
ollama show glm-ocr-vn

# Xóa model
ollama rm glm-ocr-vn
```

---

## 7. Cấu hình training

### Scheduler: `constant_with_warmup`

LR ramp up trong 5% bước đầu, sau đó giữ cố định. Cho phép **resume train từng epoch** mà LR không bị decay về 0 (khác với `cosine`).

```
LR
 │    ╭────────────────────────────── 5e-05 (cố định)
 │   ╱
 │  ╱ warmup (5% steps)
 │ ╱
 └───────────────────────────────────→ steps
```

### Lora_rank: 16

- Rank 8: quá ít cho 3,544 từ có dấu kép
- **Rank 16: cân bằng tốt** giữa capacity và overfit risk
- Rank 32: dễ overfit trên synthetic data

### Learning rate: 5e-5

- 1e-4: quá cao cho synthetic data, dễ overfit
- **5e-5: ổn định**, giảm đều loss mà không spike
- 1e-5: quá thấp, học chậm

---

## 8. Chi tiết dataset

### Word list

`vietnamese_hard_words.txt` — 3,544 mục (2,034 từ đơn + 1,510 cụm từ), chứa:
- Nguyên âm kép: ă, â, ê, ô, ơ, ư
- Dấu thanh trên nguyên âm kép: ắ ằ ẳ ẵ ặ, ấ ầ ẩ ẫ ậ, ế ề ể ễ ệ, ố ồ ổ ỗ ộ, ớ ờ ở ỡ ợ, ứ ừ ử ữ ự
- Chữ đ

### 6 loại sample

| Loại | Tỷ lệ | Mô tả | Ví dụ |
|---|---|---|---|
| word_list | ~20% | 8-16 từ đơn ngẫu nhiên | `lưỡi  trường  khuyết` |
| phrase_list | ~20% | 2-4 cụm từ | `chuyên nghiệp, buồn rười rượi` |
| confusion | ~15% | Cặp từ dễ nhầm + từ phụ | `chuồng khác chuộng  ngưỡn` |
| grouped | ~15% | Từ cùng nhóm dấu | `ắc ằ ẳ ẵ ặ  …` |
| mixed | ~15% | Cụm từ + từ đơn trên 2 dòng | `bán sống bán chết\nlưỡi ngưỡng` |
| dense | ~15% | Cụm từ ghép đoạn có dấu câu | `chân trời góc bể. cổ lỗ sĩ.` |

### Viết hoa (60% samples)

Ngẫu nhiên: giữ nguyên / hoa đầu câu / title case / ALL CAPS / tên riêng hoa.

### Quy trình lọc word list

```
vietnam-dict-words.txt (36,534 từ)
  → filter_hard_words.py → 20,378 từ (chỉ giữ từ có dấu kép)
  → lọc tay → 3,544 từ/cụm từ
```

---

## 9. Troubleshooting

### `ValueError: image has wrong mode` khi gen data

PIL GaussianBlur không hỗ trợ float32. Đã fix trong code bằng cách map qua uint8. Đảm bảo dùng bản mới nhất của `generate_vietnamese_dataset_v3.py`.

### `OSError: no file named model.safetensors` khi test local

Model merge từ LLaMA-Factory có thể xuất ra `model-001.safetensors` thay vì `model.safetensors`. Cần tạo file index:

```bash
cd glm-ocr-vn
python -c "
from safetensors import safe_open
import json, os
f = 'model-001.safetensors'
with safe_open(f, framework='pt') as sf:
    keys = list(sf.keys())
index = {'metadata': {'total_size': os.path.getsize(f)}, 'weight_map': {k: f for k in keys}}
json.dump(index, open('model.safetensors.index.json', 'w'), indent=2)
print(f'Created index with {len(keys)} weights')
"
```

### Colab disconnect giữa epoch

Checkpoint được auto-save lên Drive sau mỗi epoch. Chạy lại cell train — script tự động detect checkpoint cũ và resume.

### Loss không giảm ở epoch 2+

Nếu dùng `cosine` scheduler, LR sẽ bị decay về 0 khi resume. Đổi sang `constant_with_warmup` (đã fix trong config hiện tại).
