import logging

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)


async def send_otp(phone: str, code: str) -> bool:
    text = f"{code} is your AgriSense AI login code. It expires in 5 minutes. Do not share it."
    provider = settings.SMS_PROVIDER.lower()

    if provider == "msg91" and settings.MSG91_AUTH_KEY:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(
                    "https://control.msg91.com/api/v5/otp",
                    params={
                        "template_id": settings.MSG91_TEMPLATE_ID,
                        "mobile": f"91{phone}",
                        "authkey": settings.MSG91_AUTH_KEY,
                        "otp": code,
                    },
                )
                r.raise_for_status()
            return True
        except Exception as exc:
            log.error("msg91 send failed: %s", exc)
            return False

    if provider == "twilio" and settings.TWILIO_SID:
        try:
            async with httpx.AsyncClient(timeout=15) as c:
                r = await c.post(
                    f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_SID}/Messages.json",
                    auth=(settings.TWILIO_SID, settings.TWILIO_TOKEN),
                    data={"To": f"+91{phone}", "From": settings.TWILIO_FROM, "Body": text},
                )
                r.raise_for_status()
            return True
        except Exception as exc:
            log.error("twilio send failed: %s", exc)
            return False

    # console provider: the OTP is printed to the container log for local demos
    log.info("OTP for %s is %s", phone, code)
    print(f"\n=== AgriSense OTP ===  phone: {phone}  code: {code}  (valid 5 min)\n", flush=True)
    return True
