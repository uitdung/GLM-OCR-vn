## 7. Phân tích hạn chế

Chương này trình bày các hạn chế của mô hình GLM-OCR-vn đã finetune, với trọng tâm vào hiện tượng quan trọng nhất được phát hiện trong quá trình đánh giá: khoảng cách giữa kết quả trên benchmark và kết quả khi áp dụng thực tế. Việc phân tích kỹ nguyên nhân gốc rễ (root cause analysis) là điều kiện tiên quyết để đề xuất các hướng cải thiện khả thi ở phần sau.

### 7.1. Khoảng cách giữa benchmark và thực tế (Real-world gap)

Trên tập kiểm thử (Stage 2 benchmark) được xây dựng từ cùng quy trình sinh dữ liệu như tập huấn luyện, mô hình đạt kết quả rất cao: CER = 0.42% và Độ chính xác văn bản (Document Accuracy, DA) = 97.6%. Kết quả này cho thấy mô hình gần như hoàn hảo trên dữ liệu phân phối tương đồng với dữ liệu huấn luyện (in-distribution).

Tuy nhiên, khi mô hình được thử nghiệm trên ảnh thực tế — bao gồm ảnh báo chí chụp lại từ màn hình, ảnh chụp điện thoại có nhiễu cảm biến, ảnh có độ phân giải thấp hoặc font chữ lạ — DA giảm rõ rệt. Sự suy giảm này không ngẫu nhiên mà tập trung vào một dạng lỗi đặc trưng: nhầm lẫn dấu thanh tiếng Việt (tone confusion). Đây là phát hiện quan trọng nhất của đồ án, vì nó chỉ ra rằng kết quả trên benchmark là điều kiện cần nhưng chưa đủ để đánh giá khả năng tổng quát hóa của mô hình.

Sự chênh lệch giữa benchmark và thực tế xuất phát từ hai nguyên nhân chính: (i) phân phối ảnh thực tế có nhiễu và biến đổi cao hơn nhiều so với ảnh synthetic trong benchmark; (ii) cấu hình huấn luyện giữ cố định một thành phần quan trọng của kiến trúc, khiến mô hình không học được các đặc trưng thị giác tinh tế cần thiết để phân biệt dấu thanh. Nguyên nhân thứ hai được phân tích chi tiết ở 7.2 và 7.3.

Bảng 7.1 tóm tắt sự đối lập giữa hai chế độ đánh giá:

| Chế độ đánh giá | CER | DA | Phân phối dữ liệu |
|---|---|---|---|
| Stage 2 benchmark (in-distribution) | 0.42% | 97.6% | Synthetic, font chuẩn, augmentation nhẹ 35% |
| Thực tế (out-of-distribution) | Tăng rõ rệt | Giảm rõ rệt | Ảnh chụp, báo chí, low-res, noise cao |

*Bảng 7.1: Khoảng cách giữa kết quả benchmark và kết quả thực tế.*

Phát hiện này có hệ quả quan trọng đối với cách đánh giá mô hình OCR tiếng Việt: nếu chỉ đánh giá trên benchmark synthetic, ta dễ có cảm giác sai rằng bài toán đã "gần như giải quyết". Thực tế, bất kỳ hệ thống OCR nào muốn deploy đều phải đối mặt với ảnh chất lượng kém và phải xử lý được dấu thanh tiếng Việt — một thách thức đặc thù mà tiếng Anh hoặc tiếng Trung không gặp phải ở mức độ tương đương.

### 7.2. Phân tích nguyên nhân gốc rễ: Frozen Vision Tower

Nguyên nhân cốt lõi của real-world gap nằm ở cấu hình huấn luyện: `freeze_vision_tower: true` được áp dụng trong cả Stage 1 và Stage 2. Điều này có nghĩa là bộ mã hóa thị giác — mô hình CogViT với 24 layer và hidden size 1024 — giữ nguyên toàn bộ trọng số được pretrained cho tiếng Anh và tiếng Trung trong suốt quá trình finetune tiếng Việt. Chỉ có projector và LLM decoder (16 layer, hidden 1536) được cập nhật trọng số.

Hệ quả là, bộ mã hóa thị giác không học được đặc trưng thị giác mới cho dấu thanh tiếng Việt. Đây là vấn đề nghiêm trọng vì đặc trưng phân biệt giữa các dấu thanh tiếng Việt rất tinh tế về mặt pixel:

