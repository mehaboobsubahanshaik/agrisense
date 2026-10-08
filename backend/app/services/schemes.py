"""Keeping the scheme catalogue current, and being straight about how.

There is no public API that serves the full text of Indian agricultural schemes.
myscheme.gov.in has no open endpoint, and data.gov.in publishes datasets rather
than a maintained scheme catalogue. Pretending otherwise would mean scraping
pages that change layout without notice and silently showing farmers wrong
eligibility rules - the worst possible failure for this feature.

So the design is:

  1. A curated catalogue with the benefit, eligibility, documents and application
     route for each scheme, written from the official portals.
  2. A scheduled job that checks each official link is still live and stamps
     `last_verified`. A dead link is the strongest available signal that a scheme
     has moved or closed, and it gets flagged rather than hidden.
  3. Every scheme carries its official URL, and the UI sends the farmer there for
     the final word. We are a signpost, not the source of truth.
  4. Genuinely live data - today's mandi prices - comes from a real government
     API and is labelled with its own timestamp (see services/market.py).

`last_verified` is therefore an honest claim: the link was reachable at that
moment. It does not claim the eligibility text was re-read by a human.
"""
import asyncio
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select

from app.db.models import GovernmentScheme
from app.db.session import SessionLocal

log = logging.getLogger(__name__)

TIMEOUT = 12.0
CONCURRENCY = 4


async def _check(client: httpx.AsyncClient, url: str) -> str:
    if not url:
        return "unchecked"
    try:
        r = await client.head(url, follow_redirects=True)
        if r.status_code >= 400:                 # some gov portals reject HEAD
            r = await client.get(url, follow_redirects=True)
        return "ok" if r.status_code < 400 else "unreachable"
    except Exception as exc:
        log.info("scheme link check failed for %s: %s", url, exc)
        return "unreachable"


async def refresh() -> dict:
    """Verify every scheme link and stamp the result. Safe to run on a schedule."""
    now = datetime.now(timezone.utc)
    checked = ok = broken = 0

    async with SessionLocal() as db:
        schemes = (await db.execute(select(GovernmentScheme))).scalars().all()
        sem = asyncio.Semaphore(CONCURRENCY)

        async with httpx.AsyncClient(
            timeout=TIMEOUT,
            headers={"User-Agent": "AgriSense-AI/1.0 (scheme link verification)"},
        ) as client:

            async def one(scheme: GovernmentScheme) -> None:
                nonlocal checked, ok, broken
                async with sem:
                    status = await _check(client, scheme.link)
                scheme.link_status = status
                scheme.last_verified = now
                checked += 1
                if status == "ok":
                    ok += 1
                elif status == "unreachable":
                    broken += 1
                    log.warning("scheme %s link unreachable: %s", scheme.code, scheme.link)

            await asyncio.gather(*(one(s) for s in schemes))

        await db.commit()

    log.info("scheme refresh: %d checked, %d ok, %d unreachable", checked, ok, broken)
    return {"checked": checked, "ok": ok, "unreachable": broken, "at": now.isoformat()}


def freshness_label(scheme: GovernmentScheme) -> dict:
    """What the UI shows next to a scheme, in plain terms."""
    if not scheme.last_verified:
        return {"state": "unchecked", "text": "Not yet verified - open the official page"}
    days = (datetime.now(timezone.utc) - scheme.last_verified).days
    if scheme.link_status == "unreachable":
        return {
            "state": "broken",
            "text": "Official page did not respond when last checked. Confirm at the district agriculture office.",
        }
    when = "today" if days == 0 else ("yesterday" if days == 1 else f"{days} days ago")
    return {"state": "ok", "text": f"Official link verified {when}"}
