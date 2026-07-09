# Original User Request

## Initial Request — 2026-06-17T17:05:25+07:00

Viết báo cáo đồ án môn học đầy đủ (20-30 trang, tiếng Việt, kỹ thuật sâu) cho đề tài "Nghiên cứu và Finetune MLLM cho OCR Tiếng Việt" — case study GLM-OCR. Bao gồm: kiến trúc MLLM/OCR, phương pháp finetune LoRA 2-stage với rsLoRA, thiết kế dataset synthetic chống hallucination, benchmark đánh giá diacritic accuracy, và phân tích kết quả thực tế.

Working directory: c:\project\uit\nlp\GLM-OCR
Integrity mode: development

## Reference Material

- Source code: `c:\project\uit\nlp\GLM-OCR\tools\dataset\` (dataset generation scripts)
- Training configs: `examples/finetune/glm_ocr_vn_s1_rslora.yaml`, `glm_ocr_vn_s2_rslora.yaml`
- Eval results: Stage 1 (CER 2.01%, DA 89.4%), Stage 2 (CER 0.42%, DA 97.6%)
- Real-world test: DA drops significantly due to frozen vision tower (tone confusion)
- Previous artifacts: `GLM_OCR_Comprehensive_Research.md`, `De_xuat_toi_uu_training.md`, `training_v2_guide.md`

## Requirements

### R1. Cấu trúc báo cáo đầy đủ theo chuẩn đồ án UIT

Báo cáo cần có cấu trúc: Tóm tắt → Giới thiệu → Tổng quan nghiên cứu (MLLM cho OCR, GLM-OCR, PP-OCRv6) → Phương pháp đề xuất (2-stage LoRA, rsLoRA, dataset design) → Thực nghiệm (setup, dataset, training) → Kết quả & Đánh giá (benchmark metrics: CER, WER, DA, FP rate; so sánh Stage 1 vs 2) → Phân tích hạn chế (frozen vision tower → tone confusion) → Demo → Kết luận & Hướng phát triển. Mỗi chương 3-5 trang.

### R2. Nội dung kỹ thuật sâu

Trình bày chi tiết: (1) Kiến trúc GLM-OCR (vision encoder + projector + LLM decoder), số params, tokenizer; (2) LoRA/rsLoRA math (rank decomposition, scaling factor √α/r); (3) Dataset v3 design: 12 fonts, anti-hallucination (88 English words, 20% confusion pairs, plain_words), augmentation 65/35; (4) Stage 1: word-level diacritic training, 20K samples, 1 epoch; (5) Stage 2: document-level, 11.5K crawled news, 1 epoch. Include code snippets quan trọng: YAML config, eval script, dataset generation logic.

### R3. Phần đánh giá thực nghiệm với bảng biểu và phân tích

Bảng so sánh metrics Stage 1 vs Stage 2 (CER, WER, EM, DA per-group: ă/â/ê/ô/ơ/ư/đ, FP rate). Bar chart mô tả diacritic accuracy theo từng nhóm dấu. Phân tích nguyên nhân gap giữa benchmark (DA 97.6%) và thực tế (tone confusion). Đề xuất giải pháp: unfreeze vision tower, LR scheduling cho vision vs text.

### R4. Phần Demo cuối bài

Mô tả pipeline demo: upload ảnh → OCR → hiển thị kết quả. Trích kết quả OCR thực tế trên ảnh báo chí tiếng Việt. So sánh before (base GLM-OCR) vs after (finetuned). Note các lỗi còn tồn tại.

## Acceptance Criteria

### Cấu trúc & độ dài
- [ ] Báo cáo dài 20-30 trang (không tính appendix)
- [ ] Có đầy đủ 8 chương như R1
- [ ] Có mục lục, danh sách hình vẽ/bảng biểu
- [ ] Mỗi chương có 3-5 trang nội dung thực chất

### Nội dung kỹ thuật
- [ ] Có giải thích toán học về LoRA và rsLoRA (có công thức)
- [ ] Có code snippet: YAML config, eval script, dataset gen logic (ít nhất 5 snippet)
- [ ] Có diagram kiến trúc GLM-OCR (mermaid hoặc text description)
- [ ] Có phân tích chi tiết dataset v3 design (font selection, anti-hallucination, augmentation ratio)

### Đánh giá thực nghiệm
- [ ] Có bảng so sánh Stage 1 vs Stage 2 với tất cả metrics
- [ ] Có breakdown DA theo từng nhóm dấu (ă/â/ê/ô/ơ/ư/đ)
- [ ] Có phân tích gap benchmark vs thực tế (root cause: frozen vision)
- [ ] Có đề xuất hướng cải thiện cụ thể

### Demo
- [ ] Mô tả pipeline demo với code
- [ ] Trích ví dụ OCR thực tế (before/after)

Lưu báo cáo vào file `c:\project\uit\nlp\GLM-OCR\docs\bao_cao_do_an_MLLM_OCR_Tieng_Viet.md`
