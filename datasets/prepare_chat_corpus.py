#!/usr/bin/env python3
"""Preprocess the advisory corpus and measure whether retrieval actually works.

Two jobs.

**Preprocess.** Long documents retrieve badly: a 900-word page about nutrient
management scores against every fertiliser question and buries the specific
answer. This splits documents into passages sized for retrieval, normalises the
units and spellings farmers and bulletins disagree on (kg/ha vs kg per hectare,
fertiliser vs fertilizer), and drops near-duplicate passages.

**Evaluate.** A retriever nobody measured is a retriever nobody can improve.
GOLDEN below is a set of questions in the words a farmer would use, each with the
document that must come back. The script reports hit@1, hit@3 and MRR, and names
every question that failed so you can fix the corpus rather than guess.

Usage
-----
    python datasets/prepare_chat_corpus.py --evaluate
    python datasets/prepare_chat_corpus.py --build --out datasets/corpus/passages.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.knowledge.agri_docs import DOCS  # noqa: E402
from app.services import rag  # noqa: E402

TARGET_WORDS = 110          # long enough to answer, short enough to be specific
OVERLAP_WORDS = 25          # keeps a dose and its timing in the same passage

# Spelling and unit variants that would otherwise split the same concept across
# two vocabulary entries and halve its score.
NORMALISE = [
    (r"\bfertilizer\b", "fertiliser"),
    (r"\bfertilizers\b", "fertilisers"),
    (r"\bkg\s*/\s*ha\b", "kg per hectare"),
    (r"\bkg\s*/\s*acre\b", "kg per acre"),
    (r"\bg\s*/\s*l(itre)?\b", "g per litre"),
    (r"\bml\s*/\s*l(itre)?\b", "ml per litre"),
    (r"\bha\b", "hectare"),
    (r"\bRs\.?\s*", "rupees "),
    (r"\bper cent\b", "percent"),
    (r"\s+", " "),
]

# Questions in farmer vocabulary -> the document id that must be retrieved.
GOLDEN: list[tuple[str, str]] = [
    ("my paddy has grey spots with brown edges what to spray", "rice-blast"),
    ("rice blast control", "rice-blast"),
    ("how much urea for cotton per acre", "cotton-nutrition"),
    ("cotton fertiliser dose", "cotton-nutrition"),
    ("how much urea for paddy", "rice-nutrition"),
    ("when should I irrigate maize", "irrigation-schedule"),
    ("critical stage for watering wheat", "irrigation-schedule"),
    ("which crop costs the most to grow", "cost-of-cultivation"),
    ("cost of chilli cultivation per acre", "cost-of-cultivation"),
    ("which crop gives the most profit", "crop-economics"),
    ("where can I check mandi rate", "market-price-sources"),
    ("how to reduce my input cost", "input-cost-saving"),
    ("PM KISAN eligibility", "schemes-overview"),
    ("crop insurance scheme", "schemes-overview"),
    ("soil pH is too low what to do", "soil-ph"),
    ("organic carbon is low", "soil-organic"),
    ("how to read my soil health card", "npk-interpretation"),
    ("what crop after rice", "crop-rotation"),
    ("fall armyworm in maize", "maize-fall-armyworm"),
    ("pink bollworm control", "cotton-bollworm"),
    ("tomato leaves turning black", "tomato-blight"),
    ("wheat rust treatment", "wheat-rust"),
    ("seed treatment before sowing", "seed-treatment"),
    ("storing grain after harvest", "post-harvest"),
]


def normalise(text: str) -> str:
    out = text
    for pattern, replacement in NORMALISE:
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
    return out.strip()


def sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def chunk(doc: dict) -> list[dict]:
    """Sentence-aware chunks with overlap. Splitting mid-sentence separates a
    dose from its units, which is exactly the error that costs a farmer money."""
    text = normalise(doc["text"])
    sents = sentences(text)
    chunks: list[dict] = []
    current: list[str] = []
    count = 0

    for sentence in sents:
        words = len(sentence.split())
        if count + words > TARGET_WORDS and current:
            chunks.append(" ".join(current))
            tail, tail_words = [], 0
            for s in reversed(current):          # carry the overlap forward
                tail.insert(0, s)
                tail_words += len(s.split())
                if tail_words >= OVERLAP_WORDS:
                    break
            current, count = tail, tail_words
        current.append(sentence)
        count += words

    if current:
        chunks.append(" ".join(current))

    return [
        {
            "id": f"{doc['id']}#{i}",
            "parent_id": doc["id"],
            "title": doc["title"],
            "crop": doc.get("crop", ""),
            "text": c,
            "words": len(c.split()),
        }
        for i, c in enumerate(chunks)
    ]


def dedupe(passages: list[dict], threshold: float = 0.85) -> list[dict]:
    """Drop near-duplicates by token Jaccard. Overlap between chunks is
    deliberate; two passages that are 85% identical are waste."""
    kept: list[dict] = []
    signatures: list[set[str]] = []
    for p in passages:
        tokens = set(p["text"].lower().split())
        if any(
            len(tokens & sig) / max(1, len(tokens | sig)) >= threshold
            for sig in signatures
        ):
            continue
        kept.append(p)
        signatures.append(tokens)
    return kept


def build(out_path: Path) -> dict:
    passages: list[dict] = []
    for doc in DOCS:
        passages.extend(chunk(doc))
    before = len(passages)
    passages = dedupe(passages)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(passages, indent=2, ensure_ascii=False))

    lengths = [p["words"] for p in passages]
    return {
        "documents": len(DOCS),
        "passages": len(passages),
        "removed_as_duplicates": before - len(passages),
        "words_min": min(lengths),
        "words_median": sorted(lengths)[len(lengths) // 2],
        "words_max": max(lengths),
        "output": str(out_path),
    }


def evaluate(k: int = 3) -> dict:
    """hit@1, hit@3 and MRR against the golden set, plus the failures by name."""
    import asyncio

    hit1 = hit_k = 0
    reciprocal = 0.0
    failures: list[dict] = []

    async def run() -> None:
        nonlocal hit1, hit_k, reciprocal
        for question, expected in GOLDEN:
            hits = await rag.retrieve(question, k=k)
            ids = [h["id"] for h in hits]
            if ids and ids[0] == expected:
                hit1 += 1
            if expected in ids:
                hit_k += 1
                reciprocal += 1 / (ids.index(expected) + 1)
            else:
                failures.append(
                    {"question": question, "expected": expected,
                     "got": [f"{h['id']} ({h['score']})" for h in hits] or ["nothing"]}
                )

    asyncio.run(run())
    n = len(GOLDEN)
    return {
        "questions": n,
        "hit@1": round(hit1 / n, 3),
        f"hit@{k}": round(hit_k / n, 3),
        "mrr": round(reciprocal / n, 3),
        "failures": failures,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true", help="write preprocessed passages")
    ap.add_argument("--evaluate", action="store_true", help="score retrieval against the golden set")
    ap.add_argument("--out", type=Path, default=ROOT / "datasets" / "corpus" / "passages.json")
    ap.add_argument("--k", type=int, default=3)
    args = ap.parse_args()

    if not args.build and not args.evaluate:
        args.build = args.evaluate = True

    if args.build:
        stats = build(args.out)
        print("Corpus preprocessing")
        for key, value in stats.items():
            print(f"  {key:24} {value}")
        print()

    if args.evaluate:
        result = evaluate(args.k)
        print("Retrieval quality")
        for key in ("questions", "hit@1", f"hit@{args.k}", "mrr"):
            print(f"  {key:24} {result[key]}")
        if result["failures"]:
            print(f"\n  {len(result['failures'])} question(s) missed:")
            for f in result["failures"]:
                print(f"    {f['question']!r}")
                print(f"      expected {f['expected']}, got {', '.join(f['got'])}")
            print("\n  Fix by adding the missing wording to the document, or a synonym")
            print("  to SYNONYMS in backend/app/services/rag.py.")
        else:
            print("\n  Every golden question retrieved its document.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
