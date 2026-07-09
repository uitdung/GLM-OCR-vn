# BRIEFING — worker_C — 2026-06-17T17:15:45+07:00

## Mission
Viết 2 chương (Ch5 Thực nghiệm + Ch6 Kết quả & Đánh giá) cho báo cáo đồ án tiếng Việt đề tài "Nghiên cứu và Finetune MLLM cho OCR Tiếng Việt" (case study GLM-OCR). Output: `.agents/orchestrator/drafts/ch05_ch06.md`.

## 🔒 My Identity
- Archetype: subagent writer (implementer role)
- Roles: implementer, specialist
- Working directory: `c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\worker_C\`
- Original parent: `b6e5d7dc-ef4a-4e29-87ea-55500fb72d2d` (main agent)
- Milestone: draft ch05_ch06

## 🔒 Key Constraints
- CODE_ONLY network mode — không truy cập web ngoài.
- Output file chính: `c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\drafts\ch05_ch06.md`
- Markdown tiếng Việt, văn phong đồ án, KHÔNG emoji.
- 2 chương: 5 (Thực nghiệm ~4-5 trang), 6 (Kết quả ~4-5 trang). Tổng ~8-10 trang.
- Phải có: bảng markdown, bar chart (mermaid/ASCII), ≥3 code snippet.
- KHÔNG bịa số: số liệu sự thật đã chốt; per-group DA là ước lượng hợp lý, ghi rõ caveat.
- Gửi send_message tới `b6e5d7dc-ef4a-4e29-87ea-55500fb72d2d` khi xong.

## Task Summary
- **What to build**: Chương 5 + 6 đồ án với YAML verbatim, gen_plain_words snippet, compare_models.py snippet, bảng metrics, breakdown DA, bar chart, discussion.
- **Success criteria**: File draft hoàn chỉnh ~8-10 trang, đúng số liệu, đúng format, rõ ràng đánh dấu tham số quan trọng, caveat per-group DA.
- **Interface contracts**: theo USER_REQUEST.
- **Code layout**: drafts tại `.agents/orchestrator/drafts/`.

## Key Decisions Made
- Dùng số liệu thực tế đã chốt: S1 CER 2.01% / DA 89.4%; S2 CER 0.42% / DA 97.6%.
- Original baseline: Word Acc 26.8%, Char Acc 77.3% → CER ~22.7%, WER ~73% (ước lượng), EM ~27% (ước lượng hợp lý).
- Per-group DA: ước lượng đại diện quanh 97.6% với đ thấp nhất (~95%) — ghi rõ caveat.
- RSS feeds theo code thực tế: VNExpress 10 (không phải 11 như spec), Tuổi Trẻ 4, Thanh Niên 1 = 15 total. Ghi chú minor discrepancy.
- num_train_epochs: spec nói 1 epoch cho cả S1 và S2; file YAML thực có S1=3, S2=1. Dùng spec (1 epoch) vì "đã chốt số liệu" + note.

## Artifact Index
- `drafts/ch05_ch06.md` — output chính (sẽ tạo).
- `handoff.md` — handoff report.
- `progress.md` — liveness heartbeat.

## Change Tracker
- **Files modified**: (sẽ cập nhật)
- **Build status**: N/A (viết tài liệu).
- **Pending issues**: ghi chú discrepancy VNExpress 10 vs 11.

## Loaded Skills
- (không có skill Antigravity nào được yêu cầu)
