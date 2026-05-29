# Báo cáo: Fine-tune GLM-OCR cho Tiếng Việt

> **Dự án:** uitdung/GLM-OCR-vn  
> **Thời gian:** 14/05/2026 – 19/05/2026 (6 ngày)  
> **Tác giả:** tuandung-specominc  
> **Số commit:** 31 commits (21 + 10)  
> **Dòng code:** ~79.500 dòng mới, 16 files

---

## 1. Tổng quan

### 1.1 Bài toán

[GLM-OCR](https://huggingface.co/zai-org/GLM-OCR) là mô hình Vision-Language (~1.1B params) của zai-org, được pre-train chủ yếu cho OCR tiếng Anh và tiếng Trung. Khi áp dụng lên tiếng Việt, mô hình **nhận diện kém các dấu thanh** (ă, â, ê, ô, ơ, ư, ã, õ, etc.), dẫn đến sai lệch nghĩa nghiêm trọng.

**Mục tiêu:** Fine-tune GLM-OCR để nhận diện chính xác dấu tiếng Việt, giảm CER (Character Error Rate) và đặc biệt giảm tỷ lệ **False Positive** — lỗi model tự thêm dấu vào text gốc không có dấu.

### 1.2 Kiến trúc mô hình

| Thành phần | Chi tiết |
|---|---|
| **Model** | `GlmOcrForConditionalGeneration` |
| **LLM** | 16 layers, hidden=1536, 16 heads, GQA 8 KV heads |
| **ViT** | 24 layers, hidden=1024, image=336×336, patch=14, spatial_merge=2 |
| **Projector** | Multi-modal projector (vision→language bridge) |
| **Tokenizer** | vocab=59,392, đã chứa âm tiết VN phổ biến (nhưng từ phức tách 2-3 tokens) |
| **Tổng params** | ~1.1B |

```
┌─────────────┐     ┌────────────────┐     ┌─────────────────┐
│  ViT (frozen)│ ──▶ │  Projector     │ ──▶ │  LLM + LoRA     │
│  24 layers   │     │  (unfrozen S1) │     │  16 layers      │
└─────────────┘     └────────────────┘     └─────────────────┘
```

---

## 2. Phương pháp

### 2.1 Tổng quan Pipeline

```
Synthetic Data Generation ──▶ Stage 1: Line-level SFT ──▶ Stage 2: Doc-level SFT ──▶ Merge LoRA ──▶ Deploy
        ↓                            ↓                          ↓
  generate_vietnamese_        Colab T4 GPU              crawl_vi_news.py
  dataset_v3.py               50K samples               10K news samples
```

### 2.2 Sinh dữ liệu Synthetic (Stage 1)

**File:** [generate_vietnamese_dataset_v3.py](file:///c:/project/uit/nlp/GLM-OCR/tools/dataset/generate_vietnamese_dataset_v3.py)

**Từ điển:**
- 35.501 từ tiếng Việt sạch (`vietnamese_words_clean.txt`)
- 3.544 "từ khó" — chứa dấu kép, được lọc thủ công từ 20.378 ứng viên (`vietnamese_hard_words.txt`)
- 677 từ đã loại bỏ (từ mượn Anh/Pháp, viết tắt, thuật ngữ khoa học)

**58 font Windows** đã verify render đúng dấu tiếng Việt, gồm: Arial, Calibri, Cambria, Candara, Consola, Constantia, Courier, Palatino, Segoe UI, Sitka, Tahoma, Times, Verdana (mỗi font có biến thể regular/bold/italic/light/semibold/black).

**7 loại mẫu sinh dữ liệu:**

| # | Generator | Tỷ lệ | Mô tả |
|---|---|---|---|
| 1 | `gen_word_list` | 10% | 8-16 từ ngẫu nhiên |
| 2 | `gen_phrase_list` | 25% | 2-4 cụm từ nối bằng dấu phẩy |
| 3 | `gen_confusion_pair` | 15% | Cặp từ gần giống nhau (edit distance=1), ví dụ "chuồng" vs "chuộng" |
| 4 | `gen_grouped_words` | 10% | Từ cùng nhóm dấu (ă, â, ê, ô, ơ, ư) |
| 5 | `gen_mixed_line` | 15% | Cụm từ + từ trên 2 dòng |
| 6 | `gen_dense_sentence` | 25% | Cụm từ + dấu chấm + từ thêm |
| 7 | `gen_plain_words` | 10% | **Anti-bias:** trộn từ có dấu + không dấu |

**14 loại augmentation** (60% mẫu train, 40% giữ nguyên để học dấu sạch):

| Augmentation | Chi tiết |
|---|---|
| Gaussian Blur | radius 0.3-0.8 |
| Gaussian Noise | intensity 15-35 |
| Contrast Up/Down | 1.1-1.5× / 0.65-0.9× |
| JPEG Compression | quality 55-80 |
| Rotation | ±3° |
| Shadow | Gradient theo 5 hướng |
| Glare | Vùng sáng chói |
| Perspective | Homography 2-7% offset |
| Downscale+Upscale | Scale 0.75-0.92 |
| Wave | Sinusoidal displacement 2-10px |
| Elastic | Random displacement field |
| Motion Blur | Directional kernel 5-12px |
| Defocus | Blur + noise (lấy nét sai) |

**Kết quả Stage 1:** 50.000 train + 100 val + 100 test = **100.390 ảnh** (1.76 GB zip)

### 2.3 Crawler Tin tức (Stage 2)

**File:** [crawl_vi_news.py](file:///c:/project/uit/nlp/GLM-OCR/tools/dataset/crawl_vi_news.py)

- **Nguồn:** 15 RSS feeds từ VNExpress (11 chủ đề), Tuổi Trẻ (4), Thanh Niên (1)
- **Pipeline:** RSS → Article URLs → Extract `<p>` paragraphs → Filter (length > 50 chars, > 60% alphabetic) → Chunk 2-10 dòng
- **Strip diacritics 30%:** Dùng `unicodedata` NFD decomposition → loại dấu thanh trên 30% chunks. **Mục đích:** dạy model KHÔNG tự thêm dấu khi text gốc không có dấu (anti-hallucination).
- **Augmentation nhẹ:** Chỉ blur, noise, jpeg, rotate (không distortion nặng).

**Kết quả Stage 2:** 10.000 train + 50 val + 100 test = **10.100 ảnh** (1.07 GB zip)

### 2.4 Chiến lược Training — Two-Stage Curriculum Learning

**File:** [finetune_glm_ocr_vn_1epoch.ipynb](file:///c:/project/uit/nlp/GLM-OCR/tools/dataset/finetune_glm_ocr_vn_1epoch.ipynb)

#### Stage 1: Line-level SFT (Học dấu cơ bản)

```yaml
LoRA rank: 16, alpha: 32, dropout: 0.1
Target modules: all linear layers (q/k/v/o_proj, gate/up/down_proj, lm_head)
Freeze vision_tower: true
Freeze projector: false     # ← KEY: mở khóa để học dấu VN mới
Learning rate: 1e-4
Scheduler: constant_with_warmup (5% warmup)
Batch: 8 per_device × 8 accum = effective 64
FP16: true (T4)
Cutoff: 2048 tokens
Dataset: 50K synthetic images
```

> **Tại sao unfreeze Projector?** Projector là cầu nối vision→language. Khi đóng băng ViT (giữ khả năng thị giác tốt), mở khóa Projector giúp tạo "từ điển thị giác" mới cho dấu tiếng Việt mà không mất kiến thức pretrain.

#### Stage 2: Document-level SFT (Văn bản thực tế)

```yaml
Load: Stage 1 adapter (optimizer reset)
Cutoff: 4096 tokens
Batch: 2 per_device × 8 accum = effective 16
Learning rate: 5e-5
Dataset: 10K news images
Early stopping: patience=3
Eval: every 200 steps on 50 val samples
```

#### Đặc điểm kỹ thuật Colab

- **GPU:** T4 (16GB VRAM, dùng ~6.9GB)
- **Tốc độ:** ~1.6s/step
- **Auto-resume:** Tự động detect checkpoint trước trên Drive, tính epoch tiếp theo
- **Thời gian ước tính:** ~2h/epoch (Stage 1, 50K samples)

### 2.5 Đánh giá

**File:** [compare_models.py](file:///c:/project/uit/nlp/GLM-OCR/tools/dataset/compare_models.py)

**Metrics:**

| Metric | Mô tả |
|---|---|
| **Word Accuracy** | Exact match theo vị trí |
| **Character Accuracy** | Dựa trên edit distance (Wagner-Fischer DP) |
| **Diacritic Accuracy** | Per-group: ă/ắ/ằ/ẳ/ẵ/ặ, â/ấ/ầ/ẩ/ẫ/ậ, ê, ô, ơ, ư, đ |
| **False Positive Rate** | Tỷ lệ model tự thêm dấu sai (a→ă, e→ê, etc.) |

**Trong notebook (Step 7):** Eval toàn diện sau mỗi epoch — CER, WER, Exact Match%, Diacritic Acc% per group, FP tracking. Lưu history JSON để theo dõi tiến bộ.

### 2.6 Merge & Deploy

**File:** [merge_lora.py](file:///c:/project/uit/nlp/GLM-OCR/tools/dataset/merge_lora.py)

- Load base model + PEFT LoRA adapter → `merge_and_unload()` → lưu safetensors
- Output: **~2.1 GB** model hoàn chỉnh (bfloat16)
- Hỗ trợ deploy qua **Ollama** với Modelfile tự generate

**Kết quả:** 2 models đã merge — `glm-ocr-vn` (Stage 1) và `glm-ocr-vn-s2` (Stage 2)

---

## 3. Công cụ hỗ trợ

### 3.1 Font Tester

**File:** [font_tester_v2.py](file:///c:/project/uit/nlp/GLM-OCR/tools/dataset/font_test/font_tester_v2.py)

Kiểm tra 58 font Windows render đúng các ký tự khó tiếng Việt:
- Dấu kép: ắ ằ ẳ ẵ ặ ấ ầ ẩ ẫ ậ ế ề ể ễ ệ ố ồ ổ ỗ ộ...
- Từ khó: lắm, ngắn, thằn lằn, nhất, mật, triệt, diệt
- Nguyên âm ba: khuyên, quyển, khuỷu, khuyết
- Tên riêng: Huỳnh, Thuỳ, Đặng, Đắk Lắk, Buôn Ma Thuột
- Bảng 167 biến thể nguyên âm đầy đủ

### 3.2 Local Inference

**File:** [test_local.py](file:///c:/project/uit/nlp/GLM-OCR/tools/dataset/test_local.py)

- Nhận 1 ảnh, nhiều ảnh, hoặc cả thư mục
- 3 task: Text / Table / Formula Recognition
- Auto-detect GPU/CPU, ~4GB VRAM
- `max_new_tokens=512`, greedy decoding

### 3.3 Scripts (package.json)

| Script | Lệnh |
|---|---|
| `gen` | Sinh 10K×3=30K samples |
| `gen:big` | Sinh 20K×3=60K samples |
| `gen:clean` | Sinh dataset sạch |
| `test:image` | Test 1 ảnh |
| `test:compare` | So sánh model gốc vs fine-tuned |
| `zip` | Nén dataset |
| `build` | Build cho deploy |

---

## 4. Thiết kế đáng chú ý

### 4.1 Anti-bias Strategy

Hai cơ chế chống bias (model tự thêm dấu sai):

1. **`gen_plain_words` (10% train):** Trộn từ không dấu vào data → model học rằng text không dấu là hợp lệ
2. **30% strip diacritics (Stage 2):** Crawler loại bỏ dấu trên 30% news → reinforce hành vi không thêm dấu

### 4.2 Confusion Pairs

Sinh cặp từ chỉ khác 1 ký tự (edit distance=1) — ví dụ "lặng" vs "lẫm", "hổ" vs "hỗ". Giúp model phân biệt fine-grained giữa các dấu tương tự.

### 4.3 Auto-resume trên Colab

Notebook tự detect checkpoint cuối cùng trên Drive, tính epoch tiếp theo → tránh mất tiến độ khi Colab ngắt kết nối.

### 4.4 meta.json Protocol

Generator ghi `meta.json` với số lượng train/val/test → Notebook đọc chính xác, không hardcode → linh hoạt khi thay đổi dataset.

### 4.5 constant_with_warmup Scheduler

Dùng thay vì cosine schedule vì cho phép **resume training** qua nhiều epoch mà LR không giảm về 0. Warmup 5% giúp ổn định ban đầu.

---

## 5. Kết quả

### 5.1 Datasets đã tạo

| Dataset | Train | Val | Test | Tổng | Dung lượng |
|---|---|---|---|---|---|
| **Stage 1** (synthetic) | 50.000 | 100 | 100 | 100.390 | 1.76 GB |
| **Stage 2** (news) | 10.000 | 50 | 100 | 10.100 | 1.07 GB |

### 5.2 Models đã fine-tune

| Model | Stage | Dung lượng |
|---|---|---|
| `glm-ocr-vn` | Stage 1 (50K synthetic) | ~2.1 GB |
| `glm-ocr-vn-s2` | Stage 2 (10K news, tiếp tục từ S1) | ~2.1 GB |

### 5.3 Hiệu suất training

- **VRAM:** ~6.9/16 GB trên T4
- **Tốc độ:** ~1.6s/step
- **Early stopping:** patience=3 trên cả 2 stages
- **FP16** training trên T4

---

## 6. Kết luận

Dự án đã xây dựng thành công **pipeline fine-tune GLM-OCR cho tiếng Việt** hoàn chỉnh, bao gồm:

1. ✅ **Hệ thống sinh dữ liệu synthetic** với 14 loại augmentation, 58 font, 7 mẫu đa dạng
2. ✅ **Crawler tin tức** từ 15 nguồn VN để tạo dữ liệu thực tế (Stage 2)
3. ✅ **Two-stage curriculum learning**: synthetic → real news, phù hợp best practices của VARY/TrOCR
4. ✅ **Anti-bias design**: Ngăn model hallucinate dấu tiếng Việt
5. ✅ **Đánh giá chi tiết**: CER, WER, diacritic accuracy per group, False Positive tracking
6. ✅ **Tooling hoàn chỉnh**: Font tester, local inference, model comparison, Ollama deploy
7. ✅ **Colab-friendly**: Auto-resume, auto-save Drive, tối ưu T4

---

## 7. Cấu trúc dự án

```
tools/dataset/
├── finetune_glm_ocr_vn_1epoch.ipynb   # Training notebook (8 steps)
├── generate_vietnamese_dataset_v3.py   # Synthetic data generator
├── crawl_vi_news.py                    # News crawler (Stage 2)
├── compare_models.py                   # Evaluation script
├── test_local.py                       # Local inference
├── merge_lora.py                       # LoRA merger
├── package.json                        # npm scripts
├── GUIDE.md                            # Documentation (545 lines)
├── README.md                           # Quick reference
├── .gitignore
├── dictionary/
│   ├── vietnamese_words.txt            # 36.534 từ gốc
│   ├── vietnamese_words_clean.txt      # 35.501 từ đã clean
│   ├── vietnamese_hard_words.txt       # 3.544 từ khó (dấu kép)
│   ├── removed_words.txt               # 677 từ đã loại
│   └── filter_vietnamese.py            # Script lọc từ khó
├── font_test/
│   └── font_tester_v2.py               # Font validation
├── vietnamese_ocr/                     # Stage 1 dataset (100K ảnh)
├── vietnamese_ocr_s2/                  # Stage 2 dataset (10K ảnh)
├── glm-ocr-vn/                         # Merged model Stage 1
└── glm-ocr-vn-s2/                      # Merged model Stage 2
```