- Dấu sắc (/) và dấu huyền (\\) chỉ khác nhau về hướng nét, tương đương vài pixel ở độ phân giải 336×336.
- Dấu ngã (~) và dấu mũ (^) trên cùng một nguyên âm khác nhau chủ yếu ở độ cong của nét.
- Dấu móc (hỏi, ngã) thêm một nét nhỏ có diện tích rất hạn chế.

Ước tính ở độ phân giải ảnh đầu vào 336×336 và sau khi đi qua patch embedding (patch 14×14, 24×24 = 576 token không gian), sự khác biệt pixel giữa dấu sắc và dấu huyền trên một ký tự chỉ chiếm khoảng 5–10 pixel — một tín hiệu rất yếu để bộ mã hóa thị giác giữ lại. Khi trọng số CogViT bị đóng băng, các token thị giác đầu ra cho vùng dấu thanh mang thông tin mờ nhạt và không phân biệt được, vì bộ mã hóa này chưa từng được tối ưu cho đặc trưng đó.

Chuỗi nhân quả như sau: trọng số CogViT cố định → đặc trưng trích xuất cho vùng dấu thanh không đủ chi tiết và không được tinh chỉnh → projector (dù được học) chỉ có thể ánh xạ từ một không gian đặc trưng "mờ" sang không gian token của LLM → LLM nhận thông tin mơ hồ về dấu thanh → mô hình nhầm lẫn giữa các dấu thanh khi ảnh đầu vào có nhiễu.

Cần lưu ý rằng trên benchmark, gap này ít xuất hiện vì ảnh synthetic có chất lượng cao (font rõ, không noise nặng, không perspective). Đặc trưng dấu thanh "mờ" vẫn đủ để LLM suy luận đúng khi ngữ cảnh sạch. Chỉ khi ảnh có nhiễu thực tế thì độ mờ của đặc trưng vượt ngưỡng chịu đựng của LLM và nhầm lẫn xuất hiện.

### 7.3. Hệ quả: Tone confusion đặc biệt nghiêm trọng

Hệ quả trực tiếp của frozen vision tower là hiện tượng tone confusion — nhầm lẫn giữa các nguyên âm mang dấu thanh khác nhau. Bảng 7.2 liệt kê các cặp nhầm lẫn điển hình được quan sát:

| Nguyên âm đúng | Nguyên âm bị nhầm | Dấu thanh khác nhau | Mức pixel khác biệt |
|---|---|---|---|
| ả (hỏi) | ã (ngã) | dấu hỏi vs dấu ngã | Rất nhỏ (~5px) |
| ạ (nặng) | ậ (nặng-mũ) | thêm/bớt dấu mũ | Rất nhỏ (~5px) |
| ằ (huyền) | ắ (sắc) — sai dấu | huyền vs sắc | Rất nhỏ (~5–10px) |
| ớ (sắc) | ờ (huyền) | sắc vs huyền | Rất nhỏ (~5–10px) |

*Bảng 7.2: Các cặp tone confusion điển hình do đặc trưng dấu thanh quá tinh tế so với capacity của CogViT đã đóng băng.*

Đặc điểm của tone confusion là nó khu trú vào các nguyên âm mang dấu thanh, chứ không ảnh hưởng đến phụ âm hoặc nguyên âm không dấu. Điều này khớp với dự đoán lý thuyết: phụ âm và nguyên âm không dấu (như a, ă, â) khác nhau nhiều pixel và đặc trưng dễ phân biệt ngay cả với CogViT đóng băng, trong khi dấu thanh là thông tin tinh tế không được học riêng cho tiếng Việt.

Về mức độ ảnh hưởng: tiếng Việt là ngôn ngữ có hệ thống thanh điệu chặt chẽ, một dấu thanh sai có thể thay đổi nghĩa của từ hoàn toàn (ví dụ "má" — mẹ, "mà" — liên từ, "mả" — mộ, "mã" — mã). Vì vậy tone confusion có tác động đến độ chính xác ngữ nghĩa lớn hơn nhiều so với CER thuần. Một câu có thể có DA thấp dù chỉ sai 2–3 ký tự dấu thanh, vì các từ bị sai đều trở thành từ vô nghĩa hoặc sai nghĩa.

