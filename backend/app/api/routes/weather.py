from fastapi import APIRouter, Depends

from app.api.deps import current_user
from app.db.models import User
from app.services import weather as weather_service

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("")
async def get_weather(lat: float | None = None, lon: float | None = None, user: User = Depends(current_user)):
    return await weather_service.forecast(lat if lat is not None else user.lat, lon if lon is not None else user.lon)
