"""So sánh Original GLM-OCR vs Finetuned trên test set."""
import argparse, os, glob, random
from pathlib import Path
from transformers import AutoProcessor, AutoModelForImageTextToText
import torch, json, editdistance

parser = argparse.ArgumentParser(description="So sánh Original vs Finetuned GLM-OCR")
parser.add_argument("--ft_path", type=str, default="./glm-ocr-vn", help="Đường dẫn model finetuned")
parser.add_argument("--test_json", type=str, default="./vietnamese_ocr/vietnamese_ocr_test.json", help="Test set JSON")
parser.add_argument("--n", type=int, default=0, help="Số ảnh test (0 = tất cả)")
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

all_items = list(lookup.items())
if args.n > 0:
    random.seed(42)
    all_items = random.sample(all_items, min(args.n, len(all_items)))
test_files = [fname for fname, _ in all_items]
base = os.path.join(os.path.dirname(args.test_json), "images")
print(f"Testing trên {len(test_files)}/{len(lookup)} ảnh...\n")


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

# Nhóm dấu tiếng Việt cho diacritic accuracy
DIACRITIC_GROUPS = {
    "ă (ắằẳẵặ)": set("ăắằẳẵặ"),
    "â (ấầẩẫậ)": set("âấầẩẫậ"),
    "ê (ếềểễệ)": set("êếềểễệ"),
    "ô (ốồổỗộ)": set("ôốồổỗộ"),
    "ơ (ớờởỡợ)": set("ơớờởỡợ"),
    "ư (ứừửữự)": set("ưứừửữự"),
    "đ": set("đĐ"),
}
d_stats = {g: {"correct": 0, "total": 0} for g in DIACRITIC_GROUPS}


def align_chars(gt, pred):
    m, n = len(gt), len(pred)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if gt[i - 1] == pred[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    pairs = []
    i, j = m, n
    while i > 0 or j > 0:
        if i > 0 and j > 0 and gt[i - 1] == pred[j - 1]:
            pairs.append((gt[i - 1], pred[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and dp[i][j] == dp[i - 1][j - 1] + 1:
            pairs.append((gt[i - 1], pred[j - 1]))
            i -= 1
            j -= 1
        elif i > 0 and dp[i][j] == dp[i - 1][j] + 1:
            pairs.append((gt[i - 1], ""))
            i -= 1
        else:
            pairs.append(("", pred[j - 1]))
            j -= 1
    pairs.reverse()
    return pairs

for i, fname in enumerate(test_files):
    img_path = os.path.join(base, fname)
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

    # Diacritic accuracy (chỉ trên finetuned, using optimal alignment)
    for g, chars in DIACRITIC_GROUPS.items():
        for c_gt, c_pred in align_chars(gt, pred_ft):
            if c_gt in chars:
                d_stats[g]["total"] += 1
                if c_gt == c_pred:
                    d_stats[g]["correct"] += 1

    if (i + 1) % 25 == 0 or (i + 1) == len(test_files):
        print(f"  [{i+1}/{len(test_files)}]")

    show_detail = len(test_files) <= 10
    if show_detail:
        print(f"━━━ {fname} ━━━")
        print(f"  GT:    {gt}")
        print(f"  Orig:  {pred_orig}")
        print(f"  FT:    {pred_ft}")

    orig_diffs = [(a, b) for a, b in zip(gt_w, pred_orig.split()) if a != b]
    ft_diffs = [(a, b) for a, b in zip(gt_w, pred_ft.split()) if a != b]
    if show_detail:
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
print()

# Diacritic accuracy (finetuned only)
total_dc = sum(d["correct"] for d in d_stats.values())
total_dt = sum(d["total"] for d in d_stats.values())
if total_dt > 0:
    print(f"  {'Diacritic Acc (FT)':<18} {total_dc / total_dt * 100:>10.1f}%  ({total_dc}/{total_dt})")
    print()
    print(f"  {'Nhóm dấu':<20} {'Accuracy':>10} {'Chi tiết':>12}")
    print(f"  {'─'*20} {'─'*10} {'─'*12}")
    for g in DIACRITIC_GROUPS:
        t, c = d_stats[g]["total"], d_stats[g]["correct"]
        acc = c / max(t, 1) * 100
        print(f"  {g:<20} {acc:>9.1f}%  ({c}/{t})")
print("=" * 60)
