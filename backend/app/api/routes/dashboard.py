from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.db.models import (
    ChatMessage,
    CropImage,
    DiseaseReport,
    Farm,
    GovernmentScheme,
    Notification,
    SoilReport,
    User,
    YieldPrediction,
)
from app.db.session import get_db
from app.services import agronomy, weather as weather_service

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def summary(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    farm = (await db.execute(select(Farm).where(Farm.user_id == user.id))).scalars().first()
    lat = farm.lat if farm else user.lat
    lon = farm.lon if farm else user.lon
    w = await weather_service.forecast(lat, lon)

    since = datetime.now(timezone.utc) - timedelta(days=30)
    reports = (
        await db.execute(
            select(DiseaseReport)
            .where(DiseaseReport.user_id == user.id)
            .order_by(DiseaseReport.created_at.desc())
            .limit(5)
        )
    ).scalars().all()
    active_alerts = [r for r in reports if r.severity in ("high", "medium")]

    soil = (
        await db.execute(
            select(SoilReport).where(SoilReport.user_id == user.id).order_by(SoilReport.created_at.desc()).limit(1)
        )
    ).scalars().first()
    yield_row = (
        await db.execute(
            select(YieldPrediction)
            .where(YieldPrediction.user_id == user.id)
            .order_by(YieldPrediction.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    last_chat = (
        await db.execute(
            select(ChatMessage)
            .where(ChatMessage.user_id == user.id, ChatMessage.role == "assistant")
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
    ).scalars().first()
    uploads = (
        await db.execute(
            select(CropImage).where(CropImage.user_id == user.id).order_by(CropImage.created_at.desc()).limit(6)
        )
    ).scalars().all()
    unread = (
        await db.execute(
            select(func.count()).select_from(Notification).where(
                Notification.user_id == user.id, Notification.read.is_(False)
            )
        )
    ).scalar_one()
    schemes = (await db.execute(select(GovernmentScheme).limit(3))).scalars().all()

    soil_score = soil.score if soil else 0
    crop_health = max(0, 100 - sum({"high": 30, "medium": 15, "low": 5}.get(r.severity, 0) for r in reports))
    rain_next = sum(d["rain_mm"] for d in w["daily"][:3])

    # water requirement: crop coefficient x reference ET, minus effective rainfall
    crop = (farm.crops[0] if farm and farm.crops else "rice")
    kc = {"rice": 1.15, "maize": 1.0, "cotton": 0.95, "wheat": 0.95}.get(crop, 1.0)
    et0 = max(2.5, 0.0023 * (w["current"]["temp_c"] + 17.8) * 12)
    need_mm = max(0.0, round(kc * et0 * 3 - rain_next, 1))

    farm_score = round(
        0.35 * soil_score + 0.35 * crop_health + 0.30 * (100 - min(100, len(active_alerts) * 25)), 1
    )

    return {
        "farm": {
            "name": farm.name if farm else "My Farm",
            "area_acres": farm.area_acres if farm else 0,
            "soil_type": farm.soil_type if farm else "-",
            "crops": farm.crops if farm else [],
            "score": farm_score,
        },
        "weather": {"current": w["current"], "daily": w["daily"][:5], "advisory": w["advisory"], "source": w["source"]},
        "disease_alerts": [
            {"id": r.id, "disease": r.disease, "severity": r.severity, "confidence": r.confidence,
             "created_at": r.created_at}
            for r in reports
        ],
        "crop_health": crop_health,
        "soil": {"score": soil_score, "grade": (soil.recommendation or {}).get("grade") if soil else None,
                 "crop": soil.crop if soil else None},
        "water": {"next_3_day_rain_mm": round(rain_next, 1), "irrigation_need_mm": need_mm,
                  "advice": "Skip irrigation, rain is coming." if need_mm == 0 else f"Apply about {need_mm} mm over the next 3 days."},
        "yield": {"crop": yield_row.crop, "total_quintals": yield_row.predicted_quintals,
                  "confidence": yield_row.confidence} if yield_row else None,
        "latest_chat": {"content": last_chat.content[:220], "created_at": last_chat.created_at} if last_chat else None,
        "recent_uploads": [{"url": u.path, "created_at": u.created_at} for u in uploads],
        "unread_notifications": unread,
        "schemes": [{"code": s.code, "name": s.name, "benefit": s.benefit} for s in schemes],
        "crop_calendar": agronomy.CROP_PROFILE.get(crop, {}),
    }
