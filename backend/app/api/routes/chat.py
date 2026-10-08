"""Chat: text, voice transcript, photo or document.

Two endpoints because FastAPI cannot accept JSON and multipart on one path:
  POST /chat          - plain JSON question (fast path, no file)
  POST /chat/attach   - multipart question with a photo or document

Both share the same answering pipeline, so an attached photo produces an answer
in the same language, with the same grounding and the same safety line.
"""
import logging
import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.core.config import settings
from app.db.models import ChatMessage, CropImage, DiseaseReport, Farm, User
from app.db.session import get_db
from app.knowledge import localization as L
from app.schemas import ChatIn, ChatOut
from app.services import agronomy, llm, market, vision

log = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
DOC_TYPES = {"application/pdf", "text/plain", "text/csv", "application/json", "text/markdown"}
MAX_BYTES = 12 * 1024 * 1024
DOC_CHARS = 4000


async def _farm_context(db: AsyncSession, user: User) -> str:
    farm = (await db.execute(select(Farm).where(Farm.user_id == user.id))).scalars().first()
    parts = [f"State: {user.state}", f"District: {user.district or 'not set'}"]
    if farm:
        parts += [
            f"Farm size: {farm.area_acres} acres",
            f"Soil type: {farm.soil_type}",
            f"Irrigation: {farm.irrigation}",
            f"Crops grown: {', '.join(farm.crops or []) or 'not set'}",
        ]
    return "; ".join(parts)


PRICE_WORDS = {
    "price", "prices", "rate", "rates", "cost", "mandi", "market", "sell", "selling",
    "profit", "profitable", "income", "msp", "quintal", "value", "worth",
    "ధర", "రేటు", "మార్కెట్", "भाव", "दाम", "कीमत", "बाजार", "விலை", "ಬೆಲೆ", "দাম", "ਭਾਅ",
}


async def _live_price_context(message: str, user: User) -> str:
    """If the farmer is asking about money, answer from today's mandi feed rather
    than from a static document. Returns evidence for the model, or '' when the
    question is not about price or no market reported that crop today."""
    words = set(message.lower().replace("?", " ").split())
    if not words & PRICE_WORDS:
        return ""

    # Which crop? Take the first one the question actually names.
    crop = ""
    for token in message.lower().split():
        candidate, known = agronomy.normalise_crop(token.strip(",.?!"))
        if known:
            crop = candidate
            break
    if not crop:
        return ""

    try:
        summary = await market.summary_for_crop(crop, user.state or "")
        return market.as_chat_context(summary)
    except Exception as exc:                 # never let a price lookup break chat
        log.warning("live price lookup failed: %s", exc)
        return ""


async def _persist(
    db: AsyncSession,
    user: User,
    question: str,
    result: dict,
    language: str,
    attachment: dict | None = None,
) -> None:
    db.add(
        ChatMessage(
            user_id=user.id, role="user", content=question,
            language=language, attachment=attachment,
        )
    )
    db.add(
        ChatMessage(
            user_id=user.id, role="assistant", content=result["reply"],
            language=language, sources=result["sources"], engine=result.get("engine"),
        )
    )
    await db.commit()


