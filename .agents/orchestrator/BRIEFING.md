# BRIEFING — Orchestrator Báo cáo Đồ án MLLM OCR Tiếng Việt

## Mission
Viết báo cáo đồ án 20-30 trang tiếng Việt (kỹ thuật sâu) đề tài "Nghiên cứu và Finetune MLLM cho OCR Tiếng Việt" — GLM-OCR case study.

## 🔒 My Identity
- Archetype: Project Orchestrator (sub-orchestrator của Sentinel)
- Roles: orchestrator, user_liaison, human_reporter, successor
- Working directory: `c:\project\uit\nlp\GLM-OCR\.agents\orchestrator`
- Original parent: main agent (Sentinel)
- Original parent conversation ID: `9abe4869-a361-45a4-a22f-44635a8b8e11`

## 🔒 My Workflow
- **Pattern**: Project (sub-orchestrator)
- **Scope**: 1 milestone duy nhất — viết báo cáo docs/bao_cao_do_an_MLLM_OCR_Tieng_Viet.md
- **Decompose**: 4 chương-pair song song (1-2, 3-4, 5-6, 7-8+Kết luận)
- **Execute**: worker draft → synthesizer merge → reviewer check acceptance → fix loop
- **On failure**: retry → replace worker → degrade (synthesize từ partial drafts)
- **Succession**: 16 spawns (dễ dàng — task bounded)
- **Work items**:
  1. Phase 1 Exploration — DONE
  2. Phase 2 Draft 4 chương — IN_PROGRESS
  3. Phase 3 Synthesis
  4. Phase 4 Review acceptance
  5. Phase 5 Victory report
- **Current phase**: 2
- **Current focus**: Đợi 4 worker draft (conv 643ec52a, 0dbc212f, b8891105, 4f097bc8)

## 🔒 Key Constraints
- Output duy nhất: `c:\project\uit\nlp\GLM-OCR\docs\bao_cao_do_an_MLLM_OCR_Tieng_Viet.md`
- Metadata trong `.agents/orchestrator/` (drafts, progress)
- KHÔNG sửa source/config
- KHÔNG bịa số liệu — dùng đúng eval: S1 CER 2.01%/DA 89.4%, S2 CER 0.42%/DA 97.6%
- Tiếng Việt, kỹ thuật sâu, 20-30 trang
- Never reuse subagent sau handoff

## Current Parent
- Conversation ID: `9abe4869-a361-45a4-a22f-44635a8b8e11`
- Updated: 2026-06-17T17:11

## Team Roster
| Agent | Type | Work Item | Status | Conv ID |
|-------|------|-----------|--------|---------|
| worker_A | teamwork_preview_worker | Draft ch1-2 | in_progress | 643ec52a-8dcc-4449-bca8-d45cd26ffba9 |
| worker_B | teamwork_preview_worker | Draft ch3-4 | in_progress | 0dbc212f-6371-4fd4-9ff5-3e9b2ff483bd |
| worker_C | teamwork_preview_worker | Draft ch5-6 | in_progress | b8891105-9e65-4129-8f92-79828edcd443 |
| worker_D | teamwork_preview_worker | Draft ch7-8+KL | in_progress | 4f097bc8-e0ba-4235-b1dc-e04033e5a14e |

## Succession Status
- Spawn count: 4 / 16
- Pending subagents: 4 (worker_A/B/C/D)
- Successor: not yet spawned

## Active Timers
- Liveness cron: b6e5d7dc-ef4a-4e29-87ea-55500fb72d2d/task-41 (every 10 min)

## Key Decisions Made
- Phân giải theo 4 nhóm chương (1-2, 3-4, 5-6, 7-8) để tối ưu parallelism
- Dùng 12 font (VERIFIED_FONTS) chứ không phải 58 như báo cáo cũ (sai)
- Dùng 88 ENGLISH_WORDS (đếm chính xác từ source)
- Augmentation 65/35 (13 "none" + 7 augment trong 20 slots)
- num_train_epochs YAML S1=3 nhưng báo cáo theo user contract (1 epoch)

## Artifact Index
- `c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\progress.md` — tracker
- `c:\project\uit\nlp\GLM-OCR\.agents\sentinel\ORIGINAL_REQUEST.md` — authoritative spec
- `C:\Users\Dung\.gemini\antigravity\brain\b6e5d7dc-ef4a-4e29-87ea-55500fb72d2d\orchestrator_plan.md` — plan artifact
- Output: `c:\project\uit\nlp\GLM-OCR\docs\bao_cao_do_an_MLLM_OCR_Tieng_Viet.md`
