"""
Mix Dataset — gộp 3 source phẳng thành 1 dataset train theo tỉ lệ.
====================================================================
Input:  data/{text_single_line,text_multi_line,table}/<name>.json
Output: data/mixed/<name>/dataset.json (+ meta.json)

Ảnh KHÔNG copy (path relative tới data/<source>/).

Cách dùng:
    # Xem các source đã gen + số mẫu
    python prepare/mix_dataset.py --info

    # Mix theo tỉ lệ (số mẫu lấy từ mỗi source)
    python prepare/mix_dataset.py \\
        --ratio text_single_line:5000 \\
        --ratio text_multi_line:3000 \\
        --ratio table:4000 \\
        --name full

    # Mix shortcut
    python prepare/mix_dataset.py --all --name all_13k        # lấy hết
    python prepare/mix_dataset.py --text --name text_only     # bỏ table
"""

import argparse
import json
import random
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SOURCES = ["text_single_line", "text_multi_line", "table"]
SEED = 42


def discover_sources(base_dir):
    """Scan base_dir xem source nào đã gen."""
    found = []
    for name in SOURCES:
        d = base_dir / name
        jf = d / f"{name}.json"
        if jf.exists():
            samples = json.loads(jf.read_text(encoding="utf-8"))
            found.append({"name": name, "dir": d, "json_file": jf,
                          "count": len(samples)})
    return found


def pick(samples, n, seed):
    """Pick n mẫu từ samples (random sample nếu n < len)."""
    if n >= len(samples):
        return list(samples)
    return random.Random(seed).sample(samples, n)


def main():
    parser = argparse.ArgumentParser(description="Mix 3 source → 1 dataset")
    parser.add_argument("--ratio", action="append", default=[],
                        metavar="NAME:COUNT",
                        help="Source:số mẫu. Vd --ratio text_single_line:5000. Lặp lại.")
    parser.add_argument("--all", action="store_true",
                        help="Lấy tất cả source, full mẫu")
    parser.add_argument("--text", action="store_true",
                        help="Chỉ lấy 2 source text (bỏ table), full mẫu")
    parser.add_argument("--table_ratio", type=int, default=None,
                        help="Khi dùng --text, thêm N mẫu table")
    parser.add_argument("--task", type=str, default=None,
                        choices=["text", "table", "text_single", "text_multi"],
                        help="Chỉ lấy mẫu theo task: text (cả 2 source text), "
                             "table (chỉ table), text_single, text_multi. "
                             "Ghi đè --ratio/--all/--text.")
    parser.add_argument("--name", type=str, default="dataset",
                        help="Tên dataset (folder con dưới data/mixed/)")
    parser.add_argument("--info", action="store_true",
                        help="Hiển thị thông tin source rồi thoát")
    parser.add_argument("--output_dir", type=str, default=str(DATA_DIR / "mixed"))
    parser.add_argument("--sources_dir", type=str, default=str(DATA_DIR),
                        help="Thư mục chứa 3 source folder (mặc định data/)")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    sources = discover_sources(Path(args.sources_dir))

    # ---- INFO mode ----
    if args.info:
        print(f"Các source tại: {DATA_DIR}\n")
        if not sources:
            print("  (chưa có source nào — chạy:")
            print("   python prepare/generate_sources.py)")
            return
        total = 0
        print(f"  {'SOURCE':22s} {'COUNT':>8s}  TASK")
        print(f"  {'-'*22} {'-'*8}  {'-'*10}")
        for s in sources:
            # detect task từ prompt
            data = json.loads(s["json_file"].read_text(encoding="utf-8"))
            task = "table" if "Table" in data[0]["messages"][0]["content"] else "text"
            print(f"  {s['name']:22s} {s['count']:>8,}  {task}")
            total += s["count"]
        print(f"  {'-'*22} {'-'*8}")
        print(f"  {'TỔNG':22s} {total:>8,}")
        return

    if not sources:
        print(f"⚠ Không có source nào tại {DATA_DIR}")
        print(f"  Chạy: python prepare/generate_sources.py")
        return

    src_map = {s["name"]: s for s in sources}

    # ---- Build plan ----
    plan = []   # list of (name, count)
    if args.task:
        task_to_sources = {
            "table": ["table"],
            "text_single": ["text_single_line"],
            "text_multi": ["text_multi_line"],
            "text": ["text_single_line", "text_multi_line"],
        }
        wanted = task_to_sources[args.task]
        for nm in wanted:
            if nm not in src_map:
                print(f"⚠ Source '{nm}' chưa gen (cần cho task '{args.task}').")
                print(f"  Có: {[s['name'] for s in sources]}")
                return
            plan.append((nm, src_map[nm]["count"]))
    elif args.ratio:
        for spec in args.ratio:
            if ":" not in spec:
                print(f"⚠ Sai cú pháp '{spec}'. Dùng NAME:COUNT")
                return
            name, val = spec.rsplit(":", 1)
            try:
                n = int(val)
            except ValueError:
                print(f"⚠ Count phải là số: '{spec}'")
                return
            if name not in src_map:
                print(f"⚠ Source '{name}' chưa gen. Có: {[s['name'] for s in sources]}")
                return
            plan.append((name, n))
    elif args.all:
        for s in sources:
            plan.append((s["name"], s["count"]))
    elif args.text:
        for s in sources:
            data = json.loads(s["json_file"].read_text(encoding="utf-8"))
            is_table = "Table" in data[0]["messages"][0]["content"]
            if not is_table:
                plan.append((s["name"], s["count"]))
            elif args.table_ratio:
                plan.append((s["name"], args.table_ratio))
    else:
        print("ℹ Không chỉ định flag. Lấy tất cả source, full mẫu (như --all).")
        for s in sources:
            plan.append((s["name"], s["count"]))

    # ---- Mix ----
    random.seed(args.seed)
    out_dir = Path(args.output_dir) / args.name
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print(f"  MIX DATASET — {args.name}")
    print("=" * 60)
    print(f"  {'SOURCE':22s} {'HAVE':>8s} {'PICK':>8s}")
    print(f"  {'-'*22} {'-'*8} {'-'*8}")
    dataset = []
    for name, want in plan:
        s = src_map[name]
        data = json.loads(s["json_file"].read_text(encoding="utf-8"))
        picked = pick(data, want, args.seed)
        print(f"  {name:22s} {s['count']:>8,} {len(picked):>8,}")
        task = "table" if name == "table" else "text"
        sub = "text_single_line" if name == "text_single_line" \
            else "text_multi_line" if name == "text_multi_line" \
            else "table"
        for d in picked:
            d["task"] = task       # text | table
            d["source"] = sub       # text_single_line | text_multi_line | table
        dataset.extend(picked)

    random.Random(args.seed).shuffle(dataset)
    n_text = sum(1 for d in dataset if "Text" in d["messages"][0]["content"])
    n_table = sum(1 for d in dataset if "Table" in d["messages"][0]["content"])

    out_path = out_dir / "dataset.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    meta = {
        "name": args.name,
        "total": len(dataset),
        "num_text": n_text,
        "num_table": n_table,
        "seed": args.seed,
        "plan": [{"source": n, "pick": w} for n, w in plan],
        "note": "Ảnh tại data/<source>/images/. Path trong JSON relative tới data/<source>/.",
    }
    with open(out_dir / "meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n  ✅ DONE")
    print(f"  Tổng:     {len(dataset):,}")
    print(f"  Text:     {n_text:,}")
    print(f"  Table:    {n_table:,}")
    print(f"  Output:   {out_path}")


if __name__ == "__main__":
    main()
