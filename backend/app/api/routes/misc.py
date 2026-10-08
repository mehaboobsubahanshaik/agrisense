from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, require_roles
from app.db.models import (
    ActivityLog,
    ChatMessage,
    DiseaseReport,
    Farm,
    Feedback,
    IoTDevice,
    Language,
    Notification,
    User,
)
from app.db.session import get_db
from app.schemas import FeedbackIn, IoTReadingIn

router = APIRouter(tags=["misc"])


@router.get("/notifications")
async def notifications(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(Notification).where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc()).limit(50)
        )
    ).scalars().all()
    return [{"id": n.id, "title": n.title, "body": n.body, "kind": n.kind, "read": n.read,
             "created_at": n.created_at} for n in rows]


@router.post("/notifications/read-all")
async def read_all(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(update(Notification).where(Notification.user_id == user.id).values(read=True))
    await db.commit()
    return {"detail": "All notifications marked as read."}


@router.get("/farms")
async def get_farms(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Farm).where(Farm.user_id == user.id))).scalars().all()
    return [{"id": f.id, "name": f.name, "area_acres": f.area_acres, "soil_type": f.soil_type,
             "irrigation": f.irrigation, "lat": f.lat, "lon": f.lon, "crops": f.crops} for f in rows]


@router.patch("/farms/{farm_id}")
async def update_farm(farm_id: str, payload: dict, user: User = Depends(current_user),
                      db: AsyncSession = Depends(get_db)):
    farm = await db.get(Farm, farm_id)
    if farm is None or farm.user_id != user.id:
        raise HTTPException(status_code=404, detail="That farm was not found.")
    for field in ("name", "area_acres", "soil_type", "irrigation", "lat", "lon", "crops"):
        if field in payload:
            setattr(farm, field, payload[field])
    await db.commit()
    return {"detail": "Farm updated."}


@router.get("/languages")
async def languages(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Language))).scalars().all()
    return [{"code": r.code, "label": r.label, "native": r.native} for r in rows]


@router.post("/feedback")
async def feedback(body: FeedbackIn, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    db.add(Feedback(user_id=user.id, rating=body.rating, message=body.message))
    await db.commit()
    return {"detail": "Thanks - your feedback was recorded."}


@router.post("/iot/reading")
async def iot_reading(body: IoTReadingIn, db: AsyncSession = Depends(get_db)):
    """Open endpoint for field sensors. Authenticate with the device key."""
    device = (
        await db.execute(select(IoTDevice).where(IoTDevice.device_key == body.device_key))
    ).scalars().first()
    if device is None:
        raise HTTPException(status_code=404, detail="Unknown device key.")
    device.last_reading = body.model_dump(exclude={"device_key"}, exclude_none=True)
    device.last_seen = datetime.now(timezone.utc)
    if body.soil_moisture is not None and body.soil_moisture < 15:
        db.add(Notification(user_id=device.user_id, title="Soil moisture low",
                            body=f"{device.label} reads {body.soil_moisture}% moisture. Irrigation is due.",
                            kind="weather"))
    await db.commit()
    return {"detail": "Reading stored."}


@router.get("/iot/devices")
async def iot_devices(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(IoTDevice).where(IoTDevice.user_id == user.id))).scalars().all()
    return [{"id": d.id, "label": d.label, "device_key": d.device_key, "last_reading": d.last_reading,
             "last_seen": d.last_seen} for d in rows]


@router.get("/admin/stats")
async def admin_stats(user: User = Depends(require_roles("admin")), db: AsyncSession = Depends(get_db)):
    async def count(model):
        return (await db.execute(select(func.count()).select_from(model))).scalar_one()

    return {
        "users": await count(User),
        "disease_reports": await count(DiseaseReport),
        "chat_messages": await count(ChatMessage),
        "farms": await count(Farm),
        "logins_logged": await count(ActivityLog),
    }


# ---------------------------------------------------------------------------
# Live market prices (data.gov.in daily mandi feed)
# ---------------------------------------------------------------------------
@router.get("/market/prices", tags=["market"])
async def market_prices(
    state: str = "",
    commodity: str = "",
    limit: int = 40,
    user: User = Depends(current_user),
):
    """Today's mandi prices. Every response states its own `as_of` date and
    whether it came from the live feed or a cached snapshot."""
    from app.services import market

    return await market.prices(state=state or user.state or "", commodity=commodity, limit=limit)


@router.get("/market/crop/{crop}", tags=["market"])
async def market_crop(crop: str, state: str = "", user: User = Depends(current_user)):
    from app.services import market

    return await market.summary_for_crop(crop, state or user.state or "")
