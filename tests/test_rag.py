import asyncio

from app.services import rag


def test_retriever_finds_the_right_document():
    hits = asyncio.run(rag.retrieve("grey spindle lesions on paddy leaves", k=3))
    assert hits, "retrieval returned nothing"
    assert any("blast" in h["id"] for h in hits[:2])


def test_retriever_handles_fertiliser_questions():
    hits = asyncio.run(rag.retrieve("how much urea for paddy per hectare", k=3))
    assert any(h["id"] in ("rice-nutrition", "npk-interpretation") for h in hits)


def test_retriever_returns_nothing_for_off_topic_gibberish():
    hits = asyncio.run(rag.retrieve("zzzz qqqq xxxx", k=3))
    assert hits == []


def test_weak_matches_are_not_cited():
    """A passage far below the top score used to appear as a source chip under an
    unrelated answer - organic carbon cited under a question about crop cost."""
    import asyncio
    hits = asyncio.run(rag.retrieve("cost of chilli cultivation per acre", k=4))
    assert hits, "cost question should retrieve something"
    titles = " ".join(h["title"].lower() for h in hits)
    assert "organic carbon" not in titles
    best = hits[0]["score"]
    assert all(h["score"] >= best * 0.60 for h in hits)


def test_cost_questions_reach_the_economics_documents():
    import asyncio
    hits = asyncio.run(rag.retrieve("which crop has the highest cost", k=3))
    assert any("cost" in h["title"].lower() or "profitab" in h["title"].lower() for h in hits)


def test_farmer_vocabulary_reaches_the_right_document():
    """Farmers say urea, not nitrogen; paddy, not rice. Retrieval has to bridge that."""
    import asyncio
    cases = [
        ("how much urea for cotton", "cotton nutrient"),
        ("rice blast grey spots", "rice blast"),
        ("PM KISAN scheme eligibility", "government support"),
        ("where can I check mandi price", "crop prices"),
    ]
    for query, expected in cases:
        hits = asyncio.run(rag.retrieve(query, k=3))
        titles = " ".join(h["title"].lower() for h in hits)
        assert expected in titles, f"{query!r} -> {titles}"
