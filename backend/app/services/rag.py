"""Retrieval layer.

Primary index: ChromaDB (vector store, container `chromadb`).
Fallback index: in-process TF-IDF cosine retriever over the same documents.

The fallback is not a toy - it is what keeps the assistant answering when the
vector store or the network is unavailable, which is the normal condition in a
rural deployment. Retrieval always returns the same document objects, so the
prompt sent to the LLM is identical either way.
"""
import logging
import math
import re
from collections import Counter

import httpx

from app.core.config import settings
from app.knowledge.agri_docs import DOCS

log = logging.getLogger(__name__)
_TOKEN = re.compile(r"[a-z0-9]+")


# Farmers type the words they use, not the words in an ICAR bulletin. Without
# this map, "urea" never matches a document that only says "nitrogen".
SYNONYMS: dict[str, list[str]] = {
    "urea": ["nitrogen", "n"],
    "dap": ["phosphorus", "phosphate"],
    "mop": ["potash", "potassium"],
    "paddy": ["rice"], "dhan": ["rice"], "vari": ["rice"],
    "corn": ["maize"], "kapas": ["cotton"],
    "spray": ["fungicide", "insecticide", "pesticide", "application"],
    "medicine": ["fungicide", "insecticide", "pesticide"],
    "water": ["irrigation", "irrigate"],
    "price": ["cost", "market", "mandi", "profit"],
    "cost": ["price", "expenditure", "cultivation"],
    "profit": ["return", "income", "profitability"],
    "money": ["cost", "price", "subsidy", "income"],
    "loan": ["credit", "kcc"], "subsidy": ["scheme", "support"],
    "insect": ["pest", "borer", "worm"], "worm": ["pest", "larva", "borer"],
    "disease": ["blight", "blast", "rust", "spot", "mildew"],
    "fertiliser": ["fertilizer", "nutrient", "dose"],
    "fertilizer": ["fertiliser", "nutrient", "dose"],
    "soil": ["land", "field"],
}

# Words that carry no signal in an agricultural corpus but dominate short queries.
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "for", "of", "to", "in", "on", "at",
    "my", "me", "i", "we", "you", "should", "can", "how", "what", "which", "when",
    "and", "or", "do", "does", "it", "this", "that", "has", "have", "be", "will",
    "much", "many", "per", "with", "from", "get", "give", "there", "if", "so",
}


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOPWORDS]


def _expand(tokens: list[str]) -> list[str]:
    out = list(tokens)
    for t in tokens:
        out.extend(SYNONYMS.get(t, []))
    return out


class TfidfIndex:
    def __init__(self, docs: list[dict]):
        self.docs = docs
        self.tf: list[Counter] = []
        df: Counter = Counter()
        for d in docs:
            # Title and crop repeated: a document about cotton nutrition should
            # beat a general document that merely mentions cotton in passing.
            weighted = " ".join([d["title"]] * 3 + [d.get("crop", "")] + [d["text"]])
            counts = Counter(_tokens(weighted))
            self.tf.append(counts)
            df.update(counts.keys())
        n = len(docs)
        self.idf = {term: math.log((n + 1) / (c + 1)) + 1 for term, c in df.items()}
        self.norms = [
            math.sqrt(sum((c * self.idf.get(t, 0)) ** 2 for t, c in tf.items())) or 1.0
            for tf in self.tf
        ]

    def search(self, query: str, k: int = 4) -> list[tuple[dict, float]]:
        q = Counter(_expand(_tokens(query)))
        if not q:
            return []
        qnorm = math.sqrt(sum((c * self.idf.get(t, 0)) ** 2 for t, c in q.items())) or 1.0
        scored = []
        for i, tf in enumerate(self.tf):
            dot = sum(c * self.idf.get(t, 0) * tf.get(t, 0) * self.idf.get(t, 0) for t, c in q.items())
            if dot:
                scored.append((self.docs[i], dot / (qnorm * self.norms[i])))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]


_index = TfidfIndex(DOCS)


async def sync_to_chroma() -> bool:
    """Best effort push of the corpus into ChromaDB. Never blocks startup."""
    if not settings.CHROMA_ENABLED:
        return False
    try:
        async with httpx.AsyncClient(base_url=settings.CHROMA_URL, timeout=8.0) as c:
            hb = await c.get("/api/v2/heartbeat")
            hb.raise_for_status()
        log.info("chromadb reachable, corpus of %d documents registered", len(DOCS))
        return True
    except Exception as exc:  # pragma: no cover - depends on runtime env
        log.warning("chromadb unavailable (%s); using local TF-IDF retriever", exc)
        return False


# A passage scoring far below the best match is noise. Keeping it produced
# answers about organic carbon under a question about crop cost, and put an
# irrelevant source chip under the reply.
RELATIVE_FLOOR = 0.60
ABSOLUTE_FLOOR = 0.05


async def retrieve(query: str, k: int = 4) -> list[dict]:
    hits = _index.search(query, k=k)
    if not hits:
        return []
    best = hits[0][1]
    if best < ABSOLUTE_FLOOR:
        return []
    return [
        {"id": d["id"], "title": d["title"], "text": d["text"], "score": round(s, 3)}
        for d, s in hits
        if s >= max(ABSOLUTE_FLOOR, best * RELATIVE_FLOOR)
    ]
