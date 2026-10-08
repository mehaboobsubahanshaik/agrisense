"""OTP lifecycle in Redis.

Policy enforced here (exactly as specified):
  6 digits | 5 minute expiry | 5 verification attempts | 30 second resend cooldown
"""
import json
import secrets
from dataclasses import dataclass

from app.core.config import settings
from app.core.redis_client import get_redis
from app.core.security import hash_secret, verify_secret
from app.services import sms


class OtpError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code, self.message, self.status = code, message, status
        super().__init__(message)


@dataclass
class Issued:
    code: str
    ttl: int
    resend_after: int


def _key(phone: str) -> str:
    return f"otp:code:{phone}"


def _cooldown(phone: str) -> str:
    return f"otp:cooldown:{phone}"


def _daily(phone: str) -> str:
    return f"otp:daily:{phone}"


async def issue(phone: str) -> Issued:
    r = get_redis()

    if await r.exists(_cooldown(phone)):
        wait = await r.ttl(_cooldown(phone))
        raise OtpError("resend_too_soon", f"Please wait {wait} seconds before asking for a new code.", 429)

    sent_today = int(await r.get(_daily(phone)) or 0)
    if sent_today >= settings.OTP_DAILY_LIMIT:
        raise OtpError("daily_limit", "Too many codes requested today. Try again tomorrow.", 429)

    code = "".join(secrets.choice("0123456789") for _ in range(settings.OTP_LENGTH))
    await r.setex(
        _key(phone),
        settings.OTP_TTL_SECONDS,
        json.dumps({"hash": hash_secret(code), "attempts": 0}),
    )
    await r.setex(_cooldown(phone), settings.OTP_RESEND_SECONDS, "1")
    await r.incr(_daily(phone))
    await r.expire(_daily(phone), 86400)

    await sms.send_otp(phone, code)
    return Issued(code=code, ttl=settings.OTP_TTL_SECONDS, resend_after=settings.OTP_RESEND_SECONDS)


async def verify(phone: str, code: str) -> None:
    r = get_redis()
    raw = await r.get(_key(phone))
    if not raw:
        raise OtpError("expired", "That code has expired. Ask for a new one.", 400)

    record = json.loads(raw)
    if record["attempts"] >= settings.OTP_MAX_ATTEMPTS:
        await r.delete(_key(phone))
        raise OtpError("locked", "Too many wrong attempts. Ask for a new code.", 429)

    if not verify_secret(code, record["hash"]):
        record["attempts"] += 1
        ttl = await r.ttl(_key(phone))
        await r.setex(_key(phone), max(ttl, 1), json.dumps(record))
        left = settings.OTP_MAX_ATTEMPTS - record["attempts"]
        raise OtpError("invalid", f"Wrong code. {left} attempt(s) left.", 400)

    await r.delete(_key(phone))
