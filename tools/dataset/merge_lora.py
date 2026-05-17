"""
Merge LoRA adapter vào base model — chạy local.
=============================================
Cách dùng:
    # 1. Tải checkpoint mới nhất từ Google Drive (folder checkpoint-XXXXX)
    #    Cần 2 file: adapter_model.safetensors + adapter_config.json
    #
    # 2. Chạy merge:
    python merge_lora.py --adapter_path ./checkpoint-11241 --output_dir ./glm-ocr-vn-merged
    #
    # 3. Base model tự download từ HuggingFace lần đầu, cache lại sau đó

Yêu cầu:
    pip install transformers peft torch accelerate safetensors
"""

import argparse
import os

import torch
from peft import PeftModel
from transformers import AutoModelForImageTextToText, AutoProcessor


def merge(adapter_path: str, output_dir: str):
    base_model = "zai-org/GLM-OCR"

    print(f"Loading base model: {base_model}")
    model = AutoModelForImageTextToText.from_pretrained(
        base_model,
        trust_remote_code=True,
        torch_dtype=torch.bfloat16,
        device_map="cpu",
    )

    print(f"Loading adapter: {adapter_path}")
    model = PeftModel.from_pretrained(model, adapter_path)

    print("Merging...")
    model = model.merge_and_unload()

    os.makedirs(output_dir, exist_ok=True)
    print(f"Saving to: {output_dir}")
    model.save_pretrained(output_dir, safe_serialization=True)

    print("Saving processor/tokenizer...")
    processor = AutoProcessor.from_pretrained(base_model, trust_remote_code=True)
    processor.save_pretrained(output_dir)

    # Verify
    size_mb = os.path.getsize(os.path.join(output_dir, "model.safetensors")) / 1e6
    print(f"Done. model.safetensors = {size_mb:.0f} MB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge LoRA adapter into base model")
    parser.add_argument(
        "--adapter_path", type=str, required=True,
        help="Path to checkpoint folder (contains adapter_model.safetensors)"
    )
    parser.add_argument(
        "--output_dir", type=str, default="./glm-ocr-vn-merged",
        help="Output directory for merged model"
    )
    args = parser.parse_args()
    merge(args.adapter_path, args.output_dir)
