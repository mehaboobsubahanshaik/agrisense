from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.models import Session as SessionModel
from app.db.models import User
from app.db.session import get_db

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Your session has ended. Sign in again.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def current_user(
    authorization: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.lower().startswith("bearer "):
        raise CREDENTIALS_ERROR
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token, "access")
    except Exception:
        raise CREDENTIALS_ERROR

    session = await db.get(SessionModel, payload.get("sid", ""))
    if session is None or session.revoked:
        raise CREDENTIALS_ERROR

    user = (await db.execute(select(User).where(User.id == payload["sub"]))).scalar_one_or_none()
    if user is None or not user.is_active:
        raise CREDENTIALS_ERROR
    return user


def require_roles(*roles: str):
    async def _guard(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="You do not have access to this area.")
        return user

    return _guard
