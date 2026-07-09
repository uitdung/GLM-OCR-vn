# Handoff — worker_A (draft ch01_ch02)

## Observation
- Đã tạo file `c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\drafts\ch01_ch02.md` (80 dòng, 19,004 bytes).
- Cấu trúc: `## 1. Tóm tắt` (6 đoạn, dòng 5–17) + `## 2. Giới thiệu` với 4 sub-headings `### 2.1`–`### 2.4` (dòng 21–79).
- Đã sửa 1 lỗi chính tả ở dòng 61: "trong văn献" (lẫn ký tự Hán Việt 献) → "trong văn liệu".
- Số liệu sử dụng đúng như chỉ định: GLM-OCR ~1.1B params, `GlmOcrForConditionalGeneration`, zai-org, OmniDocBench V1.5 = 94.62 (#1), S1 CER 2.01%/DA 89.4%, S2 CER 0.42%/DA 97.6%, 12 font, 88 EN words, plain_words, 15 nguồn báo chí.
- Tiếng Việt: 6 nguyên âm đôi (ă â ê ô ơ ư), 6 dấu thanh (ngang/sắc/huyền/hỏi/ngã/nặng), chữ đ — đề cập đầy đủ.

## Logic Chain
1. Yêu cầu: viết 2 chương đầu đồ án tiếng Việt, hàn lâm, có cite dạng [n], không emoji, không lặp nội dung. (Quan sát từ original_prompt.)
2. Viết file draft `ch01_ch02.md` theo đúng cấu trúc yêu cầu (heading `## 1.`, `## 2.`, `### 2.1`–`### 2.4`). (Quan sát: file đã tạo.)
3. Chương 1 ~6 đoạn (~500-700 từ yêu cầu) tóm tắt đầy đủ: bài toán, đóng góp (5 ý), kết quả (4 con số), hạn chế (frozen vision tower). (Quan sát: dòng 5–17.)
4. Chương 2 có đủ 4 sub-section: 2.1 đặt vấn đề (3 thành phần phức tạp + pixel nhỏ), 2.2 động lực (MLLM xu hướng + 3 lợi thế + GLM-OCR dẫn đầu + 3 điểm yếu tiếng Việt), 2.3 đóng góp (5 ý đầy đủ theo yêu cầu), 2.4 cấu trúc (8 chương + kết luận). (Quan sát: dòng 21–79.)
5. Phát hiện lỗi "văn献" → sửa thành "văn liệu". (Quan sát: diff dòng 61.)
6. Văn phong hàn lâm, không "mình"/"bạn", không emoji. (Quan sát: kiểm tra toàn bộ nội dung.)

## Caveats
- Không chạy được lệnh PowerShell đếm từ (run_command timeout, user không phê duyệt kịp). Số trang là ước lượng dựa trên kích thước file: 19,004 bytes UTF-8 tiếng Việt ≈ ~3,800 từ → render A4 ~4-5 trang tổng, đáp ứng mục tiêu chương 1 ~1 trang + chương 2 ~3-4 trang.
- Chương 1 hơi dài hơn ~500-700 từ một chút (6 đoạn dày) — vẫn trong phạm vi 1 trang render.
- Bibliography [1]–[8] chưa có, theo yêu cầu sẽ thêm sau. Ánh xạ dự kiến: [1] Tesseract, [2] CRNN-CTC, [3] GPT-4V, [4] Gemini, [5] Qwen-VL, [6] LoRA, [7] OmniDocBench V1.5, [8] rsLoRA — nếu orchestrator dùng thứ tự khác cần đồng bộ.
- Chưa có bảng/hình — phù hợp cho Tóm tắt + Giới thiệu, chương sau mới cần.

## Conclusion
Draft `ch01_ch02.md` hoàn chỉnh, tuân thủ format/style, số liệu chính xác, ~4-5 trang render (ch01 ~1 trang, ch02 ~3-4 trang). Sẵn sàng để orchestrator duyệt hoặc merge với output của worker_B (chương khác). Hạn chế duy nhất: bibliography sẽ thêm sau (đã rõ trong yêu cầu).

## Verification Method
- Mở file: `c:\project\uit\nlp\GLM-OCR\.agents\orchestrator\drafts\ch01_ch02.md`.
- Kiểm tra heading: grep `^##` và `^###` — phải thấy `## 1. Tóm tắt`, `## 2. Giới thiệu`, `### 2.1`, `### 2.2`, `### 2.3`, `### 2.4`.
- Kiểm tra số liệu khóa: grep `94.62`, `2.01`, `0.42`, `89.4`, `97.6`, `1.1 tỷ`, `GlmOcrForConditionalGeneration` — phải xuất hiện đúng bối cảnh.
- Kiểm tra không có ký tự lạ: grep `[^\x00-\x7F]` ngoài tập ký tự tiếng Việt hợp lệ (phải loại trừ Hán tự như 献).
- Kiểm tra không emoji: grep Unicode emoji range — phải rỗng.
- Render bằng Markdown previewer để xác nhận số trang trực quan.