### 7.4. Đề xuất cải thiện cụ thể

Dựa trên chẩn đoán ở 7.2 và 7.3, phần này đề xuất sáu hướng cải thiện theo thứ tự ưu tiên, với lý do kỹ thuật và đánh giá tính khả thi cho từng hướng.

**(1) Unfreeze Vision Tower (toàn phần hoặc từng phần)** — Đây là biện pháp trực tiếp nhất để giải quyết nguyên nhân gốc rễ. Có hai chiến lược khả thi:

- *Unfreeze các layer cuối của ViT*: CogViT có 24 layer, các layer sâu (ví dụ từ layer 16 trở lên) thường học đặc trưng bậc cao (semantic). Ta có thể mở đóng băng các layer sâu này và giữ cố định các layer đầu (low-level edge/texture) — vốn đã được pretrain tốt và không cần tinh chỉnh cho tiếng Việt. Chiến lược này giảm chi phí tính toán và tránh catastrophic forgetting so với unfreeze toàn phần.
- *Áp dụng LoRA (Low-Rank Adaptation) trên ViT*: Với rank nhỏ (4–8), ta thêm adapter hạng thấp vào các layer của ViT. LoRA tăng capacity học đặc trưng dấu thanh mà không phá vỡ trọng số pretrain, đồng thời giảm đáng kể số tham số cần huấn luyện. Đây là lựa chọn cân bằng giữa hiệu quả và hiệu năng.

**(2) Lịch học (LR scheduling) riêng cho vision và text** — Khi unfreeze vision tower, không nên dùng cùng learning rate cho cả hai thành phần. Vision encoder đã được pretrain tốt nên cần LR thấp (đề xuất 1e-5 hoặc 5e-6) để tránh phá vỡ đặc trưng tổng quát, trong khi text decoder cần LR cao hơn (đề xuất 1e-4) để học phân phối ngôn ngữ tiếng Việt. Thực hiện bằng cách chia tham số thành các nhóm (param groups) riêng trong optimizer, mỗi nhóm có LR và weight decay khác nhau.

**(3) Tăng độ phân giải ảnh đầu vào** — Từ 336 lên 448 hoặc 512 pixel giúp dấu thanh có nhiều pixel hơn, giảm tỷ lệ "mờ" đặc trưng. Nhược điểm là tăng chi phí attention bậc hai với số token (24²→32² token tăng ~78%), cần đánh đổi chi phí tính toán. Đề xuất dùng 448 như điểm cân bằng.

**(4) Tăng cường data augmentation nặng hơn cho ảnh thực tế** — Hiện tại augmentation chỉ áp dụng cho 35% dữ liệu và ở mức nhẹ. Đề xuất bổ sung các biến đổi mô phỏng điều kiện thực tế: shadow (bóng đổ), perspective distortion (méo phối cảnh), motion blur (mờ do rung máy), JPEG artifact nặng. Nên đưa tỷ lệ augmentation lên 60–70% và tăng cường độ để mô hình gặp dữ liệu "khó" ngay trong huấn luyện.

**(5) Hard negative mining** — Sinh tập ảnh chứa các cặp nhầm lẫn (confusion pairs) mà mô hình đang sai (liệt kê ở Bảng 7.2). Tập trung generate các ảnh có dấu thanh của các nguyên âm dễ nhầm, với nhiễu nhẹ để ép mô hình học ranh giới phân biệt. Có thể thực hiện bằng cách: đánh giá mô hình hiện tại trên tập sinh lớn → chọn các mẫu bị sai → sinh thêm các mẫu tương đồng → đưa vào tập huấn luyện với trọng số cao.

**(6) Multi-scale training** — Resize ảnh ngẫu nhiên trong khoảng [0.8×, 1.2×] so với kích thước chuẩn trong mỗi bước huấn luyện. Giúp mô hình bền vững hơn với biến đổi kích thước chữ trong ảnh thực tế (chữ trong ảnh chụp điện thoại thường không cùng kích thước chuẩn như synthetic).

### 7.5. Các hạn chế khác ngoài vision tower

Ngoài nguyên nhân vision tower, đồ án còn có các hạn chế về dữ liệu:

