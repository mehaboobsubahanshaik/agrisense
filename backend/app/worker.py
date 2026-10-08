"""Celery worker: scheduled advisories and heavy background jobs.

Run with:  celery -A app.worker.celery_app worker -B --loglevel=info
"""
import asyncio

from celery import Celery
from celery.schedules import crontab
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Farm, Notification, User
from app.db.session import SessionLocal
from app.services import market, weather as weather_service
from app.services import schemes as scheme_service

celery_app = Celery("agrisense", broker=settings.REDIS_URL, backend=settings.REDIS_URL)
celery_app.conf.beat_schedule = {
    "daily-weather-advisory": {"task": "app.worker.daily_weather_advisory", "schedule": crontab(hour=1, minute=30)},
    # Verify every official scheme link nightly, so a closed or moved scheme is
    # flagged in the app instead of quietly sending farmers to a dead page.
    "nightly-scheme-verification": {"task": "app.worker.verify_schemes", "schedule": crontab(hour=2, minute=15)},
    # Pull the day's mandi prices into cache before the morning rush.
    "morning-market-prices": {"task": "app.worker.warm_market_prices", "schedule": crontab(hour=6, minute=0)},
}
celery_app.conf.timezone = "Asia/Kolkata"


async def _daily() -> int:
    sent = 0
    async with SessionLocal() as db:
        users = (await db.execute(select(User).where(User.is_active.is_(True)))).scalars().all()
        for user in users:
            farm = (await db.execute(select(Farm).where(Farm.user_id == user.id))).scalars().first()
            data = await weather_service.forecast(farm.lat if farm else user.lat, farm.lon if farm else user.lon)
            for item in data["advisory"]:
                if item["level"] == "high":
                    db.add(Notification(user_id=user.id, title=item["title"], body=item["text"], kind="weather"))
                    sent += 1
        await db.commit()
    return sent


@celery_app.task(name="app.worker.daily_weather_advisory")
def daily_weather_advisory() -> int:
    return asyncio.run(_daily())


@celery_app.task(name="app.worker.verify_schemes")
def verify_schemes() -> dict:
    if not settings.SCHEME_REFRESH_ENABLED:
        return {"skipped": True}
    return asyncio.run(scheme_service.refresh())


async def _warm_market() -> int:
    """Prime the price cache for the states we have users in."""
    states: set[str] = set()
    async with SessionLocal() as db:
        for user in (await db.execute(select(User).where(User.is_active.is_(True)))).scalars().all():
            if user.state:
                states.add(user.state)
    warmed = 0
    for state in states or {""}:
        try:
            await market.prices(state=state, limit=60)
            warmed += 1
        except Exception:
            pass
    return warmed


@celery_app.task(name="app.worker.warm_market_prices")
def warm_market_prices() -> int:
    return asyncio.run(_warm_market())
