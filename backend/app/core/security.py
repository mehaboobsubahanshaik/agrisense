import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

ALGO = "HS256"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def hash_secret(value: str) -> str:
    """HMAC used for OTP codes and refresh tokens at rest (never stored in clear)."""
    return hmac.new(settings.SECRET_KEY.encode(), value.encode(), hashlib.sha256).hexdigest()


def verify_secret(value: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_secret(value), hashed)


def create_access_token(user_id: str, session_id: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "sid": session_id,
        "role": role,
        "type": "access",
        "jti": str(uuid.uuid4()),
        "iat": _now(),
        "exp": _now() + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGO)


def create_refresh_token(user_id: str, session_id: str) -> str:
    payload = {
        "sub": user_id,
        "sid": session_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "iat": _now(),
        "exp": _now() + timedelta(days=settings.REFRESH_TOKEN_DAYS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGO)


def decode_token(token: str, expected_type: str) -> dict:
    data = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGO])
    if data.get("type") != expected_type:
        raise jwt.InvalidTokenError("wrong token type")
    return data