- **Dataset synthetic giới hạn font**: chỉ dùng 12 font Windows cài sẵn (Arial, Times New Roman, Calibri, v.v.). Thiếu font chữ viết tay (handwritten), font chữ trên báo mạng (web fonts có hinting khác), font nghệ thuật. Điều này khiến mô hình chưa bền với sự đa dạng font thực tế.
- **Crawler giới hạn nguồn**: chỉ thu thập văn bản từ 15 nguồn, chủ yếu là bài viết tin tức và văn bản thông dụng. Thiếu văn bản chuyên ngành như sách giáo khoa, văn bản pháp lý, hồ sơ y tế. Điều này tạo ra domain bias — mô hình tốt với ngôn ngữ báo chí nhưng có thể kém với thuật ngữ chuyên ngành.
- **Thiếu đa dạng điều kiện ảnh**: ảnh synthetic sinh ra trên nền trắng/trắng-ngiện, thiếu ảnh có phông nền phức tạp, có table/cell, hoặc có watermark.

Các hạn chế này cộng hưởng với tone confusion: một ảnh báo mạng có cả font lạ và noise sẽ khiến cả mô hình suy luận sai dấu thanh và sai ký tự.

### 7.6. Bảng tổng hợp đề xuất và ưu tiên

Bảng 7.3 tổng hợp sáu hướng đề xuất, kèm mức độ ưu tiên và ước tính nỗ lực thực hiện (dựa trên ước lượng về công sức triển khai và tài nguyên tính toán):

| # | Đề xuất | Ưu tiên | Nỗ lực ước tính | Lý do |
|---|---|---|---|---|
| 1 | Unfreeze Vision Tower (full hoặc partial) | Cao | Trung bình (cần finetune lại S1/S2, ~2–4 ngày GPU) | Giải quyết trực tiếp root cause |
| 2 | LR scheduling riêng vision vs text | Cao | Thấp (chỉ thay đổi code optimizer) | Bắt buộc khi làm (1), giảm risk phá pretrain |
| 3 | Tăng resolution 336 → 448/512 | Trung bình | Thấp (đổi config) đến Trung bình (VRAM tăng) | Giảm mờ đặc trưng dấu thanh |
| 4 | Data augmentation nặng hơn (shadow, perspective, motion blur) | Cao | Thấp (đổi pipeline augmentation) | Bắt kịp điều kiện ảnh thực tế |
| 5 | Hard negative mining cho confusion pairs | Trung bình | Trung bình (cần pipeline đánh giá + sinh) | Nhắm đúng nhóm lỗi phổ biến |
| 6 | Multi-scale training [0.8×, 1.2×] | Trung bình | Thấp (đổi transform) | Tăng bền vững kích thước chữ |

*Bảng 7.3: Bảng tổng hợp sáu hướng đề xuất cải thiện, xếp theo mức độ ưu tiên và nỗ lực ước tính.*

Khuyến nghị thực tế: nên thực hiện (1) + (2) + (4) cùng nhau trong một đợt finetune mới, vì ba đề xuất này bổ trợ nhau — unfreeze vision cần LR thấp để ổn định, và augmentation nặng giúp tận dụng capacity học mới của vision tower. (3) và (6) có thể thêm vào bằng cách thay đổi config đơn giản. (5) là bước tinh chỉnh thứ cấp sau khi đã có mô hình cải thiện từ (1)–(4).

## 8. Demo

Chương này mô tả cách mô hình GLM-OCR-vn (bản merged sau Stage 2, ký hiệu `glm-ocr-vn-s2`) được triển khai để sử dụng thực tế, từ pipeline suy luận, đoạn mã tham chiếu, đến các tùy chọn deploy và ví dụ minh họa kết quả OCR trước/sau khi finetune.

### 8.1. Mô tả pipeline demo

Pipeline suy luận của mô hình gồm năm bước:

