"""Gemini client plus a deterministic offline advisor.

Grounding rule: the model may only answer from the retrieved agricultural
passages plus the farm context we pass in. With no API key the same passages are
turned into a readable answer locally, so a demo without internet still gives
correct agronomic advice.

Language rule: the answer must come back in the farmer's own script, not
romanised. We ask for it explicitly and then verify - see localization.is_native_script.

Speed: identical questions are cached in Redis for six hours, passages are
trimmed before they reach the prompt, and the whole call has a hard timeout.
"""
import asyncio
import hashlib
import json
import logging

import httpx

from app.core.config import settings
from app.core.redis_client import get_redis
from app.knowledge import localization as L
from app.services import rag

log = logging.getLogger(__name__)

LANG_NAME = {code: m["name"] for code, m in L.LANGUAGES.items()}

CACHE_TTL = 6 * 3600
PASSAGE_CHARS = 900          # trimmed context keeps the prompt small and the reply fast
GEMINI_TIMEOUT = 25.0

SYSTEM = """You are AgriSense AI, an agricultural advisor for Indian smallholder farmers.

LANGUAGE - this is the most important rule:
- Write the ENTIRE answer in {language} using {script} script.
- Do NOT romanise. Do NOT reply in English. Do NOT add an English translation.
- Keep pesticide brand names, chemical names and numbers in their original form
  (for example Tricyclazole 75 WP, 0.6 g/litre) inside the {script} sentence.

CONTENT:
- Answer only from the reference passages, the farm context and any image or file
  analysis given below. If they do not cover the question, say so plainly and name
  the officer or soil test that would answer it.
- Give quantities the farmer can act on: product, dose per litre or per acre, timing.
- Short sentences. No jargon. No markdown tables. Under 180 words.
- When you name a chemical, add one line on protective gear and the pre-harvest interval.
"""

RETRY_NUDGE = """
Your previous answer was not in {script} script. Rewrite it completely in
{language} using {script} script. Output only the rewritten answer.
"""


# --------------------------------------------------------------------------
# offline composer
# --------------------------------------------------------------------------
def _fallback(passages: list[dict], language: str, extra: str = "") -> str:
    """Native-script skeleton around English reference detail.

    We deliberately do not machine translate the passage text without a model -
    a hallucinated Telugu dose is worse than a correct English one. So the
    structure, headings and safety line are localised and the detail is labelled.
    """
    blocks: list[str] = []
    if extra:
        blocks.append(extra)

    if not passages:
        blocks.append(L.t("no_answer", language))
        return "\n\n".join(blocks)

    blocks.append(L.t("ref_intro", language))
    blocks.append(L.t("safety", language))

    if language != "en":
        blocks.append(f"**{L.t('english_detail', language)}**")
    for p in passages[:2]:
        sentences = [s.strip() for s in p["text"].split(". ") if s.strip()]
        body = ". ".join(sentences[:4]).rstrip(".") + "."
        blocks.append(f"**{p['title']}** — {body}")

    if language != "en":
        blocks.append(f"_{L.t('offline_note', language)}_")
    return "\n\n".join(blocks)


# --------------------------------------------------------------------------
# Gemini
# --------------------------------------------------------------------------
# Indic scripts cost roughly three times more tokens per character than English,
# and gemini-2.5 spends part of the same budget on internal thinking. At 800
# tokens a Telugu answer was being cut off mid-sentence, so: no thinking budget
# for what is a short grounded rewrite, and a much larger output ceiling.
MAX_OUTPUT_TOKENS = 2048


async def _gemini(prompt: str, client: httpx.AsyncClient) -> str:
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.GEMINI_MODEL}:generateContent"
    )
    r = await client.post(
        url,
        headers={"x-goog-api-key": settings.GEMINI_API_KEY, "Content-Type": "application/json"},
        json={
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": MAX_OUTPUT_TOKENS,
                # 2.5-series only; harmlessly ignored by older models.
                "thinkingConfig": {"thinkingBudget": 0},
            },
        },
    )
    r.raise_for_status()
    data = r.json()
    candidate = data["candidates"][0]
    text = "".join(
        part.get("text", "") for part in candidate.get("content", {}).get("parts", [])
    ).strip()

    if candidate.get("finishReason") == "MAX_TOKENS":
        log.warning("gemini hit the output ceiling; answer may be clipped")
        # Trim back to the last complete sentence rather than showing a half word.
        for end in ("\u0964", ".", "!", "?"):      # danda for Indic scripts
            cut = text.rfind(end)
            if cut > len(text) * 0.5:
                return text[: cut + 1]
    return text


def _cache_key(question: str, language: str, context: str, extra: str) -> str:
    # The engine is part of the key. Without this, answers composed offline stay
    # cached for six hours after an API key is added, and it looks like the key
    # was ignored.
    engine = settings.GEMINI_MODEL if settings.GEMINI_API_KEY else "offline"
    raw = f"{engine}|{language}|{question.strip().lower()}|{context}|{extra}"
    return "chat:" + hashlib.sha256(raw.encode()).hexdigest()[:32]


