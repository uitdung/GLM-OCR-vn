<!--
Bản Front Matter này được tạo bởi worker_synthesizer.
Nội dung: trang bìa, mục lục, danh sách hình vẽ, danh sách bảng biểu, tài liệu tham khảo.
Ghép nối tiếp (concatenate) phía trước 4 draft chapters để tạo file báo cáo final.
-->

<div align="center">

# Báo cáo Đồ án

# Nghiên cứu và Finetune Mô hình Ngôn ngữ Đa phương thức Lớn (MLLM) cho Nhận dạng Ký tự Quang học Tiếng Việt — Trường hợp GLM-OCR

</div>

---

## Mục lục

- [1. Tóm tắt](#1-tóm-tắt)
- [2. Giới thiệu](#2-giới-thiệu)
  - [2.1 Đặt vấn đề OCR tiếng Việt](#21-đặt-vấn-đề-ocr-tiếng-việt)
  - [2.2 Động lực](#22-động-lực)
  - [2.3 Đóng góp của đồ án](#23-đóng-góp-của-đồ-án)
  - [2.4 Cấu trúc báo cáo](#24-cấu-trúc-báo-cáo)
- [3. Tổng quan nghiên cứu](#3-tổng-quan-nghiên-cứu)
  - [3.1 Mô hình ngôn ngữ thị giác cho OCR: lộ trình tiến hóa](#31-mô-hình-ngôn-ngữ-thị-giác-cho-ocr-lộ-trình-tiến-hóa)
  - [3.2 Kiến trúc chi tiết của GLM-OCR](#32-kiến-trúc-chi-tiết-của-glm-ocr)
  - [3.3 So sánh PP-OCRv6 và GLM-OCR](#33-so-sánh-pp-ocrv6-và-glm-ocr)
  - [3.4 Hiện trạng OCR tiếng Việt](#34-hiện-trạng-ocr-tiếng-việt)
- [4. Phương pháp đề xuất](#4-phương-pháp-đề-xuất)
  - [4.1 Tổng quan pipeline hai giai đoạn](#41-tổng-quan-pipeline-hai-giai-đoạn)
  - [4.2 Toán học của LoRA](#42-toán-học-của-lora)
  - [4.3 Toán học của rsLoRA](#43-toán-học-của-rslora)
  - [4.4 Lý do đóng băng vision tower và mở khóa projector](#44-lý-do-đóng-băng-vision-tower-và-mở-khóa-projector)
  - [4.5 Thiết kế bộ dữ liệu v3 chống ảo giác](#45-thiết-kế-bộ-dữ-liệu-v3-chống-ảo-giác)
  - [4.6 Cấu hình YAML cho hai giai đoạn finetune](#46-cấu-hình-yaml-cho-hai-giai-đoạn-finetune)
  - [4.7 Logic bộ sinh dữ liệu](#47-logic-bộ-sinh-dữ-liệu-trích-từ-generate_vietnamese_dataset_v3py)
- [5. Thực nghiệm](#chương-5-thực-nghiệm)
  - [5.1 Môi trường phần cứng và phần mềm](#51-môi-trường-phần-cứng-và-phần-mềm)
  - [5.2 Tập dữ liệu v3](#52-tập-dữ-liệu-v3)
  - [5.3 Huấn luyện Stage 1 (line-level)](#53-huấn-luyện-stage-1-line-level)
  - [5.4 Huấn luyện Stage 2 (document-level)](#54-huấn-luyện-stage-2-document-level)
  - [5.5 Cấu hình YAML chi tiết](#55-cấu-hình-yaml-chi-tiết)
  - [5.6 Hợp nhất adapter và triển khai](#56-hợp-nhất-adapter-và-triển-khai)
  - [5.7 Generator `gen_plain_words` — chống ảo giác](#57-generator-gen_plain_words--chống-ảo-giác)
- [6. Kết quả và Đánh giá](#chương-6-kết-quả-và-đánh-giá)
  - [6.1 Định nghĩa các metric](#61-định-nghĩa-các-metric)
  - [6.2 Bảng kết quả chính](#62-bảng-kết-quả-chính--original-vs-stage-1-vs-stage-2)
  - [6.3 Phân tích Diacritic Accuracy theo 7 nhóm dấu](#63-phân-tích-diacritic-accuracy-theo-7-nhóm-dấu)
  - [6.4 Biểu đồ cột DA theo nhóm dấu](#64-biểu-đồ-cột-da-theo-nhóm-dấu)
  - [6.5 Phân tích so sánh Stage 1 vs Stage 2](#65-phân-tích-so-sánh-stage-1-vs-stage-2)
  - [6.6 Script đánh giá `compare_models.py`](#66-script-đánh-giá-compare_modelspy)
  - [6.7 Thảo luận](#67-thảo-luận)
- [7. Phân tích hạn chế](#7-phân-tích-hạn-chế)
  - [7.1 Khoảng cách giữa benchmark và thực tế](#71-khoảng-cách-giữa-benchmark-và-thực-tế-real-world-gap)
  - [7.2 Phân tích nguyên nhân gốc rễ: Frozen Vision Tower](#72-phân-tích-nguyên-nhân-gốc-rễ-frozen-vision-tower)
  - [7.3 Hệ quả: Tone confusion](#73-hệ-quả-tone-confusion-đặc-biệt-nghiêm-trọng)
  - [7.4 Đề xuất cải thiện cụ thể](#74-đề-xuất-cải-thiện-cụ-thể)
  - [7.5 Các hạn chế khác ngoài vision tower](#75-các-hạn-chế-khác-ngoài-vision-tower)
  - [7.6 Bảng tổng hợp đề xuất và ưu tiên](#76-bảng-tổng-hợp-đề-xuất-và-ưu-tiên)
- [8. Demo](#8-demo)
  - [8.1 Mô tả pipeline demo](#81-mô-tả-pipeline-demo)
  - [8.2 Đoạn mã pipeline demo](#82-đoạn-mã-pipeline-demo)
  - [8.3 Các tùy chọn deploy](#83-các-tùy-chọn-deploy)
  - [8.4 Ví dụ OCR thực tế trước/sau khi finetune](#84-ví-dụ-ocr-thực-tế-trướcsau-khi-finetune)
  - [8.5 Bảng lỗi tồn tại (residual errors)](#85-bảng-lỗi-tồn-tại-residual-errors)
- [Kết luận và Hướng phát triển](#kết-luận-và-hướng-phát-triển)
- [Phụ lục — Tài liệu tham khảo](#tài-liệu-tham-khảo)

---

## Danh sách hình vẽ

### Hình tham chiếu tệp PNG (nằm ở thư mục gốc dự án)

| Hình | Tệp | Chương tham chiếu | Mô tả |
|------|-----|--------------------|-------|
| H.1 | `vlm_ocr_evolution.png` | §3.1 | Lộ trình tiến hóa các kiến trúc OCR từ CRNN–CTC (2017) đến VLM end-to-end (2026) |
| H.2 | `glm_ocr_architecture.png` | §3.2 | Sơ đồ khối kiến trúc GLM-OCR: Vision Encoder CogViT → Projector → LLM Decoder |
| H.3 | `finetune_pipeline.png` | §4.1 | Pipeline finetune hai giai đoạn (Stage 1 line-level → Stage 2 doc-level → merge → deploy) |
| H.4 | `lora_architecture.png` | §4.2–4.3 | Kiến trúc adapter LoRA / rsLoRA gắn vào ma trận trọng số gốc $W_0$ |

### Sơ đồ Mermaid inline trong báo cáo

| Sơ đồ | Chương | Mô tả |
|-------|---------|-------|
| M.1 | §3.2 | Sơ đồ khối GLM-OCR (CogViT FROZEN → Projector UNFROZEN → LLM decoder, LoRA adapter vòng ngược) |
| M.2 | §4.1 | Pipeline hai giai đoạn (khối sinh dữ liệu → Stage 1 → checkpoint → Stage 2 → merge → deploy) |
| M.3 | §6.4 | Biểu đồ cột `xychart-beta` — Diacritic Accuracy theo 7 nhóm dấu (Stage 2) |
| M.4 | §6.4 | Biểu đồ ASCII tương đương DA per-group (dự phòng khi Mermaid không render) |

---

## Danh sách bảng biểu

Bảng được liệt kê theo thứ tự xuất hiện trong báo cáo.

| Bảng | Chương | Nội dung |
|------|---------|----------|
| Bảng 3.1 | §3.1 | Tiến hóa các kiến trúc OCR học sâu (2017–2026) |
| Bảng 3.2 | §3.1 | So sánh đặc trưng giữa ba nhóm kiến trúc OCR (CNN–RNN / Transformer-decoder / VLM end-to-end) |
| Bảng 3.3 | §3.3 | So sánh PP-OCRv6 (pipeline truyền thống) và GLM-OCR (VLM end-to-end) |
| Bảng 4.1 | §4.5 | 7 bộ sinh Stage 1 với trọng số (tổng 100%) |
| Bảng 4.2 | §4.5 | Augmentation 20 slot — phân bố 65% sạch / 35% biến đổi |
| Bảng 5.1 | §5.1 | Cấu hình phần cứng và phần mềm thực nghiệm (T4 16GB, LLaMA-Factory) |
| Bảng 5.2 | §5.2.1 | Bộ font 12 biến thể (Arial, Times, Calibri, Tahoma, Segoe UI) |
| Bảng 5.3 | §5.2.1 | 7 generator với trọng số cho Stage 1 |
| Bảng 5.4 | §5.2.1 | Augmentation — tỷ lệ 65% sạch / 35% biến đổi (20 slot) |
| Bảng 5.5 | §5.2.1 | 5 chế độ viết hoa ngẫu nhiên |
| Bảng 5.6 | §5.5 | Các tham số quan trọng nhất của hai giai đoạn |
| Bảng 6.1 | §6.2 | So sánh tổng thể các metric — Original vs Stage 1 vs Stage 2 |
| Bảng 6.2 | §6.3 | Ước lượng Diacritic Accuracy theo 7 nhóm dấu (Stage 2) |
| Bảng 7.1 | §7.1 | Khoảng cách giữa kết quả benchmark và kết quả thực tế |
| Bảng 7.2 | §7.3 | Các cặp tone confusion điển hình do đặc trưng dấu thanh tinh tế |
| Bảng 7.3 | §7.6 | Bảng tổng hợp sáu hướng đề xuất cải thiện (ưu tiên + nỗ lực) |
| Bảng 8.1 | §8.4 | Minh họa trước/sau khi finetune trên ảnh chất lượng cao |
| Bảng 8.2 | §8.4 | Minh họa tone confusion còn tồn tại trên ảnh noise cao |
| Bảng 8.3 | §8.5 | Bảng tổng hợp các nhóm lỗi tồn tại sau Stage 2 và hướng xử lý |

---

## Tài liệu tham khảo

Dưới đây là danh mục tài liệu tham khảo chính được trích dẫn trong báo cáo theo thứ tự xuất hiện của nhãn `[N]`. Một số mục ghi chú "cần bổ sung" do thiếu metadata chi tiết (DOI, số trang) — nội dung cốt lõi đã được xác minh.

- **[1]** Smith, R., "An Overview of the Tesseract OCR Engine", *Proceedings of the Ninth International Conference on Document Analysis and Recognition (ICDAR 2007)*, IEEE, 2007. *(Tesseract OCR engine — engine OCR mã nguồn mở dựa trên LSTM).*
- **[2]** Shi, B., Bai, X., Yao, C., "An End-to-End Trainable Neural Network for Image-based Sequence Recognition and Its Application to Scene Text Recognition", *IEEE Transactions on Pattern Analysis and Machine Intelligence (TPAMI)*, vol. 39, no. 8, pp. 1613–1625, 2017. *(Kiến trúc CRNN + CTC cho OCR — mô hình tham chiếu kinh điển).*
- **[3]** OpenAI, "GPT-4V(ision) System Card", *OpenAI Technical Report*, 2023. *(GPT-4V — MLLM tiên phong cho tác vụ thị giác–ngôn ngữ, bao gồm OCR).*
- **[4]** Google DeepMind, "Gemini: A Family of Highly Capable Multimodal Models", *Google Technical Report*, 2023–2024. *(Gemini — MLLM đa phương thức của Google, có năng lực OCR mạnh).*
- **[5]** Bai, J., Bai, S., et al. (Alibaba DAMO Academy), "Qwen-VL: A Versatile Vision-Language Model for Understanding, Localization, Text Reading, and Beyond", *arXiv:2308.12966*, 2023. *(Qwen-VL — MLLM định hướng đọc văn bản trong ảnh).*
- **[6]** Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L., Chen, W., "LoRA: Low-Rank Adaptation of Large Language Models", *International Conference on Learning Representations (ICLR 2022)*, arXiv:2106.09685, 2021. *(LoRA — kỹ thuật tinh chỉnh tham số hiệu quả với phân tích hạng thấp $BA$).*
- **[7]** OmniDocBench Team, "OmniDocBench V1.5: A Comprehensive Benchmark for Document Parsing", 2025–2026. *(Benchmark đánh giá toàn diện các mô hình OCR/VLM trên nhiều loại tài liệu; GLM-OCR đạt điểm trung bình 94.62, dẫn đầu bảng xếp hạng toàn cầu. — *cần bổ sung* chi tiết tác giả và venue chính thức).*
- **[8]** Kalajdzievski, D., "A Rank Stabilization Scaling Factor for Fine-Tuning with LoRA", *arXiv:2312.03732*, 2023. *(rsLoRA — biến thể của LoRA với hệ số co giãn $\sqrt{\alpha/r}$ giúp ổn định huấn luyện ở hạng cao).*

---

*Báo cáo này được tổng hợp từ 4 draft chapters đã được kiểm tra nội dung. Toàn bộ số liệu thực nghiệm (CER, WER, EM, DA) và siêu tham số YAML được trích dẫn nguyên vẹn từ file cấu hình và kết quả chạy thực tế của đồ án.*

---
