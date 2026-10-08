from fastapi import APIRouter, Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import current_user, require_roles
from app.db.models import GovernmentScheme, User
from app.db.session import get_db
from app.services import schemes as scheme_service

router = APIRouter(prefix="/schemes", tags=["schemes"])


@router.get("")
async def list_schemes(
    state: str | None = None,
    category: str | None = None,
    q: str | None = None,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(GovernmentScheme)
    if state:
        stmt = stmt.where(or_(GovernmentScheme.state == state, GovernmentScheme.state == "All India"))
    if category:
        stmt = stmt.where(GovernmentScheme.category == category)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(or_(GovernmentScheme.name.ilike(like), GovernmentScheme.benefit.ilike(like)))
    stmt = stmt.where(GovernmentScheme.active.is_(True))
    rows = (await db.execute(stmt)).scalars().all()
    return [
        {
            "id": s.id, "code": s.code, "name": s.name, "category": s.category, "state": s.state,
            "benefit": s.benefit, "eligibility": s.eligibility, "documents": s.documents,
            "how_to_apply": s.how_to_apply, "link": s.link,
            # Freshness is shown, never implied.
            "last_verified": s.last_verified,
            "link_status": s.link_status,
            "freshness": scheme_service.freshness_label(s),
            "source_note": s.source_note,
        }
        for s in rows
    ]


@router.post("/refresh")
async def refresh_schemes(user: User = Depends(require_roles("admin"))):
    """Re-verify every official scheme link now. Also runs nightly via Celery."""
    return await scheme_service.refresh()