async def _cached(key: str) -> dict | None:
    try:
        hit = await get_redis().get(key)
        return json.loads(hit) if hit else None
    except Exception:            # cache is a nice-to-have, never a hard dependency
        return None


async def _store(key: str, value: dict) -> None:
    try:
        await get_redis().setex(key, CACHE_TTL, json.dumps(value))
    except Exception:
        pass


async def answer(
    question: str,
    language: str = "en",
    context: str = "",
    attachment_context: str = "",
    attachment_preamble: str = "",
) -> dict:
    """Answer a farmer's question.

    attachment_context  - machine-readable analysis of an uploaded photo or file,
                          fed to the model as evidence.
    attachment_preamble - already-localised summary shown to the farmer even when
                          no LLM is available (the offline path).
    """
    key = _cache_key(question, language, context, attachment_context)
    cached = await _cached(key)
    if cached:
        cached["cached"] = True
        return cached

    passages = await rag.retrieve(question, k=3)
    sources = [p["title"] for p in passages]

    if not settings.GEMINI_API_KEY:
        result = {
            "reply": _fallback(passages, language, attachment_preamble),
            "sources": sources,
            "engine": "offline-rag",
            "language": language,
        }
        await _store(key, result)
        return result

    meta = L.meta(language)
    reference = "\n\n".join(
        f"[{p['title']}]\n{p['text'][:PASSAGE_CHARS]}" for p in passages
    ) or "No passages retrieved."

    prompt = (
        SYSTEM.format(language=meta["name"], script=meta["script"])
        + f"\n\nFARM CONTEXT:\n{context or 'not provided'}"
        + (f"\n\nIMAGE / FILE ANALYSIS:\n{attachment_context}" if attachment_context else "")
        + f"\n\nREFERENCE PASSAGES:\n{reference}"
        + f"\n\nFARMER'S QUESTION:\n{question}"
    )

    try:
        async with httpx.AsyncClient(timeout=GEMINI_TIMEOUT) as client:
            text = await _gemini(prompt, client)
            if not text:
                raise ValueError("empty completion")

            # Models drift into romanised output. Catch it and force a rewrite once.
            if not L.is_native_script(text, language):
                log.info("reply not in %s script, retrying", meta["script"])
                retry = (
                    prompt
                    + "\n\nYOUR PREVIOUS ANSWER:\n"
                    + text
                    + RETRY_NUDGE.format(language=meta["name"], script=meta["script"])
                )
                rewritten = await _gemini(retry, client)
                if rewritten and L.is_native_script(rewritten, language):
                    text = rewritten

        reply = f"{attachment_preamble}\n\n{text}" if attachment_preamble else text
        result = {"reply": reply, "sources": sources, "engine": settings.GEMINI_MODEL, "language": language}
        await _store(key, result)
        return result

    except Exception as exc:
        detail = exc.response.text[:300] if isinstance(exc, httpx.HTTPStatusError) else str(exc)
        log.error(
            "GEMINI CALL FAILED - falling back to offline answer. model=%s error=%s",
            settings.GEMINI_MODEL, detail,
        )
        return {
            "reply": _fallback(passages, language, attachment_preamble),
            "sources": sources,
            # Distinct from plain "offline-rag" so you can tell a rejected key
            # from no key at all, without reading the logs.
            "engine": "offline-rag (gemini unavailable)",
            "language": language,
        }


async def translate(text: str, language: str) -> str:
    """Translate a short system-generated string. Returns the input unchanged
    when there is no model, rather than guessing."""
    if language == "en" or not settings.GEMINI_API_KEY:
        return text
    meta = L.meta(language)
    prompt = (
        f"Translate the following agricultural advice into {meta['name']} using "
        f"{meta['script']} script. Keep chemical names and numbers unchanged. "
        f"Output only the translation.\n\n{text}"
    )
    try:
        async with httpx.AsyncClient(timeout=GEMINI_TIMEOUT) as client:
            out = await _gemini(prompt, client)
        return out or text
    except Exception as exc:
        log.warning("translate failed: %s", exc)
        return text


async def warm_up() -> None:
    if settings.GEMINI_API_KEY:
        log.info("LLM: gemini enabled, model=%s, key ends ...%s",
                 settings.GEMINI_MODEL, settings.GEMINI_API_KEY[-4:])
    else:
        log.warning("LLM: no GEMINI_API_KEY in this container - answering from local RAG only")
    """Touch the retrieval index at boot so the first farmer question is not the
    one that pays to build it."""
    try:
        await asyncio.wait_for(rag.retrieve("rice", k=1), timeout=5)
    except Exception:
        pass