1. **Upload ảnh**: người dùng cung cấp ảnh chứa văn bản tiếng Việt (PNG/JPG). Ảnh được nạp vào bộ nhớ dưới dạng đối tượng hình ảnh PIL.
2. **Load mô hình merged**: nạp `glm-ocr-vn-s2` (~2.1 GB safetensors, định dạng bfloat16) bằng `AutoModelForImageTextToText` từ thư viện `transformers`. Bộ xử lý `AutoProcessor` được nạp cùng để xử lý ảnh và văn bản prompt.
3. **Áp dụng chat template**: prompt người dùng được xây dựng theo định dạng chat của GLM, gồm một ảnh và một chỉ thị "Text Recognition:". Hàm `apply_chat_template` token hóa và tạo `input_ids` cùng `pixel_values`/`image_features`.
4. **Sinh đầu ra**: gọi `model.generate(...)` với `max_new_tokens=512` và `do_sample=False` (greedy decoding) để có kết quả tất định, phù hợp với OCR. Greedy được chọn thay vì sampling vì OCR cần độ ổn định — cùng một ảnh phải luôn cho cùng một kết quả.
5. **Giải mã và hiển thị**: cắt bỏ phần `input_ids` ban đầu, giải mã phần token mới sinh, loại bỏ special token, và trả về chuỗi văn bản đã nhận dạng.

Lựa chọn greedy decoding có lý do cụ thể: với bài toán OCR, ngẫu nhiên (sampling) chỉ làm tăng phương sai mà không cải thiện chất lượng. `max_new_tokens=512` đủ cho văn bản dài vài câu trong một ảnh đơn. Định dạng bfloat16 giúp giảm một nửa bộ nhớ GPU so với float32 mà không làm giảm chất lượng đáng kể.

### 8.2. Đoạn mã pipeline demo

Đoạn mã Python dưới đây sử dụng thư viện `transformers` để thực hiện toàn bộ pipeline demo. Mã giả định mô hình đã được merge và lưu tại thư mục `./glm-ocr-vn-s2`:

```python
from transformers import AutoProcessor, AutoModelForImageTextToText
import torch

MODEL_PATH = "./glm-ocr-vn-s2"
processor = AutoProcessor.from_pretrained(MODEL_PATH, trust_remote_code=True)
model = AutoModelForImageTextToText.from_pretrained(
    MODEL_PATH, trust_remote_code=True,
    torch_dtype=torch.float16, device_map="auto"
)

def ocr(image_path):
    messages = [{"role": "user", "content": [
        {"type": "image", "url": image_path},
        {"type": "text", "text": "Text Recognition:"},
    ]}]
    inputs = processor.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True,
        return_dict=True, return_tensors="pt",
    ).to(model.device)
    inputs.pop("token_type_ids", None)
    ids = model.generate(**inputs, max_new_tokens=512, do_sample=False)
    return processor.decode(ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()

print(ocr("bao_chi_test.png"))
```

*Đoạn mã 8.1: Hàm OCR tối giản cho GLM-OCR-vn-S2.*

Một số lưu ý khi chạy đoạn mã:

- `trust_remote_code=True` là bắt buộc vì GLM-OCR sử dụng mã xử lý riêng (custom modeling code) được tải kèm mô hình.
- `device_map="auto"` tự động phân bổ mô hình giữa GPU và CPU tùy theo bộ nhớ khả dụng. Nếu GPU đủ (khoảng 4–5 GB VRAM cho mô hình 2.1 GB ở float16), toàn bộ nằm trên GPU.
- `inputs.pop("token_type_ids", None)` loại bỏ trường không dùng trong suy luận, tránh lỗi khi truyền vào `generate`.
- Cắt `ids[0][inputs["input_ids"].shape[1]:]` lấy đúng phần token mới sinh, bỏ qua prompt.

### 8.3. Các tùy chọn deploy

Để triển khai mô hình trong môi trường sản xuất, có ba lựa chọn phổ biến:

**Ollama** — Đóng gói mô hình qua `Modelfile` cùng các tệp safetensors. Lợi ích chính là Ollama tự động quantize (4-bit hoặc 8-bit) giúp giảm bộ nhớ, đồng thời cung cấp API REST tương thích OpenAI. Phù hợp cho môi trường có giới hạn VRAM. Nhược điểm là Ollama hiện chưa hỗ trợ đầy đủ mọi kiến trúc MLLM, cần kiểm tra khả năng tương thích của GLM-OCR trước khi chọn.

**vLLM** — Sử dụng lệnh `vllm serve zai-org/GLM-OCR --port 8080` để khởi động dịch vụ suy luận hiệu năng cao. vLLM tận dụng paged attention và continuous batching, cho phép xử lý nhiều yêu cầu song song. Phù hợp cho môi trường có nhiều người dùng đồng thời. Cần GPU đủ lớn (khuyến nghị >= 8 GB VRAM cho mô hình này).

