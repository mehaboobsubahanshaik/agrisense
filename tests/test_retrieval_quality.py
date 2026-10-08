"""Retrieval quality gate.

The golden set lives in datasets/prepare_chat_corpus.py so the same questions
score the retriever in CI and on a developer's machine. If a corpus edit drops
hit@3 below the floor, the build fails rather than the farmer discovering it.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "datasets"))

from prepare_chat_corpus import GOLDEN, build, chunk, evaluate, normalise  # noqa: E402


def test_retrieval_meets_the_quality_floor():
    result = evaluate(k=3)
    assert result["hit@3"] >= 0.95, result["failures"]
    assert result["hit@1"] >= 0.75, result["failures"]
    assert result["mrr"] >= 0.85, result["failures"]


def test_every_golden_question_has_a_real_document():
    from app.knowledge.agri_docs import DOCS

    ids = {d["id"] for d in DOCS}
    missing = sorted({expected for _, expected in GOLDEN if expected not in ids})
    assert not missing, f"golden set points at documents that do not exist: {missing}"


def test_normalisation_unifies_units_and_spelling():
    assert "fertiliser" in normalise("Fertilizer dose")
    assert "kg per hectare" in normalise("120 kg/ha of N")
    assert "ml per litre" in normalise("1.5 ml/l")
    assert "rupees 6000" in normalise("Rs. 6000")


def test_chunks_never_split_a_sentence():
    doc = {"id": "t", "title": "T", "crop": "rice",
           "text": "First sentence here. Second sentence with a dose of 120 kg. Third one."}
    for c in chunk(doc):
        assert c["text"].endswith((".", "!", "?")), c["text"]


def test_build_writes_passages_within_size_bounds(tmp_path):
    stats = build(tmp_path / "passages.json")
    assert stats["passages"] >= stats["documents"]
    assert stats["words_max"] <= 200, "a passage this long retrieves against everything"
