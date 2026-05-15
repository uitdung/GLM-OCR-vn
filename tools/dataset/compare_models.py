"""So sánh Original GLM-OCR vs Finetuned trên test set."""
import argparse, os, glob
from pathlib import Path
from transformers import AutoProcessor, AutoModelForImageTextToText
import torch, json, editdistance

parser = argparse.ArgumentParser(description="So sánh Original vs Finetuned GLM-OCR")
parser.add_argument("--ft_path", type=str, default="./glm-ocr-vn", help="Đường dẫn model finetuned")
parser.add_argument("--test_json", type=str, default="./vietnamese_ocr/vietnamese_ocr_test.json", help="Test set JSON")
parser.add_argument("--n", type=int, default=5, help="Số ảnh test")
args = parser.parse_args()

# Load models
print("Loading ORIGINAL model (zai-org/GLM-OCR)...")
processor_orig = AutoProcessor.from_pretrained("zai-org/GLM-OCR", trust_remote_code=True)
model_orig = AutoModelForImageTextToText.from_pretrained(
    "zai-org/GLM-OCR", trust_remote_code=True, torch_dtype="auto", device_map="auto"
)
print("OK")

ft_path = os.path.abspath(args.ft_path)
print(f"Loading FINETUNED model ({ft_path})...")
processor_ft = AutoProcessor.from_pretrained(ft_path, trust_remote_code=True)
model_ft = AutoModelForImageTextToText.from_pretrained(
    ft_path, trust_remote_code=True, torch_dtype="auto", device_map="auto"
)
print("OK\n")

# Load test set
with open(args.test_json, "r", encoding="utf-8") as f:
    data = json.load(f)
lookup = {item["images"][0].split("/")[-1]: item["messages"][1]["content"] for item in data}

# Lấy N ảnh test ngẫu nhiên
import random
random.seed(42)
sampled = random.sample(list(lookup.items()), min(args.n, len(lookup)))
test_files = [fname for fname, _ in sampled]
base = os.path.join(os.path.dirname(args.test_json), "images")


def run_inference(processor, model, img_path):
    messages = [{"role": "user", "content": [
        {"type": "image", "url": img_path},
        {"type": "text", "text": "Text Recognition:"},
    ]}]
    inputs = processor.apply_chat_template(
        messages, tokenize=True, add_generation_prompt=True,
        return_dict=True, return_tensors="pt",
    ).to(model.device)
    inputs.pop("token_type_ids", None)
    ids = model.generate(**inputs, max_new_tokens=512, do_sample=False)
    return processor.decode(ids[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()


# Compare
stats = {
    "orig_w": 0, "ft_w": 0, "orig_w_ok": 0, "ft_w_ok": 0,
    "orig_c": 0, "ft_c": 0, "orig_c_ok": 0, "ft_c_ok": 0,
}

for fname in test_files:
    img_path = f"{base}/{fname}"
    gt = lookup[fname]

    pred_orig = run_inference(processor_orig, model_orig, img_path)
    pred_ft = run_inference(processor_ft, model_ft, img_path)

    gt_w = gt.split()
    orig_wa = sum(1 for a, b in zip(gt_w, pred_orig.split()) if a == b)
    ft_wa = sum(1 for a, b in zip(gt_w, pred_ft.split()) if a == b)

    stats["orig_w"] += len(gt_w); stats["ft_w"] += len(gt_w)
    stats["orig_w_ok"] += orig_wa; stats["ft_w_ok"] += ft_wa
    stats["orig_c"] += len(gt); stats["ft_c"] += len(gt)
    stats["orig_c_ok"] += len(gt) - editdistance.eval(pred_orig, gt)
    stats["ft_c_ok"] += len(gt) - editdistance.eval(pred_ft, gt)

    print(f"━━━ {fname} ━━━")
    print(f"  GT:    {gt}")
    print(f"  Orig:  {pred_orig}")
    print(f"  FT:    {pred_ft}")

    orig_diffs = [(a, b) for a, b in zip(gt_w, pred_orig.split()) if a != b]
    ft_diffs = [(a, b) for a, b in zip(gt_w, pred_ft.split()) if a != b]
    if orig_diffs:
        print(f"  ❌ Orig sai: {orig_diffs}")
    if ft_diffs:
        print(f"  ❌ FT sai:   {ft_diffs}")
    if not orig_diffs and not ft_diffs:
        print(f"  ✅ Cả hai perfect!")
    print()

# Summary
print("=" * 60)
print(f"  {'Metric':<18} {'Original':>12} {'Finetuned':>12} {'Δ':>8}")
print("=" * 60)
orig_wa_pct = stats["orig_w_ok"] / max(stats["orig_w"], 1) * 100
ft_wa_pct = stats["ft_w_ok"] / max(stats["ft_w"], 1) * 100
orig_ca_pct = stats["orig_c_ok"] / max(stats["orig_c"], 1) * 100
ft_ca_pct = stats["ft_c_ok"] / max(stats["ft_c"], 1) * 100
print(f"  {'Word Acc':<18} {orig_wa_pct:>10.1f}% {ft_wa_pct:>10.1f}% {ft_wa_pct - orig_wa_pct:>+7.1f}%")
print(f"  {'Char Acc':<18} {orig_ca_pct:>10.1f}% {ft_ca_pct:>10.1f}% {ft_ca_pct - orig_ca_pct:>+7.1f}%")
print("=" * 60)
