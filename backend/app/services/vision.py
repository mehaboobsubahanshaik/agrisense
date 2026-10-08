"""Thin client for the YOLO inference microservice + advisory composition."""
import logging

import httpx

from app.core.config import settings
from app.knowledge.agri_docs import DISEASE_LIBRARY

log = logging.getLogger(__name__)


async def detect(image_bytes: bytes, filename: str, crop_hint: str = "") -> dict:
    try:
        async with httpx.AsyncClient(timeout=90) as c:
            r = await c.post(
                f"{settings.AI_SERVICE_URL}/detect",
                files={"file": (filename, image_bytes, "application/octet-stream")},
                data={"crop_hint": crop_hint},
            )
            r.raise_for_status()
            return r.json()
    except Exception as exc:
        log.error("ai-service detect failed: %s", exc)
        return {
            "ok": False,
            "model": "unavailable",
            "predictions": [],
            "error": "The image analysis service is not responding. Try again in a moment.",
        }


def build_advisory(result: dict) -> dict:
    preds = result.get("predictions") or []
    if not preds:
        return {"disease_key": "unknown", "label": "No confident detection", "remedies": {},
                "message": "The image was not clear enough. Take a close, well-lit photo of the affected leaf "
                           "against a plain background and try again."}
    top = preds[0]
    key = top.get("class", "unknown")
    lib = DISEASE_LIBRARY.get(key, DISEASE_LIBRARY["leaf_spot"])
    conf = float(top.get("confidence", 0))
    severity = top.get("severity") or ("high" if conf > 0.8 else "medium" if conf > 0.55 else "low")
    return {
        "disease_key": key,
        "label": lib["label"],
        "crop": lib["crop"],
        "confidence": round(conf, 3),
        "severity": severity,
        "affected_area_pct": top.get("affected_area_pct", 0),
        "symptoms": lib["symptoms"],
        "remedies": {
            "chemical": lib["chemical"],
            "organic": lib["organic"],
            "cultural": lib["cultural"],
        },
        "safety": "Wear gloves, mask and full sleeves while spraying. Do not spray against the wind. "
                  "Respect the pre-harvest interval printed on the label.",
    }