**Flask service (`python -m glmocr.server`)** — Đóng gói pipeline 8.2 thành một dịch vụ Flask REST. Đơn giản nhất để tự xây dựng và kiểm soát, dễ tích hợp vào hệ thống có sẵn. Nhược điểm là không có batching hiệu quả — mỗi yêu cầu xử lý tuần tự, cần đưa vào hàng đợi nếu có tải cao.

Lựa chọn phụ thuộc vào yêu cầu tải: tải thấp và cần linh hoạt → Flask; tải cao và cần throughput → vLLM; giới hạn VRAM → Ollama.

### 8.4. Ví dụ OCR thực tế trước/sau khi finetune

Phần này trình bày ví dụ minh họa về đầu ra OCR của ba phiên bản mô hình trên cùng một ảnh đầu vào. **Lưu ý quan trọng**: các ví dụ dưới đây là minh họa (illustration) dựa trên quan sát pattern tone confusion đã phân tích ở Chương 7. Vì báo cáo không chứa ảnh thật, các kết quả được mô tả bằng văn bản; độ chính xác cụ thể cần được xác nhận lại bằng thử nghiệm thực trên ảnh tương ứng. Mục đích minh họa là làm rõ pattern lỗi được phân tích, không phải là số liệu đánh giá chính thức.

**Ảnh minh họa 1** — Văn bản ground truth (GT) là câu lịch sử tiếng Việt, font Arial rõ, chất lượng ảnh cao:

- GT: "Nguyễn Trãi viết bài bình Ngô đại cáo"
- Original GLM-OCR (chưa finetune): "Nguyển Trãi viết bài bình Ngô đại cáo"
  - *Lỗi quan sát*: nhầm "Nguyễn" → "Nguyển" — bỏ qua dấu thanh của nguyên âm ễ. Đây là pattern phổ biến của mô hình chưa học dấu thanh tiếng Việt.
- Sau Stage 1: "Nguyễn Trãi viết bài bình Ngô đại cáo"
  - *Đã sửa được* lỗi dấu thanh trên "Nguyễn", nhưng có thể còn một vài lỗi nhỏ ở các từ phức tạp khác.
- Sau Stage 2: "Nguyễn Trãi viết bài bình Ngô đại cáo"
  - *Chính xác toàn bộ* trên ảnh sạch.

Bảng 8.1 tóm tắt minh họa:

| Mô hình | Đầu ra | Lỗi |
|---|---|---|
| GT | Nguyễn Trãi viết bài bình Ngô đại cáo | — |
| Original GLM-OCR | Nguyển Trãi viết bài bình Ngô đại cáo | ễ → ể (sai dấu) |
| Stage 1 | Nguyễn Trãi viết bài bình Ngô đại cáo | Đã sửa (ảnh sạch) |
| Stage 2 | Nguyễn Trãi viết bài bình Ngô đại cáo | Chính xác |

*Bảng 8.1: Minh họa trước/sau khi finetune trên ảnh chất lượng cao. (Minh họa, không phải số liệu đánh giá chính thức.)*

**Ảnh minh họa 2** — Văn bản GT là câu ngắn, ảnh chụp điện thoại có noise cao và rung nhẹ:

- GT: "thầy giáo dạy em học"
- Original GLM-OCR: "thây giao day em hoc" — sai nhiều (mất dấu, sai chính tả).
- Sau Stage 2: "thây giáo dạy em học"
  - *Lỗi tồn tại*: tone confusion "thầy" → "thây" — dấu thanh ầ (trong "thầy") bị mất do noise cao che lấp đặc trưng dấu thanh. Đây là pattern tone confusion đặc trưng của real-world gap đã mô tả ở 7.3.

Bảng 8.2 tóm tắt:

| Mô hình | Đầu ra | Lỗi |
|---|---|---|
| GT | thầy giáo dạy em học | — |
| Original GLM-OCR | thây giao day em hoc | Nhiều lỗi, mất dấu |
| Stage 2 (ảnh noise cao) | thây giáo dạy em học | Tone confusion ầy → ây (residual) |

