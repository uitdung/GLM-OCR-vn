# Vietnamese OCR — Dataset Generator & Fine-tune Tools

Bộ công cụ sinh dữ liệu và fine-tune GLM-OCR để nhận diện dấu tiếng Việt tốt hơn.

## Cấu trúc thư mục

```
dataset/
├── prepare/      Code sinh data: generator Stage 1, crawler Stage 2, lọc wordlist
│   ├── generate_stage1.py     Sinh ảnh OCR Stage 1 (text-line) + JSON ShareGPT
│   ├── crawl_stage2.py        Crawl báo Việt → ảnh Stage 2 (document-level)
│   └── filter_words.py        Lọc wordlist (chỉ giữ từ có dấu kép)
├── train/        Code train: notebook Colab + merge LoRA
│   ├── finetune.ipynb         Fine-tune trên Google Colab (T4)
│   └── merge_lora.py          Merge adapter LoRA vào base model
├── eval/         Code đánh giá: inference local + so sánh model
│   ├── run_inference.py       Test local trên 1/nhiều ảnh
│   └── evaluate.py            So sánh Original vs Finetuned trên test set
├── tools/        Tiện ích phụ trợ
│   └── font_tester.py         Test font Windows có hỗ trợ dấu tiếng Việt
├── data/         Dữ liệu (không commit — xem .gitignore)
│   ├── dictionary/            Wordlist: 3,544 từ/cụm từ có dấu kép
│   ├── vietnamese_ocr/        Dataset Stage 1 đã sinh
│   └── vietnamese_ocr_s2/     Dataset Stage 2 đã sinh
├── package.json  Shortcut lệnh (npm run gen, npm run eval:compare...)
├── GUIDE.md      Hướng dẫn chi tiết từng bước
└── README.md     File này
```

## Quick start

```bash
# 1. Gen data Stage 1 (text-line)
npm run gen:big                         # hoặc: python prepare/generate_stage1.py --num_train 20000 --augment_copies 3

# 2. Train trên Colab (nén data, upload Drive trước)
powershell Compress-Archive -Path data/vietnamese_ocr -DestinationPath data/vietnamese_ocr.zip -Force
#    Mở train/finetune.ipynb trên Colab → chạy theo bước

# 3. Test local sau khi tải model về
npm run eval:run -- --model_path ./glm-ocr-vn --image test.png

# 4. So sánh original vs finetuned
npm run eval:compare
```

👉 **Hướng dẫn chi tiết từng bước:** xem [`GUIDE.md`](GUIDE.md)
