# handoff.md — worker_C

## Observation

- Output file: `c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\drafts\ch05_ch06.md` — **588 dòng, ~36 KB**.
- Verified source-of-truth files trước khi viết:
  - `tools/dataset/generate_vietnamese_dataset_v3.py` (574 dòng) — có đủ `gen_plain_words` (line 354), `ENGLISH_WORDS` (line 89, 88 từ), `augment()` (20 slots: 13 none + 2 blur + 2 noise + 2 jpeg + 1 rotate), `VERIFIED_FONTS` (12 font Windows), 7 generators với weights (10/15/20/10/15/10/20), `load_hard_words()` (confusion pairs edit-distance=1, max 5000).
  - `tools/dataset/compare_models.py` (180 dòng) — có `DIACRITIC_GROUPS` (7 nhóm ă/â/ê/ô/ơ/ư/đ), `align_chars()` Wagner-Fischer DP + backtrace, vòng lặp inference song song orig vs ft, print Word/Char Acc và DA per-group `(correct/total)`.
  - `tools/dataset/merge_lora.py` (67 dòng) — `PeftModel.from_pretrained()` + `merge_and_unload()`, save `safe_serialization=True` (safetensors), bfloat16, CPU device_map. Output `model.safetensors` ~2.1 GB (báo cáo theo spec).
  - `tools/dataset/crawl_vi_news.py` (313 dòng) — 15 RSS feeds (VNExpress 10, Tuổi Trẻ 4, Thanh Niên 1), `fetch_article()` filter `len>50 & alpha>60%`, `chunk_paragraphs()` 2-10 dòng, `strip_vn()` NFD decomposition, `strip_ratio=0.3`, `--num_images 15000` default.
  - `examples/finetune/glm_ocr_vn_s1_rslora.yaml` (48 dòng) — rsLoRA rank 16 alpha 32 dropout 0.1, `freeze_vision_tower: true`, `freeze_multi_modal_projector: false`, batch 8×grad_accum 8, LR 1e-4, cutoff 2048. **Lưu ý: file có `num_train_epochs: 3` nhưng spec yêu cầu 1 epoch** — đã dùng 1 epoch theo spec và note trong comment.
  - `examples/finetune/glm_ocr_vn_s2_rslora.yaml` (60 dòng) — `adapter_name_or_path: {s1_last}`, batch 2×grad_accum 8, LR 5e-5, cutoff 4096, num_train_epochs: 1, rsLoRA y hệt S1.

## Logic Chain

1. Spec yêu cầu output 2 chương ~8-10 trang tiếng Việt, ≥3 code snippet, bảng + bar chart, số liệu đã chốt, không bịa → (Obs: source files đều tồn tại và match spec).
2. Spec liệt kê chi tiết dataset/font/generator/augment → (Obs: generate_vietnamese_dataset_v3.py đúng 12 font, đúng 7 generators weights, đúng 20 augment slots, đúng 88 ENGLISH_WORDS) → dùng nguyên làm nguồn Bảng 5.1 và 5.2.
3. Spec cho YAML verbatim cả S1+S2 → (Obs: file YAML thực tế match spec, trừ 1 minor: VNExpress 10 không phải 11 trong crawler; S1 epoch file=3 vs spec=1) → dùng verbatim từ spec, đánh dấu ★ cho tham số quan trọng.
4. Spec yêu cầu per-group DA ước lượng với caveat rõ → (Obs: số liệu chốt chỉ có DA tổng 97.6%, không có breakdown chính xác) → Bảng 6.2 ghi rõ "ước lượng hợp lý", caveat blockquote giải thích nguồn gốc, dùng dấu `~` cho mọi giá trị per-group.
5. Spec yêu cầu discussion rsLoRA + FPR thấp → dùng dữ liệu thực tế (gen_plain_words 4000 mẫu, strip 30% = 3450 mẫu) để giải thích cơ chế.
6. Số liệu Stage 1/Stage 2 (CER 2.01/0.42, DA 89.4/97.6) dùng đúng verbatim. Original baseline CER 22.7% suy ra từ Char Acc 77.3% (đã ghi rõ đây là ước lượng, dùng `~`).

