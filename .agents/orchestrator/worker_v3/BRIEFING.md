# BRIEFING — worker_v3 (EMERGENCY synthesizer)

## Mission
Atomic-write final synthesized report `docs/bao_cao_do_an_MLLM_OCR_Tieng_Viet.md` from 5 drafts, apply 7 fixes, normalize ch5/6/7/8 headers, verify >1200 lines.

## 🔒 My Identity
- Archetype: EMERGENCY synthesis worker (v3 — after 2 race-condition failures)
- Roles: implementer, qa, specialist
- Working directory: `c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\worker_v3\`
- Original parent: orchestrator `e15cadc9-5852-4138-b4fa-05b9d02e8e95`
- Milestone: ATOMIC_SYNTH

## 🔒 Key Constraints
- CODE_ONLY network mode
- PowerShell 5.1 only (no `&&`, no `?:`, no `?` alias)
- ATOMIC WRITE strategy: temp + Move-Item -Force
- DO NOT CHEAT: use real eval facts only
- Vietnamese UTF-8 encoding must be preserved

## Current Parent
- Conversation ID: `e15cadc9-5852-4138-b4fa-05b9d02e8e95`
- Updated: 2026-06-18T09:48+07:00

## Task Summary
- **What to build**: Final report (~120KB / ~1300 lines)
- **Success criteria**: file exists, >110KB, >1200 lines, 8 chapter headers, ## Kết luận, 7 fixes applied
- **Code layout**: drafts at `.agents/orchestrator/drafts/`, output at `docs/bao_cao_do_an_MLLM_OCR_Tieng_Viet.md`

## Key Eval Facts
- S1 YAML: `num_train_epochs: 3` (target), currently `1` in draft. Cutoff 2048, LR 1.0e-4
- S2 YAML: `num_train_epochs: 1` (KEEP), adapter_name_or_path, cutoff 4096
- S1 CER 2.01%/DA 89.4%; S2 CER 0.42%/DA 97.6%
- Dataset: 12 fonts, 88 EN words, 15 RSS (10 VNExpress + 4 Tuổi Trẻ + 1 Thanh Niên)
- Augmentation 65/35; S1 timing ~25 phút (3 epoch × 312 steps × 1.6s)

## 7 Fixes
1. `trong văn liệu` → `trong tài liệu`
2. S1 YAML `num_train_epochs: 1` → `3` (distinguish S1 vs S2 by cutoff/LR/adapter)
3. `11 nguồn VNExpress` → `10 nguồn VNExpress`
4. ch05 Stage 1 '1 epoch' → '3 epoch' + step math (20000/64=312 × 3 = 936)
5. `8-9 giờ`/`8 đến 9 giờ`/`8–9 giờ` → `~25 phút` (+ math)
6. Verify no other 'Stage 1: 1 epoch'
7. S2 YAML `num_train_epochs: 1` KEEP

## Header normalization (post-concat)
- `# Chương 5. Thực nghiệm` → `## 5. Thực nghiệm`
- `# Chương 6. Kết quả và Đánh giá` → `## 6. Kết quả và Đánh giá`
- If ch7/ch8 use `# Chương N`, normalize → `## N.`

## Change Tracker
- **Files modified**: (pending) `docs/bao_cao_do_an_MLLM_OCR_Tieng_Viet.md`
- **Build status**: pending
- **Pending issues**: none yet

## Artifact Index
- `progress.md` — liveness heartbeat
- `handoff.md` — final handoff (to write)
