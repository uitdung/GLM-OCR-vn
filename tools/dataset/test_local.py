"""
Test GLM-OCR Vietnamese locally — chạy inference trên ảnh bất kỳ.
=============================================
Cách dùng:
    # Test 1 ảnh
    python test_local.py --model_path ./glm-ocr-vn-merged --image test.png

    # Test nhiều ảnh
    python test_local.py --model_path ./glm-ocr-vn-merged --image img1.png img2.png img3.png

    # Test toàn bộ ảnh trong thư mục
    python test_local.py --model_path ./glm-ocr-vn-merged --image ./test_images/

    # Chỉ định task
    python test_local.py --model_path ./glm-ocr-vn-merged --image test.png --task "Formula Recognition:"

Yêu cầu:
    pip install transformers torch pillow
"""

import argparse
import os
import glob
import sys
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForImageTextToText


TASKS = {
    "text": "Text Recognition:",
    "table": "Table Recognition:",
    "formula": "Formula Recognition:",
}


def load_model(model_path: str):
    """Load model và processor."""
    print(f"Loading model từ {model_path}...")
    processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)
    model = AutoModelForImageTextToText.from_pretrained(
        model_path,
        trust_remote_code=True,
        torch_dtype="auto",
        device_map="auto",
    )
    print(f"✓ Model loaded trên {model.device}")
    return processor, model


def inference(processor, model, image_path: str, task: str = "Text Recognition:") -> str:
    """Chạy OCR trên 1 ảnh."""
    img = Image.open(image_path).convert("RGB")

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "url": image_path},
                {"type": "text", "text": task},
            ],
        }
    ]

    inputs = processor.apply_chat_template(
        messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)

    # Loại bỏ token_type_ids nếu có
    inputs.pop("token_type_ids", None)

    generated_ids = model.generate(**inputs, max_new_tokens=512, do_sample=False)

    result = processor.decode(
        generated_ids[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True,
    )
    return result.strip()


def collect_images(paths: list[str]) -> list[str]:
    """Thu thập danh sách ảnh từ path (file hoặc thư mục)."""
    images = []
    for p in paths:
        p = Path(p)
        if p.is_file():
            images.append(str(p))
        elif p.is_dir():
            for ext in ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.webp", "*.tiff"):
                images.extend(glob.glob(str(p / ext)))
        else:
            # Có thể là glob pattern
            images.extend(glob.glob(str(p)))
    return sorted(set(images))


def main():
    parser = argparse.ArgumentParser(description="Test GLM-OCR Vietnamese locally")
    parser.add_argument(
        "--model_path", type=str, required=True,
        help="Đường dẫn đến model đã merge (local path)"
    )
    parser.add_argument(
        "--image", type=str, nargs="+", required=True,
        help="Đường dẫn ảnh hoặc thư mục ảnh"
    )
    parser.add_argument(
        "--task", type=str, default="text",
        choices=list(TASKS.keys()),
        help="Loại task OCR (default: text)"
    )
    parser.add_argument(
        "--show_image", action="store_true",
        help="Hiển thị ảnh (cần GUI)"
    )
    args = parser.parse_args()

    # Thu thập ảnh
    images = collect_images(args.image)
    if not images:
        print(f"❌ Không tìm thấy ảnh nào tại: {args.image}")
        sys.exit(1)

    print(f"Tìm thấy {len(images)} ảnh\n")

    # Load model
    processor, model = load_model(args.model_path)
    task_prompt = TASKS[args.task]

    # Chạy inference
    for i, img_path in enumerate(images, 1):
        print(f"{'='*60}")
        print(f"📷 [{i}/{len(images)}] {Path(img_path).name}")
        print(f"{'='*60}")

        if args.show_image:
            try:
                Image.open(img_path).show()
            except Exception:
                pass

        try:
            result = inference(processor, model, img_path, task_prompt)
            print(f"📝 Kết quả:\n{result}\n")
        except Exception as e:
            print(f"❌ Lỗi: {e}\n")


if __name__ == "__main__":
    main()