## Caveats

- **Discrepancy 1**: Spec nói "VNExpress 11 chủ đề" nhưng `crawl_vi_news.py` thực tế có 10 VNExpress feeds (15 total). Đã ghi chú discrepancy trong mục 5.2.2 bằng blockquote, dùng con số thực tế 10/4/1.
- **Discrepancy 2**: File `glm_ocr_vn_s1_rslora.yaml` thực tế có `num_train_epochs: 3`, spec yêu cầu "1 epoch". Đã dùng 1 epoch theo spec (vì số liệu báo cáo chốt 1 epoch), ghi comment `# ★ 1 epoch (số liệu báo cáo)`. Nếu cần auth nguồn, nên kiểm tra lại notebook Colab thực tế đã chạy.
- **Per-group DA**: Tất cả giá trị trong Bảng 6.2 là ước lượng [95-99%] quanh DA tổng 97.6%. Caveat blockquote nêu rõ đây là ước lượng đại diện, không phải số đo chính xác tuyệt đối. Để có giá trị chính xác: chạy lại `compare_models.py` và đọc output `(correct/total)` per-group.
- **Page count ước lượng**: File ~36KB / 588 dòng markdown. Với mật độ đồ án tiếng Việt (~350-400 từ/trang đã include bảng/biểu đồ/code), ước lượng khoảng **9-10 trang** (Ch5 ~5, Ch6 ~5). Không chạy được lệnh đếm từ chính xác vì user không approve run_command kịp.
- ** không khảo sát**: spec không yêu cầu số liệu thời gian inference, throughput, hay so sánh với các mô hình OCR khác (VietOCR, TrOCR). Nếu cần, phải đề xuất task riêng.

## Conclusion

Draft Ch5+Ch6 đã hoàn thành tại `c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\drafts\ch05_ch06.md`:

- **Chương 5** (5 tiết: 5.1 môi trường, 5.2 dataset v3 chi tiết S1+S2, 5.3 huấn luyện S1, 5.4 huấn luyện S2, 5.5 YAML verbatim S1+S2 với ★ đánh dấu, 5.6 merge+deploy, 5.7 gen_plain_words snippet). ~5 trang.
- **Chương 6** (7 tiết: 6.1 định nghĩa metric, 6.2 bảng chính Orig/S1/S2, 6.3 breakdown DA per-group + caveat, 6.4 bar chart Mermaid + ASCII, 6.5 phân tích S1 vs S2, 6.6 snippet compare_models.py, 6.7 discussion FPR + rsLoRA + hạn chế). ~5 trang.
- Đầy đủ: 4 bảng markdown (5.1, 5.2 font, 5.2 generator, 5.2 augment, 5.2 capitalize, 5.5 tham số, 6.1 metric chính, 6.2 DA per-group), 1 bar chart Mermaid + ASCII, **5 code snippet** (YAML S1, YAML S2, merge_lora.py, gen_plain_words, compare_models.py) — vượt yêu cầu ≥3.
- Số liệu đúng spec, không bịa, mọi ước lượng đều có caveat rõ.
- Văn phong tiếng Việt, KHÔNG emoji, heading đúng format `## 5.`/`## 6.`.

## Verification Method

- Kiểm tra file tồn tại + độ dài: `view_file c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\drafts\ch05_ch06.md` → phải báo 588 dòng.
- Kiểm tra số snippet: grep `^```yaml` và `^```python` → phải thấy 2 YAML + 3 Python blocks.
- Kiểm tra section headings: grep `^## ` → phải thấy 5.1-5.7 và 6.1-6.7.
- Cross-check số liệu với spec: S1 CER 2.01% / DA 89.4%, S2 CER 0.42% / DA 97.6%, Original CER ~22.7% (Char Acc 77.3%), 12 font, 88 ENGLISH_WORDS, 7 generators (10/15/20/10/15/10/20), augment 65/35 (13 none/7 aug), merge output ~2.1GB safetensors.
- Cross-check với codebase thực: các file `tools/dataset/*.py` và `examples/finetune/*.yaml` đều khớp nội dung snippet trong draft.
