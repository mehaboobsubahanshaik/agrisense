import os
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.core.config import settings
from app.db.models import CropImage, DiseaseReport, Notification, User
from app.db.session import get_db
from app.services import vision

router = APIRouter(prefix="/disease", tags=["disease"])

ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_BYTES = 12 * 1024 * 1024


@router.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    crop_hint: str = Form(default=""),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type not in ALLOWED:
        raise HTTPException(status_code=415, detail="Upload a JPG, PNG or WEBP photo of the affected plant.")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Photo is larger than 12 MB. Take a smaller photo and retry.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "")[1][:6] or ".jpg"
    name = f"{uuid.uuid4()}{ext}"
    with open(os.path.join(settings.UPLOAD_DIR, name), "wb") as fh:
        fh.write(data)

    image = CropImage(user_id=user.id, path=f"/uploads/{name}", filename=file.filename or name)
    db.add(image)
    await db.flush()

    raw = await vision.detect(data, file.filename or name, crop_hint)
    advisory = vision.build_advisory(raw)

    report = DiseaseReport(
        user_id=user.id,
        image_id=image.id,
        crop=crop_hint or advisory.get("crop", "unknown"),
        disease=advisory.get("label", "unknown"),
        confidence=advisory.get("confidence", 0.0),
        severity=advisory.get("severity", "low"),
        model=raw.get("model", "unknown"),
        advisory=advisory,
    )
    db.add(report)

    if advisory.get("severity") == "high":
        db.add(
            Notification(
                user_id=user.id,
                title=f"Act now: {advisory.get('label')}",
                body="High severity detected in your last photo. Open the report for the spray schedule.",
                kind="disease",
            )
        )
    await db.commit()

    return {
        "report_id": report.id,
        "image_url": image.path,
        "model": raw.get("model"),
        "raw_predictions": raw.get("predictions", []),
        "annotated_image": raw.get("annotated_image"),
        "advisory": advisory,
    }


@router.get("/reports")
async def reports(limit: int = 20, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(DiseaseReport)
            .where(DiseaseReport.user_id == user.id)
            .order_by(DiseaseReport.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        {
            "id": r.id,
            "crop": r.crop,
            "disease": r.disease,
            "confidence": r.confidence,
            "severity": r.severity,
            "model": r.model,
            "advisory": r.advisory,
            "created_at": r.created_at,
        }
        for r in rows
    ]
