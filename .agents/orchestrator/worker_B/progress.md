# worker_B progress — Finetune GLM-OCR tiếng Việt (Ch3+Ch4 draft)

**Last visited:** 2026-06-17T10:29:00+07:00
**Status:** DONE — draft delivered.

## Task
Viết 2 chương giữa (Chương 3: Tổng quan nghiên cứu, Chương 4: Phương pháp đề xuất) cho báo cáo đồ án tiếng Việt về đề tài finetune GLM-OCR cho OCR tiếng Việt.

## Output
- File: `c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\drafts\ch03_ch04.md`
- Kích thước: ~31 KB, 356 dòng.

## Cấu trúc chương trình
### Chương 3 (~4 trang ước lượng)
- 3.1 MLLM cho OCR: timeline evolution + 2 bảng so sánh (Bảng 3.1 tiến hóa 2017-2026, Bảng 3.2 ba nhóm kiến trúc)
- 3.2 GLM-OCR chi tiết: 3 module (CogViT + Projector + GLM-0.5B) + diagram Mermaid flowchart LR + MTP loss mention
- 3.3 PP-OCRv6 vs GLM-OCR: bảng so sánh 7 tiêu chí
- 3.4 OCR tiếng Việt hiện trạng: PP-OCR, VietOCR, vietocr toolkit + 3 hạn chế

### Chương 4 (~5 trang ước lượng)
- 4.1 Pipeline 2-stage: diagram Mermaid flowchart TB
- 4.2 LoRA math: công thức block $W = W_0 + BA$, forward $h = W_0 x + \frac{\alpha}{r}BAx$, ví dụ số 48x tiết kiệm
- 4.3 rsLoRA math: công thức $\sqrt{\alpha/r}$, giải thích ổn định gradient
- 4.4 Lý do freeze ViT + unfreeze projector: catastrophic forgetting + chi phí tính toán
- 4.5 Dataset v3 anti-hallucination: 12 font, 7 generators bảng weights, 88 ENGLISH_WORDS, 20-slot augmentation bảng, 6 diacritic groups, dedup + random capitalize, Stage 2 crawler 15 RSS + strip 30%
- 4.6 YAML verbatim Stage 1 + Stage 2
- 4.7 Python snippet: `gen_plain_words` + `augment`

## Verification checklist
- [x] Diagram Mermaid: 2 (kiến trúc GLM-OCR + pipeline 2-stage)
- [x] Bảng so sánh: 4 (3.1, 3.2, 3.3, augmentation slot)
- [x] Công thức toán inline $...$: nhiều (LoRA, rsLoRA, ví dụ)
- [x] Công thức block $$...$$: 3 cặp (rank decomp, forward LoRA, forward rsLoRA)
- [x] Code YAML: 2 (Stage 1 + Stage 2 verbatim)
- [x] Code Python: 2 (gen_plain_words + augment)
- [x] Không emoji
- [x] Văn phong hàn lâm tiếng Việt
- [x] Số liệu sự thật: 1.1B params, CogViT 24L h=1024 image=336 patch=14 spatial_merge=2 temporal_patch=2 out_hidden=1536, LLM 16L h=1536 GQA 16/8 head_dim=128 vocab=59392 max_pos=131072 SiLU RoPE theta=10000 mRoPE=[16,24,24], 999 tokens, S1 CER 2.01% DA 89.4%, S2 CER 0.42% DA 97.6%, Stage 1 20K samples, Stage 2 11.5K samples
- [x] Sửa 2 typo: "quên mài" → "catastrophic forgetting"; "Catostrothic" → "Catastrophic"

## Ước lượng số trang
- Tổng ~31 KB markdown ≈ 9 trang A4 (350 từ/trang) — chia Ch3 ~4 trang, Ch4 ~5 trang. Đạt yêu cầu ~8-10 trang.

## Reference images (đã verify tồn tại)
- `vlm_ocr_evolution.png` (515 KB)
- `glm_ocr_architecture.png` (490 KB)
- `finetune_pipeline.png` (555 KB)
