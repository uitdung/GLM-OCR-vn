# BRIEFING — worker_synthesizer_v2

## Mission
Ghép 4 draft chapters + apply 6 fixes + thêm front matter + bibliography thành BÁO CÁO FINAL cho đồ án MLLM OCR tiếng Việt.

## 🔒 My Identity
- Archetype: Synthesizer worker
- Roles: implementer, qa, specialist
- Working directory: c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\worker_synthesizer_v2\
- Original parent: b6e5d7dc-ef4a-4e29-87ea-55500fb72d2d (main agent)
- Milestone: Final report synthesis

## 🔒 Key Constraints
- Output file: c:\project\uit\nlp\GLM-OCR\docs\bao_cao_do_an_MLLM_OCR_Tieng_Viet.md
- DÙNG PowerShell (Set-Content / Add-Content) — KHÔNG write_to_file cho file lớn (120KB+)
- PowerShell 5.1 syntax, KHÔNG dùng `&&`
- UTF-8 encoding cho tiếng Việt
- 6 fixes exact line numbers (verified upstream)
- KHÔNG sửa S2 YAML `num_train_epochs: 1` (ch03:275, ch05:240) — ĐÚNG

## Task Summary
- **What to build**: Final report file ~120-150KB bằng concat 4 drafts + header + bibliography + 6 fixes
- **Success criteria**: 20-30 trang, 8 chương + Tóm tắt + Kết luận, mục lục, tiếng Việt chuẩn, số liệu chính xác
- **Interface contracts**: 4 drafts ở `.agents/orchestrator/drafts/`
- **Code layout**: Output ở `docs/bao_cao_do_an_MLLM_OCR_Tieng_Viet.md`

## Key Decisions Made
- Strategy: 4 bước PowerShell (header → concat+fixes → bibliography → verify)
- Dùng `-Raw` để regex replace chính xác
- Regex escape khi replace blocks có ký tự đặc biệt

## 6 Fixes (to apply)
1. ch01_ch02.md:61 — "trong văn liệu" → "trong tài liệu"
2. ch03_ch04.md:247 — S1 YAML `num_train_epochs: 1` → `3`
3. ch03_ch04.md:221 — "11 ... VNExpress" → "10 ... VNExpress"
4. ch05_ch06.md:186 — S1 YAML `num_train_epochs: 1` → `3` (Stage 1 block only)
5. ch05_ch06.md:22 — "8-9 giờ" Stage 1 → "~25 phút"
6. ch05_ch06.md:126 — "khoảng 8-9 giờ" Stage 1 → "~25 phút"

## Artifact Index
- progress.md — liveness heartbeat
- handoff.md — final handoff report
