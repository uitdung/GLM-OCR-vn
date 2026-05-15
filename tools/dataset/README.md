# Vietnamese OCR — Dataset Generator & Fine-tune Tools

Bộ công cụ sinh dữ liệu và fine-tune GLM-OCR để nhận diện dấu tiếng Việt tốt hơn.

## Tổng quan

| File | Mục đích |
|---|---|
| `vietnamese_hard_words.txt` | Word list 3,544 từ/cụm từ có dấu kép tiếng Việt |
| `generate_vietnamese_dataset_v3.py` | Sinh ảnh OCR + JSON (ShareGPT format) |
| `font_tester_v2.py` | Test font hệ thống có hỗ trợ dấu tiếng Việt |
| `finetune_glm_ocr_vn_1epoch.ipynb` | Notebook fine-tune trên Google Colab (T4) |
| `test_local.py` | Chạy inference local trên 1 hoặc nhiều ảnh |
| `compare_models.py` | So sánh original vs finetuned model trên test set |

## Quick start

```bash
# 1. Gen data
python generate_vietnamese_dataset_v3.py --num_samples 20000 --augment_copies 3 --test_ratio 0.1

# 2. Train trên Colab (upload zip lên Drive trước)
#    Mở finetune_glm_ocr_vn_1epoch.ipynb trên Colab → chạy theo bước

# 3. Test local sau khi tải model về
python test_local.py --model_path ./glm-ocr-vn --image test.png

# 4. So sánh original vs finetuned
python compare_models.py
```

👉 **Hướng dẫn chi tiết từng bước:** xem [`GUIDE.md`](GUIDE.md)
