from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_secret,
    verify_secret,
)
from app.db.models import ActivityLog, Farm, Notification, OtpRequest
from app.db.models import Session as SessionModel
from app.db.models import User
from app.db.session import get_db
from app.schemas import (
    OtpRequestIn,
    OtpRequestOut,
    OtpVerifyIn,
    ProfileIn,
    RefreshIn,
    SessionOut,
    TokenOut,
    UserOut,
)
from app.services import otp as otp_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-otp", response_model=OtpRequestOut)
async def request_otp(body: OtpRequestIn, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        issued = await otp_service.issue(body.phone)
    except otp_service.OtpError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.message)

    record = OtpRequest(
        phone=body.phone,
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=issued.ttl),
        ip=request.client.host if request.client else "",
    )
    db.add(record)
    await db.commit()

    return OtpRequestOut(
        request_id=record.id,
        expires_in=issued.ttl,
        resend_after=issued.resend_after,
        max_attempts=settings.OTP_MAX_ATTEMPTS,
        dev_otp=issued.code if settings.DEV_MODE else None,
    )


@router.post("/verify-otp", response_model=TokenOut)
async def verify_otp(body: OtpVerifyIn, request: Request, db: AsyncSession = Depends(get_db)):
    try:
        await otp_service.verify(body.phone, body.otp)
    except otp_service.OtpError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.message)

    user = (await db.execute(select(User).where(User.phone == body.phone))).scalar_one_or_none()
    new_user = user is None
    if new_user:
        user = User(phone=body.phone, name=f"Farmer {body.phone[-4:]}")
        db.add(user)
        await db.flush()
        db.add(Farm(user_id=user.id, name="My Farm", crops=["rice"]))
        db.add(
            Notification(
                user_id=user.id,
                title="Welcome to AgriSense AI",
                body="Add your farm details in Settings so weather and advice match your field.",
                kind="info",
            )
        )

    session = SessionModel(
        user_id=user.id,
        refresh_hash="",
        device=body.device or request.headers.get("user-agent", "")[:250],
        ip=request.client.host if request.client else "",
    )
    db.add(session)
    await db.flush()

    refresh = create_refresh_token(user.id, session.id)
    session.refresh_hash = hash_secret(refresh)
    access = create_access_token(user.id, session.id, user.role)

    db.add(ActivityLog(user_id=user.id, action="login", meta={"new_user": new_user}))
    await db.execute(
        update(OtpRequest).where(OtpRequest.phone == body.phone, OtpRequest.verified.is_(False)).values(verified=True)
    )
    await db.commit()
    await db.refresh(user)

    return TokenOut(
        access_token=access,
        refresh_token=refresh,
        expires_in=settings.ACCESS_TOKEN_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh", response_model=TokenOut)
async def refresh_token(body: RefreshIn, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token, "refresh")
    except Exception:
        raise HTTPException(status_code=401, detail="Sign in again to continue.")

    session = await db.get(SessionModel, payload["sid"])
    if session is None or session.revoked or not verify_secret(body.refresh_token, session.refresh_hash):
        raise HTTPException(status_code=401, detail="Sign in again to continue.")

    user = await db.get(User, payload["sub"])
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Sign in again to continue.")

    # rotate the refresh token on every use
    new_refresh = create_refresh_token(user.id, session.id)
    session.refresh_hash = hash_secret(new_refresh)
    session.last_seen = datetime.now(timezone.utc)
    await db.commit()

    return TokenOut(
        access_token=create_access_token(user.id, session.id, user.role),
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_MINUTES * 60,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(current_user)):
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(body: ProfileIn, user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/sessions", response_model=list[SessionOut])
async def list_sessions(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    rows = (
        await db.execute(
            select(SessionModel).where(SessionModel.user_id == user.id).order_by(SessionModel.created_at.desc())
        )
    ).scalars().all()
    return rows


@router.post("/logout")
async def logout(
    authorization: str = Header(default=""),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    payload = decode_token(authorization.split(" ", 1)[1], "access")
    session = await db.get(SessionModel, payload["sid"])
    if session:
        session.revoked = True
        await db.commit()
    return {"detail": "Signed out on this device."}


@router.post("/logout-all")
async def logout_all(user: User = Depends(current_user), db: AsyncSession = Depends(get_db)):
    await db.execute(update(SessionModel).where(SessionModel.user_id == user.id).values(revoked=True))
    await db.commit()
    return {"detail": "Signed out on all devices."}