*Bảng 8.2: Minh họa tone confusion còn tồn tại trên ảnh noise cao. (Minh họa, không phải số liệu đánh giá chính thức.)*

Hai ví dụ trên cho thấy hai chế độ hoạt động: trên ảnh sạch, Stage 2 đạt kết quả gần hoàn hảo; trên ảnh noise cao, tone confusion vẫn còn tồn tại — đúng như dự đoán từ phân tích frozen vision tower ở Chương 7.

### 8.5. Bảng lỗi tồn tại (residual errors)

Sau khi finetune Stage 2, các nhóm lỗi còn tồn tại trên ảnh thực tế được tổng hợp ở Bảng 8.3:

| Nhóm lỗi | Điều kiện xuất hiện | Mức độ | Hướng xử lý |
|---|---|---|---|
| Tone confusion (nhầm dấu thanh) | Ảnh noise cao hoặc low-res | Vừa–Cao | Unfreeze ViT (7.4-1), tăng resolution (7.4-3) |
| Mất chữ "đ" | Font lạ, "đ" bị nhầm thành "d" | Thấp | Mở rộng tập font (7.5), hard negative cho "đ/d" |
| Mất dấu khi perspective distortion nặng | Ảnh chụp nghiêng, méo | Thấp–Vừa | Data augmentation perspective (7.4-4) |
| Sai ký tự khi shadow mạnh | Ảnh có bóng đổ đè lên chữ | Thấp | Augmentation shadow (7.4-4) |
| Cắt xén văn bản dài | Ảnh có nhiều dòng, max_new_tokens không đủ | Thấp | Tăng max_new_tokens, chunk ảnh |

*Bảng 8.3: Bảng tổng hợp các nhóm lỗi tồn tại sau Stage 2 và hướng xử lý tương ứng.*

Đặc điểm chung của hầu hết lỗi tồn tại là đều có liên quan đến chất lượng ảnh đầu vào và đặc trưng thị giác tinh tế — chính là vấn đề vision tower đã phân tích. Điều này củng cố kết luận rằng unfreeze vision tower là biện pháp ưu tiên cao nhất để cải thiện mô hình trong các đợt finetune tiếp theo.

## Kết luận và Hướng phát triển

### Tổng kết đóng góp

Đồ án đã thực hiện nghiên cứu và finetune mô hình ngôn ngữ hình ảnh lớn (MLLM) GLM-OCR cho bài toán nhận dạng văn bản tiếng Việt. Năm đóng góp chính của đồ án có thể tóm tắt như sau:

1. **Xây dựng quy trình sinh dữ liệu synthetic tiếng Việt hoàn chỉnh**: với 12 font Windows, 88 từ tiếng Anh để xen kẽ, 7 generator phân tách theo cấu trúc văn bản, và pipeline augmentation theo tỷ lệ 65/35 (65% ảnh gốc, 35% ảnh augmentation nhẹ). Quy trình này cung cấp nền dữ liệu có cấu trúc và tái lập được cho huấn luyện.
2. **Huấn luyện hai stage finetune** với cấu hình S1 và S2 khác nhau về learning rate và epoch, áp dụng frozen vision tower, projector và LLM decoder được học. Mô hình merged sau Stage 2 có kích thước khoảng 2.1 GB safetensors ở định dạng bfloat16, tương thích với `transformers`.
3. **Đánh giá định lượng** trên benchmark xây dựng từ cùng quy trình synthetic: kết quả Stage 1 đạt CER 2.01% / DA 89.4%, Stage 2 đạt CER 0.42% / DA 97.6% — cho thấy finetune hai stage cải thiện rõ rệt độ chính xác.
4. **Phát hiện và chẩn đoán hiện tượng real-world gap**: khi thử nghiệm trên ảnh báo chí và ảnh chụp điện thoại, DA giảm rõ rệt. Đồ án đã tiến hành phân tích nguyên nhân gốc rễ và xác định frozen vision tower (CogViT 24 layer, hidden 1024) là nguyên nhân chính, dẫn đến tone confusion với dấu thanh tiếng Việt. Đây là phát hiện kỹ thuật quan trọng nhất của đồ án.
5. **Đề xuất sáu hướng cải thiện cụ thể** kèm mức ưu tiên và nỗ lực ước tính, từ unfreeze vision tower (ưu tiên cao) đến multi-scale training (ưu tiên trung bình). Các đề xuất đều có cơ sở kỹ thuật rõ ràng và có thể thực hiện trong các đợt finetune tiếp theo.