# --------------------------------------------------------------------------
# plain text
# --------------------------------------------------------------------------
@router.post("", response_model=ChatOut)
async def ask(body: ChatIn, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    language = body.language or user.language or "en"
    context = await _farm_context(db, user)
    live = await _live_price_context(body.message, user)
    result = await llm.answer(body.message, language, context, attachment_context=live)
    await _persist(db, user, body.message, result, language)
    return ChatOut(**result)


# --------------------------------------------------------------------------
# with a photo or a document
# --------------------------------------------------------------------------
def _image_preamble(advisory: dict, raw: dict, language: str, include_remedies: bool) -> tuple[str, str]:
    """Return (farmer-facing localised summary, machine-readable evidence)."""
    key = advisory.get("disease_key", "unknown")
    name = L.disease_name(key, language)
    conf = round(float(advisory.get("confidence", 0)) * 100)
    severity = advisory.get("severity", "low")
    area = advisory.get("affected_area_pct", 0)

    if key == "unknown":
        shown = advisory.get("message", "")
        return shown, "No confident detection from the photo; ask the farmer for a clearer close-up."

    if key == "healthy":
        shown = f"**{L.t('detected', language)}: {name}** ({L.t('confidence', language)} {conf}%)\n\n{L.t('healthy_note', language)}"
    else:
        shown = (
            f"**{L.t('detected', language)}: {name}** "
            f"({L.t('confidence', language)} {conf}%, "
            f"{L.t('severity', language)}: {L.t(severity, language)}, "
            f"{L.t('affected_area', language)}: {area}%)"
        )

    remedies = advisory.get("remedies", {}) or {}

    # With no model to write the remedies in the farmer's language, we still show
    # them under localised headings rather than dropping them entirely.
    if include_remedies and key != "healthy":
        for field in ("chemical", "organic", "cultural"):
            items = remedies.get(field) or []
            if items:
                bullets = "\n".join(f"- {i}" for i in items[:3])
                shown += f"\n\n**{L.t(field, language)}**\n{bullets}"
        shown += f"\n\n{L.t('safety', language)}"

    evidence = (
        f"Detected disease: {advisory.get('label', key)} (key={key}); "
        f"confidence={conf}%; severity={severity}; affected_leaf_area={area}%; "
        f"detector={raw.get('model', 'unknown')}. "
        f"Chemical options: {'; '.join(remedies.get('chemical', []))}. "
        f"Organic options: {'; '.join(remedies.get('organic', []))}. "
        f"Cultural practice: {'; '.join(remedies.get('cultural', []))}."
    )
    return shown, evidence


def _extract_text(data: bytes, content_type: str, filename: str) -> str:
    if content_type == "application/pdf":
        try:
            import io

            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            pages = [(p.extract_text() or "") for p in reader.pages[:6]]
            return "\n".join(pages)[:DOC_CHARS]
        except Exception as exc:
            log.warning("pdf extract failed for %s: %s", filename, exc)
            return ""
    try:
        return data.decode("utf-8", errors="ignore")[:DOC_CHARS]
    except Exception:
        return ""


@router.post("/attach", response_model=ChatOut)
async def ask_with_attachment(
    file: UploadFile = File(...),
    message: str = Form(default=""),
    language: str = Form(default=""),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    content_type = (file.content_type or "").lower()
    if content_type not in IMAGE_TYPES | DOC_TYPES:
        raise HTTPException(
            status_code=415,
            detail="Attach a JPG, PNG or WEBP photo, or a PDF, TXT or CSV file such as a soil health card.",
        )

    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 12 MB. Send a smaller one.")
    if not data:
        raise HTTPException(status_code=400, detail="The file is empty.")

    lang = language or user.language or "en"
    filename = file.filename or "attachment"

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(filename)[1][:6] or (".jpg" if content_type in IMAGE_TYPES else ".bin")
    stored = f"{uuid.uuid4()}{ext}"
    with open(os.path.join(settings.UPLOAD_DIR, stored), "wb") as fh:
        fh.write(data)
    url = f"/uploads/{stored}"

    context = await _farm_context(db, user)
    preamble = ""
    evidence = ""
    attachment: dict = {"kind": "file", "url": url, "name": filename}

    if content_type in IMAGE_TYPES:
        # The photo goes through the same detector the Crop scan page uses, and the
        # result is saved as a report so it appears in the farmer's scan history too.
        image = CropImage(user_id=user.id, path=url, filename=filename)
        db.add(image)
        await db.flush()

        raw = await vision.detect(data, filename, "")
        advisory = vision.build_advisory(raw)
        preamble, evidence = _image_preamble(advisory, raw, lang, include_remedies=not settings.GEMINI_API_KEY)

        db.add(
            DiseaseReport(
                user_id=user.id, image_id=image.id,
                crop=advisory.get("crop", "unknown"),
                disease=advisory.get("label", "unknown"),
                confidence=advisory.get("confidence", 0.0),
                severity=advisory.get("severity", "low"),
                model=raw.get("model", "unknown"),
                advisory=advisory,
            )
        )
        attachment = {
            "kind": "image", "url": url, "name": filename,
            "disease": advisory.get("label"),
            "disease_local": L.disease_name(advisory.get("disease_key", "unknown"), lang),
            "severity": advisory.get("severity"),
            "model": raw.get("model"),
        }
        question = message.strip() or f"What should I do about {advisory.get('label', 'this problem')}?"
    else:
        text = _extract_text(data, content_type, filename)
        if not text.strip():
            raise HTTPException(
                status_code=422,
                detail="No readable text in that file. If it is a scanned page, send a photo of it instead.",
            )
        evidence = f"Attached document '{filename}':\n{text}"
        preamble = f"**{L.t('from_file', lang)}: {filename}**"
        attachment["chars"] = len(text)
        question = message.strip() or "Read my attached report and tell me what to do."

    result = await llm.answer(
        question, lang, context,
        attachment_context=evidence,
        attachment_preamble=preamble,
    )
    await _persist(db, user, question, result, lang, attachment)
    return ChatOut(**result, attachment=attachment)


# --------------------------------------------------------------------------
@router.get("/history")
async def history(limit: int = 50, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(ChatMessage)
            .where(ChatMessage.user_id == user.id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": r.id, "role": r.role, "content": r.content, "sources": r.sources,
            "attachment": r.attachment, "engine": r.engine, "created_at": r.created_at,
        }
        for r in reversed(rows)
    ]


@router.delete("/history")
async def clear_history(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(delete(ChatMessage).where(ChatMessage.user_id == user.id))
    await db.commit()
    return {"detail": "Chat history cleared."}
