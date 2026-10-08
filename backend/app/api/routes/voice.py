import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.deps import current_user
from app.core.config import settings
from app.db.models import User

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/transcribe")
async def transcribe(
    file: UploadFile = File(...),
    language: str = Form(default="en"),
    user: User = Depends(current_user),
):
    """Speech to text via Whisper running in the AI service.

    The web client also has a browser-native fallback (Web Speech API), which is
    what makes voice usable on a low-bandwidth 2G connection.
    """
    data = await file.read()
    try:
        async with httpx.AsyncClient(timeout=120) as c:
            r = await c.post(
                f"{settings.AI_SERVICE_URL}/transcribe",
                files={"file": (file.filename or "audio.webm", data, "application/octet-stream")},
                data={"language": language},
            )
            r.raise_for_status()
            return r.json()
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Voice transcription is not available right now. Use the microphone button in your browser or type the question.",
        )
