- ch01_ch02.md: 80 lines, title at top (stripped at concat)
- ch03_ch04.md: 356 lines, §3 + §4
- ch05_ch06.md: 588 lines, h1 Chương 5/6
- ch07_ch08_conclusion.md: 262 lines, §7 + §8 + Kết luận
- Fixes mapped: Sửa 1 (§2.4 list), Sửa 2 (epochs + 8-9h→25m), Sửa 3 (VNExpress 11→10), Sửa 4 (typo văn liệu), Sửa 5 (terminology)

## 2026-06-18T09:31Z — Step 1 DONE
- Wrote `c:\project\uit\nlp\GLM-OCR\docs\bao_cao_do_an_MLLM_OCR_Tieng_Viet.md` header + TOC + ch01-02
- Applied Sửa 1 (§2.4 list rewritten per USER_REQUEST chapter names)
- Applied Sửa 4 (typo "trong văn liệu" → "trong các tài liệu tham khảo")
- Applied Sửa 5 partial: "Tiếng Việt" → "tiếng Việt" in title only (rest of ch01-02 was already lowercase)
- Next: Step 2 append ch03-04 with Sửa 2, 3, 5

## 2026-06-18T09:31Z — Tool issue
- run_command timed out twice waiting for user permission. User not approving commands.
- Switching strategy: build entire file via write_to_file + replace_file_content (chunked edits). Avoid run_command.


## 2026-06-18T09:18Z — Start
- Read all 4 drafts (19008 + 31760 + 36096 + 30650 = 117514 bytes raw)
- Created BRIEFING.md
- Plan: write build_report.ps1 script to concat + apply 5 fixes, execute, verify

## 2026-06-18T09:20Z — Drafts analyzed
- ch01_ch02.md: 80 lines, title at top (will strip when concat)
- ch03_ch04.md: 356 lines, §3 Tổng quan nghiên cứu + §4 Phương pháp đề xuất
- ch05_ch06.md: 588 lines, h1 "# Chương 5/6" headings (will keep)
- ch07_ch08_conclusion.md: 262 lines, §7 + §8 + Kết luận
- Fixes mapped: Sửa 1 (§2.4 list in ch01), Sửa 2 (epochs in ch03/ch05), Sửa 3 (VNExpress 11→10 in ch03), Sửa 4 (typo in ch01), Sửa 5 (terminology global)
