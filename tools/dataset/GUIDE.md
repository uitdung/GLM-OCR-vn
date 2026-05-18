# Hướng dẫn Fine-tune GLM-OCR cho tiếng Việt

Flow hoàn chỉnh từ sinh data → train → test local.

---

## Mục lục

1. [Model Technical Specs](#model-technical-specs)
2. [Cài đặt](#1-cài-đặt)
3. [Sinh dataset](#2-sinh-dataset)
4. [Fine-tune trên Google Colab](#3-fine-tune-trên-google-colab)
5. [Test local](#4-test-local)
6. [So sánh original vs finetuned](#5-so-sánh-original-vs-finetuned)
7. [Dùng qua Ollama](#6-dùng-qua-ollama)
8. [Cấu hình training](#7-cấu-hình-training)
9. [Chi tiết dataset](#8-chi-tiết-dataset)
10. [Troubleshooting](#9-troubleshooting)

---

## Model Technical Specs

### Tổng quan

| Thuộc tính | Giá trị |
|---|---|
| Architecture | `GlmOcrForConditionalGeneration` |
| Model type | `glm_ocr` |
| Total params | **~1.1B** |
| Trainable (LoRA rank 8) | ~7.5M (0.68%) |
| LoRA targets | `all` (q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj, qkv, gate_up_proj, lm_head) |
| Compute dtype | fp16 (T4) / bfloat16 (A100/L4) |
| Image tokens | ~999 tokens cho ảnh 768×1024 (merge_size=2) |

### Text LLM

| Thuộc tính | Giá trị |
|---|---|
| hidden_size | 1536 |
| num_hidden_layers | 16 |
| num_attention_heads | 16 |
| num_key_value_heads | 8 (GQA) |
| head_dim | 128 |
| intermediate_size | 4608 |
| max_position_embeddings | 131,072 |
| hidden_act | SiLU |
| vocab_size | 59,392 |
| RoPE | theta=10000, mRoPE sections=[16, 24, 24] |
| tie_word_embeddings | false |

### Vision Encoder

| Thuộc tính | Giá trị |
|---|---|
| depth (layers) | 24 |
| hidden_size | 1024 |
| image_size | 336 |
| patch_size | 14 |
| intermediate_size | 4096 |
| num_heads | 16 |
| out_hidden_size | 1536 |
| spatial_merge_size | 2 |
| temporal_patch_size | 2 |

### Processor

| Thuộc tính | Giá trị |
|---|---|
| Image processor | `Glm46VImageProcessor` |
| Video processor | `Glm46VVideoProcessor` |
| Normalization | CLIP mean=[0.481, 0.458, 0.408], std=[0.269, 0.261, 0.276] |
| Resample | bicubic (3) |

### Training pipeline

| Thuộc tính | Giá trị |
|---|---|
| Vision encoder | **frozen** (`freeze_vision_tower: true`) |
| Multi-modal projector | **unfrozen** (`freeze_multi_modal_projector: false`) |
| LLM | LoRA adapters trên tất cả linear layers |
| Gradient checkpointing | enabled |
| KV cache | disabled (during training) |

### Tokenizer tiếng Việt

GLM-OCR dùng vocab size 59,392. Kết quả phân tích:

| Từ | Token hóa | Số mảnh |
|---|---|---|
| `là` | `[' là']` | 1 ✅ |
| `Việt` | `[' Việt']` | 1 ✅ |
| `hóa` | `[' hóa']` | 1 ✅ |
| `Nguyễn` | `['Ng', 'uy', 'ễn']` | 3 ⚠️ |
| `Trãi` | `[' Tr', 'ãi']` | 2 ⚠️ |
| `kiệt` | `[' k', 'iệt']` | 2 ⚠️ |

- **Không có byte-fallback** → tokenizer đã chứa âm tiết tiếng Việt phổ biến
- Từ phức tạp bị cắt 2-3 mảnh → Projector phải ánh xạ 1 khối hình → nhiều tokens
- Ảnh 768×1024 tốn ~999 tokens, text 6-8 từ tốn ~20 tokens → tổng ~1020 tokens/sample

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

Upload `vietnamese_ocr.zip` vào Google Drive `My Drive/ocr_data/`.

---

## 3. Fine-tune trên Google Colab

Mở `finetune_glm_ocr_vn_1epoch.ipynb` trên Colab (GPU T4 16GB).

### Flow từng bước

```
Bước 1-5: Setup (chỉ 1 lần đầu)
  1. Check GPU
  2. Mount Drive & extract dataset từ My Drive/ocr_data/
  3. Install LLaMA-Factory + pin transformers 5.6.0
  4. Download model gốc từ HuggingFace
  5. Register dataset (auto split train/val/test từ meta.json)

Bước 6: Train (nhấn lại mỗi epoch)
  - Tự động detect checkpoint cũ để resume
  - Checkpoint tự lưu thẳng lên Drive (My Drive/ocr_data/glm-ocr-vn-checkpoints)
  - Eval chạy song song trên val set mỗi 500 steps

Bước 7: Merge & Eval (sau mỗi epoch)
  - Merge LoRA weights (lưu thẳng lên Drive: My Drive/ocr_data/glm-ocr-vn)
  - Chạy eval trên test set (số lượng từ meta.json)
  - Hiển thị bảng progress across all epochs
  - Tự động lưu kết quả eval lên Drive

Bước 8: Test ảnh bất kỳ
  - Upload 1 ảnh → so sánh kết quả Original vs Finetuned
```

### Quyết định train thêm hay dừng

Sau mỗi lần chạy eval, đọc bảng kết quả:

| DA% | Hành động |
|---|---|
| < 80% | Train thêm epoch |
| 80-90% | Train thêm, tập trung vào nhóm yếu |
| 90-95% | Có thể dừng, cân nhắc gen data mới |
| >= 95% | Model đã sẵn sàng trên Drive (`My Drive/ocr_data/glm-ocr-vn/`) |

Nếu epoch mới toàn đỏ (loss tăng) → overfitting, dùng checkpoint epoch trước.

### Chiến lược Curriculum Learning (2 giai đoạn)

GLM-OCR gốc được train cho tiếng Anh + tiếng Trung. Khi finetune cho tiếng Việt, nên chia 2 giai đoạn:

**Giai đoạn 1: Text-line Alignment** (hiện tại)
- Dữ liệu: ảnh dòng text ngắn 6-8 từ tiếng Việt (synthetic data)
- Mục tiêu: dạy Projector ánh xạ ký tự có dấu tiếng Việt → token
- Config: `cutoff_len: 2048`, `lora_rank: 8`
- Tham chiếu: paper VARY, TrOCR, Monkey

**Giai đoạn 2: Document-level SFT** (tương lai)
- Dữ liệu: ảnh tài liệu/hóa đơn/book thật, text dài
- Mục tiêu: dạy LLM đọc hiểu ngữ cảnh, format
- Config: `cutoff_len: 4096`, có thể tăng `lora_rank: 16-32`

### Cấu hình training hiện tại (Giai đoạn 1)

```yaml
finetuning_type: lora
lora_rank: 16
lora_alpha: 32
lora_dropout: 0.1
lora_target: all
freeze_vision_tower: true
freeze_multi_modal_projector: false   # Unfreeze để Projector học dấu TV

learning_rate: 1.0e-4
lr_scheduler_type: constant_with_warmup   # LR ổn định khi resume
warmup_ratio: 0.05
num_train_epochs: 1                     # train từng epoch

cutoff_len: 2048
per_device_train_batch_size: 4
gradient_accumulation_steps: 4          # effective batch = 16

fp16: true                              # T4 dùng fp16, A100/L4 đổi bf16
```

### Tại sao unfreeze Multi-modal Projector?

Khi dùng LoRA, LLM chỉ học qua adapters nhỏ. Nếu khóa luôn cả Projector:
- LLM không đủ capacity học tiếng Việt mới
- Projector không học cách ánh xạ dấu tiếng Việt → token bị cắt nhỏ
- Unfreeze Projector cho phép model xây "từ điển thị giác" mới cho tiếng Việt
- Projector nhỏ (~vài triệu params), tốn thêm ~1-2GB VRAM

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
 │    ╭────────────────────────────── 1e-04 (cố định)
 │   ╱
 │  ╱ warmup (5% steps)
 │ ╱
 └───────────────────────────────────→ steps
```

### Lora_rank: 16

- **Rank 16: cân bằng tốt cho unfreezing projector + LoRA trên synthetic data**
- Rank 8: quá hẹp khi unfreeze projector
- Rank 32: có thể dùng nếu data lớn (100K+) hoặc Giai đoạn 2

### Learning rate: 1e-4

- **1e-4: khuyến nghị của tác giả GLM-OCR cho LoRA**
- 5e-5: dùng được nhưng học chậm hơn, phù hợp rank 16
- 1e-5: quá thấp cho LoRA, chỉ dùng cho full fine-tuning

### Freeze strategy

| Thành phần | Trạng thái | Lý do |
|---|---|---|
| Vision Encoder | **Frozen** | Đã được pretrain tốt, không cần học lại |
| Multi-modal Projector | **Unfrozen** | Cần học ánh xạ mới cho dấu tiếng Việt |
| LLM | **LoRA** | Học tiếng Việt qua adapters, giữ kiến thức gốc |

### GPU T4 (16GB) — Thông số thực tế

```
VRAM sử dụng: ~6.9/15 GB (còn dư ~8 GB)
Speed: ~1.6s/step trên 60K samples (2 tiếng/epoch)
Effective batch size: 16 (4 device × 4 accum)
```

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