### Kết quả chính và hạn chế cốt lõi

Về kết quả định lượng trên benchmark, Stage 2 đạt CER 0.42% và DA 97.6% — kết quả rất tốt so với baseline GLM-OCR chưa finetune. Tuy nhiên, đồ án thẳng thắn ghi nhận rằng kết quả này chưa phản ánh đầy đủ khả năng deploy thực tế, vì khoảng cách đến kết quả trên ảnh thực tế còn đáng kể. Nguyên nhân cốt lõi đã được phân tích kỹ: cấu hình `freeze_vision_tower: true` giữ cố định bộ mã hóa thị giác CogViT trong suốt hai stage, khiến mô hình không học được đặc trưng tinh tế cho dấu thanh tiếng Việt — đặc trưng chỉ khác nhau vài pixel và là đặc thù của tiếng Việt so với tiếng Anh/Trung mà CogViT đã được pretrain.

Phát hiện này có giá trị thực tiễn cho các đồ án finetune MLLM sau này: việc đóng băng vision tower là một mặc định phổ biến để tiết kiệm tính toán, nhưng với ngôn ngữ có hệ thống dấu thanh tinh tế như tiếng Việt, đây là một lựa chọn có rủi ro và cần được xem xét lại.

### Hướng phát triển

Dựa trên phân tích hạn chế ở Chương 7, các hướng phát triển cụ thể của đồ án trong giai đoạn tiếp theo bao gồm:

1. **Unfreeze vision tower với LR scheduling riêng**: thực hiện đề xuất (1) và (2) ở Chương 7. Đây là hướng ưu tiên cao nhất, dự kiến sẽ giảm rõ rệt tone confusion vì giải quyết trực tiếp nguyên nhân gốc rễ. Có thể bắt đầu với LoRA rank nhỏ (4–8) trên các layer sâu của CogViT để cân bằng giữa capacity học và chi phí tính toán.
2. **Mở rộng domain của dataset**: thu thập văn bản từ các lĩnh vực còn thiếu — sách giáo khoa, văn bản pháp lý, hồ sơ y tế, văn bản hành chính. Mở rộng crawler từ 15 nguồn hiện tại lên 40–50 nguồn để giảm domain bias.
3. **Thêm font handwritten và font đa dạng**: bổ sung font chữ viết tay và font báo mạng vào tập 12 font hiện tại, mục tiêu 25–30 font. Giúp mô hình bền vững hơn với sự đa dạng font thực tế.
4. **Multi-scale training và augmentation nặng**: thực hiện đề xuất (4) và (6) ở Chương 7 — thêm shadow, perspective, motion blur vào pipeline augmentation, tăng tỷ lệ augmentation lên 60–70%, và resize ngẫu nhiên [0.8×, 1.2×] trong huấn luyện.
5. **Đánh giá trên bộ test chuẩn tiếng Việt**: ngoài benchmark synthetic nội bộ, đồ án cần đánh giá trên các bộ test chuẩn của cộng đồng như NEWS-VN (bộ dữ liệu tiêu đề báo) và VIETOCR benchmark. Việc đánh giá trên bộ chuẩn giúp so sánh được với các mô hình OCR tiếng Việt khác và có kết quả khả lập lại độc lập.

Ngoài ra, một hướng dài hạn đáng cân nhắc là huấn luyện lại vision tower từ đầu cho tiếng Việt (pretrain CogViT trên ảnh chữ tiếng Việt đa dạng), thay vì chỉ finetune adapter. Hướng này tốn kém hơn nhưng có tiềm năng giải quyết triệt để vấn đề đặc trưng dấu thanh.

Tóm lại, đồ án đã hoàn thành mục tiêu finetune GLM-OCR cho tiếng Việt, đạt kết quả tốt trên benchmark và quan trọng hơn là phát hiện, chẩn đoán rõ ràng nguyên nhân của khoảng cách thực tế. Các hướng phát triển được đề xuất đều có cơ sở kỹ thuật cụ thể và có thể thực hiện trong các giai đoạn tiếp theo, đưa mô hình tiệm cận khả năng deploy thực tế cho bài toán OCR tiếng Việt.
