#!/usr/bin/env python3
"""Turn raw downloaded crop-disease datasets into a clean YOLO training set.

Why this exists: PlantVillage is 54k lab photographs of single leaves on a grey
background. A model trained on it alone reports 99% and then fails on the first
photo a farmer takes at 6pm in a field. This script forces the mix, removes the
duplicates that inflate validation scores, and refuses to write a split where
the same image appears on both sides of the wall.

Usage
-----
    python datasets/prepare_disease_dataset.py \
        --raw datasets/raw \
        --out datasets/crop-disease \
        --val 0.15 --test 0.10

Expected input layout (one folder per class, any nesting depth):

    datasets/raw/
      plantvillage/Tomato___Late_blight/*.jpg
      plantdoc/Tomato leaf late blight/*.jpg
      my_field_photos/rice_blast/*.jpg

Folder names are matched against CLASS_PATTERNS below, so the messy and
inconsistent names the public datasets ship with map onto our ten classes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

# The ten classes the backend already knows how to write a remedy card for.
CLASSES = [
    "rice_blast",
    "bacterial_leaf_blight",
    "leaf_spot",
    "leaf_rust",
    "powdery_mildew",
    "late_blight",
    "early_blight",
    "pest_damage",
    "nutrient_deficiency",
    "healthy",
]

# Ordered: first match wins, so put the specific patterns above the general ones.
CLASS_PATTERNS: list[tuple[str, str]] = [
    (r"blast", "rice_blast"),
    (r"bacterial.*(blight|spot)|xanthomonas", "bacterial_leaf_blight"),
    (r"late.?blight|phytophthora", "late_blight"),
    (r"early.?blight|alternaria", "early_blight"),
    (r"rust|puccinia", "leaf_rust"),
    (r"powder|mildew|oidium", "powdery_mildew"),
    (r"(leaf.?spot|cercospora|septoria|brown.?spot|gray.?spot|grey.?spot)", "leaf_spot"),
    (r"(mite|borer|worm|armyworm|aphid|thrip|hopper|pest|insect|bollworm)", "pest_damage"),
    (r"(deficien|chloros|yellow|nitrogen|potassium|magnesium)", "nutrient_deficiency"),
    (r"healthy|normal", "healthy"),
]

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
MIN_BYTES = 4096          # anything smaller is a thumbnail or a truncated download
MIN_SIDE = 96             # below this a lesion is a few pixels and teaches nothing

# Datasets shot in a lab. Tracked separately so the report can tell you what
# fraction of your training data does not look like a farmer's photo.
LAB_SOURCES = {"plantvillage", "plant_village", "pv"}


def classify(folder_name: str) -> str | None:
    name = folder_name.lower().replace("_", " ").replace("-", " ")
    for pattern, label in CLASS_PATTERNS:
        if re.search(pattern, name):
            return label
    return None


def file_hash(path: Path) -> str:
    """Hash of the file contents. Exact-duplicate images across the public
    datasets are common, and if one lands in train and its twin in val, the
    reported accuracy is a lie."""
    h = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def image_size(path: Path) -> tuple[int, int] | None:
    try:
        from PIL import Image

        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def source_of(path: Path, raw_root: Path) -> str:
    try:
        return path.relative_to(raw_root).parts[0].lower()
    except ValueError:
        return "unknown"


def collect(raw_root: Path) -> tuple[list[dict], dict]:
    """Walk the raw tree, label by folder name, drop what is unusable."""
    kept: list[dict] = []
    seen: dict[str, Path] = {}
    stats = Counter()
    unmatched: Counter = Counter()

    for path in sorted(raw_root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXT:
            continue
        stats["seen"] += 1

        label = None
        for parent in path.parents:                 # nearest labelled folder wins
            if parent == raw_root:
                break
            label = classify(parent.name)
            if label:
                break
        if not label:
            stats["unlabelled"] += 1
            unmatched[path.parent.name] += 1
            continue

        if path.stat().st_size < MIN_BYTES:
            stats["too_small_bytes"] += 1
            continue

        size = image_size(path)
        if size is None:
            stats["unreadable"] += 1
            continue
        if min(size) < MIN_SIDE:
            stats["too_small_pixels"] += 1
            continue

        digest = file_hash(path)
        if digest in seen:
            stats["duplicate"] += 1
            continue
        seen[digest] = path

        src = source_of(path, raw_root)
        kept.append(
            {
                "path": path,
                "label": label,
                "hash": digest,
                "source": src,
                "field": src not in LAB_SOURCES,
                "width": size[0],
                "height": size[1],
            }
        )
        stats["kept"] += 1

    return kept, {"counts": dict(stats), "unmatched_folders": dict(unmatched.most_common(20))}


def split(items: list[dict], val: float, test: float, seed: int = 42) -> dict[str, list[dict]]:
    """Stratified by class AND by source.

    Splitting by class alone lets every field photo land in train and every lab
    photo in val, which produces a validation score that means nothing. Grouping
    on (label, source) keeps both distributions the same on each side.
    """
    rng = random.Random(seed)
    buckets: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in items:
        buckets[(item["label"], item["source"])].append(item)

    out: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    for group in buckets.values():
        rng.shuffle(group)
        n = len(group)
        n_val = max(1, int(n * val)) if n >= 5 else 0
        n_test = max(1, int(n * test)) if n >= 10 else 0
        out["val"].extend(group[:n_val])
        out["test"].extend(group[n_val:n_val + n_test])
        out["train"].extend(group[n_val + n_test:])
    for key in out:
        rng.shuffle(out[key])
    return out


def write(splits: dict[str, list[dict]], out_root: Path, whole_image_box: bool) -> None:
    for name, items in splits.items():
        img_dir = out_root / "images" / name
        lbl_dir = out_root / "labels" / name
        img_dir.mkdir(parents=True, exist_ok=True)
        lbl_dir.mkdir(parents=True, exist_ok=True)

        for i, item in enumerate(items):
            stem = f"{item['label']}_{item['source']}_{i:06d}"
            dest = img_dir / (stem + item["path"].suffix.lower())
            shutil.copy2(item["path"], dest)

            if whole_image_box:
                # Classification-style folders have no boxes. A centred box
                # covering 90% of the frame is the standard way to train a
                # detector on them - honest, and clearly marked in the report.
                cls = CLASSES.index(item["label"])
                (lbl_dir / (stem + ".txt")).write_text(f"{cls} 0.5 0.5 0.9 0.9\n")
            else:
                src_label = item["path"].with_suffix(".txt")
                if src_label.exists():
                    shutil.copy2(src_label, lbl_dir / (stem + ".txt"))


def write_yaml(out_root: Path) -> None:
    names = "\n".join(f"  {i}: {c}" for i, c in enumerate(CLASSES))
    (out_root / "data.yaml").write_text(
        f"path: {out_root.as_posix()}\n"
        "train: images/train\n"
        "val: images/val\n"
        "test: images/test\n\n"
        f"names:\n{names}\n"
    )


def report(splits: dict[str, list[dict]], collect_stats: dict, out_root: Path) -> dict:
    per_split = {}
    for name, items in splits.items():
        by_class = Counter(i["label"] for i in items)
        field = sum(1 for i in items if i["field"])
        per_split[name] = {
            "total": len(items),
            "field_images": field,
            "lab_images": len(items) - field,
            "field_fraction": round(field / len(items), 3) if items else 0,
            "by_class": dict(by_class),
        }

    warnings: list[str] = []
    train = per_split.get("train", {})
    if train.get("field_fraction", 0) < 0.2:
        warnings.append(
            "Under 20% of training images are field photos. Expect the model to score "
            "well in validation and badly on a phone camera. Add PlantDoc or your own photos."
        )
    counts = train.get("by_class", {})
    if counts:
        biggest, smallest = max(counts.values()), min(counts.values())
        if smallest and biggest / smallest > 10:
            warnings.append(
                f"Class imbalance {biggest}:{smallest}. Use class weights, oversample the rare "
                "classes, or report per-class recall rather than overall accuracy."
            )
    missing = [c for c in CLASSES if c not in counts]
    if missing:
        warnings.append(f"No training images for: {', '.join(missing)}. The model cannot learn them.")

    doc = {"collection": collect_stats, "splits": per_split, "warnings": warnings}
    (out_root / "dataset_report.json").write_text(json.dumps(doc, indent=2))
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default="datasets/raw", type=Path)
    ap.add_argument("--out", default="datasets/crop-disease", type=Path)
    ap.add_argument("--val", default=0.15, type=float)
    ap.add_argument("--test", default=0.10, type=float)
    ap.add_argument("--seed", default=42, type=int)
    ap.add_argument("--boxes", choices=["whole-image", "existing"], default="whole-image",
                    help="whole-image: synthesise a centred box for classification folders")
    args = ap.parse_args()

    if not args.raw.exists():
        print(f"No raw data at {args.raw}. See docs/MODEL_TRAINING.md for the downloads.", file=sys.stderr)
        return 1

    print(f"Scanning {args.raw} ...")
    items, stats = collect(args.raw)
    if not items:
        print("Nothing usable found. Check that folder names describe the disease.", file=sys.stderr)
        print(f"Unmatched folders: {stats['unmatched_folders']}", file=sys.stderr)
        return 1
    print(f"  kept {len(items)} images; {stats['counts']}")

    if args.out.exists():
        shutil.rmtree(args.out)
    splits = split(items, args.val, args.test, args.seed)
    write(splits, args.out, whole_image_box=(args.boxes == "whole-image"))
    write_yaml(args.out)
    doc = report(splits, stats, args.out)

    for name, info in doc["splits"].items():
        print(f"  {name:5} {info['total']:6}  field {info['field_fraction']:.0%}")
    for w in doc["warnings"]:
        print(f"  WARNING: {w}")

    print(f"\nWrote {args.out}/data.yaml and dataset_report.json")
    print("Train with:")
    print(f"  yolo detect train model=yolo11s.pt data={args.out}/data.yaml epochs=120 imgsz=640")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
