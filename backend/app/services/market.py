"""Live market prices from the Government of India open data platform.

Source: data.gov.in resource 9ef84268-d588-465a-a308-a864a43d0070, "Current
daily price of various commodities from various markets (Mandi)", published by
the Directorate of Marketing and Inspection. It is updated every working day.

Honesty rules for anything shown as "live":
  * every response carries `as_of` and `source`, so a farmer can see how fresh
    the number is rather than trusting a stale figure;
  * when the API is unreachable we say so and return the last cached snapshot
    with its real timestamp - we never invent a price;
  * we never fabricate a modal price for a commodity the mandi did not report.

A free key takes a minute to register at data.gov.in. Without one, the platform's
published sample key is used, which is rate limited but works for a demo.
"""
import logging
from datetime import datetime, timezone

import httpx

from app.core.config import settings
from app.core.redis_client import get_redis

log = logging.getLogger(__name__)

RESOURCE_ID = "9ef84268-d588-465a-a308-a864a43d0070"
BASE = f"https://api.data.gov.in/resource/{RESOURCE_ID}"
CACHE_TTL = 3 * 3600          # mandi data changes once a working day
TIMEOUT = 20.0

# Commodity names as the mandi reports them, keyed by our canonical crop names.
COMMODITY_ALIAS = {
    "rice": "Paddy(Dhan)(Common)",
    "wheat": "Wheat",
    "maize": "Maize",
    "cotton": "Cotton",
    "groundnut": "Groundnut",
    "soybean": "Soyabean",
    "chickpea": "Bengal Gram(Gram)(Whole)",
    "pigeonpea": "Arhar (Tur/Red Gram)(Whole)",
    "greengram": "Green Gram (Moong)(Whole)",
    "onion": "Onion",
    "tomato": "Tomato",
    "chilli": "Dry Chillies",
    "turmeric": "Turmeric",
    "banana": "Banana",
    "sugarcane": "Sugarcane",
}


def _key(state: str, commodity: str) -> str:
    return f"market:{(state or 'all').lower()}:{(commodity or 'all').lower()}"


async def _fetch(state: str = "", commodity: str = "", limit: int = 40) -> list[dict]:
    params = {
        "api-key": settings.DATA_GOV_API_KEY,
        "format": "json",
        "limit": limit,
    }
    if state:
        params["filters[state.keyword]"] = state
    if commodity:
        params["filters[commodity]"] = commodity

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        r = await client.get(BASE, params=params)
        r.raise_for_status()
        payload = r.json()

    records = payload.get("records") or []
    out: list[dict] = []
    for rec in records:
        try:
            modal = float(rec.get("modal_price") or 0)
        except (TypeError, ValueError):
            continue
        if modal <= 0:                       # a zero modal price means "not reported"
            continue
        out.append(
            {
                "commodity": rec.get("commodity", ""),
                "variety": rec.get("variety", ""),
                "market": rec.get("market", ""),
                "district": rec.get("district", ""),
                "state": rec.get("state", ""),
                # The API reports rupees per quintal.
                "min_price": _num(rec.get("min_price")),
                "max_price": _num(rec.get("max_price")),
                "modal_price": modal,
                "arrival_date": rec.get("arrival_date", ""),
            }
        )
    return out


def _num(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


async def prices(state: str = "", commodity: str = "", limit: int = 40) -> dict:
    """Live mandi prices, cached, with the freshness always stated."""
    import json

    key = _key(state, commodity)
    redis = None
    try:
        redis = get_redis()
        hit = await redis.get(key)
        if hit:
            cached = json.loads(hit)
            cached["cached"] = True
            return cached
    except Exception:
        pass

    try:
        records = await _fetch(state, commodity, limit)
        result = {
            "records": records,
            "count": len(records),
            "as_of": _latest_date(records),
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "data.gov.in - Directorate of Marketing and Inspection (daily mandi prices)",
            "source_url": "https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi",
            "live": True,
            "cached": False,
        }
        if redis is not None:
            try:
                await redis.setex(key, CACHE_TTL, json.dumps(result))
            except Exception:
                pass
        return result

    except Exception as exc:
        log.warning("mandi price fetch failed (%s); returning stale-or-empty", exc)
        stale = None
        if redis is not None:
            try:
                raw = await redis.get(key + ":last")
                stale = json.loads(raw) if raw else None
            except Exception:
                stale = None
        if stale:
            stale["live"] = False
            stale["notice"] = "Live market feed unreachable. These are the last prices we received."
            return stale
        return {
            "records": [],
            "count": 0,
            "as_of": None,
            "source": "data.gov.in (unreachable)",
            "live": False,
            "cached": False,
            "notice": (
                "Live mandi prices are not reachable right now. Check the Agmarknet portal "
                "or call the Kisan Call Centre on 1800-180-1551 for today's rate."
            ),
        }


def _latest_date(records: list[dict]) -> str | None:
    dates = [r["arrival_date"] for r in records if r.get("arrival_date")]
    return max(dates) if dates else None


async def summary_for_crop(crop: str, state: str = "") -> dict:
    """One crop, aggregated across the markets that reported it.

    Used by the chat so a price question is answered from today's mandi data
    rather than from a static document.
    """
    commodity = COMMODITY_ALIAS.get((crop or "").lower(), crop)
    data = await prices(state=state, commodity=commodity, limit=60)
    records = data.get("records") or []
    if not records:
        return {"crop": crop, "commodity": commodity, "available": False, **data}

    modal = sorted(r["modal_price"] for r in records)
    mid = modal[len(modal) // 2]
    best = max(records, key=lambda r: r["modal_price"])
    return {
        "crop": crop,
        "commodity": commodity,
        "available": True,
        "median_modal_price": round(mid, 2),
        "lowest": round(modal[0], 2),
        "highest": round(modal[-1], 2),
        "best_market": {
            "market": best["market"],
            "district": best["district"],
            "state": best["state"],
            "modal_price": best["modal_price"],
        },
        "markets_reporting": len(records),
        "unit": "rupees per quintal",
        "as_of": data.get("as_of"),
        "source": data.get("source"),
        "live": data.get("live", False),
    }


def as_chat_context(summary: dict) -> str:
    """Flatten a price summary into evidence the LLM can quote."""
    if not summary.get("available"):
        return ""
    b = summary["best_market"]
    return (
        f"LIVE MANDI PRICE for {summary['crop']} ({summary['commodity']}), "
        f"reported {summary.get('as_of') or 'recently'} by {summary['markets_reporting']} markets: "
        f"median modal price {summary['median_modal_price']} rupees per quintal, "
        f"range {summary['lowest']} to {summary['highest']}. "
        f"Highest today: {b['market']} in {b['district']}, {b['state']} at {b['modal_price']}. "
        f"Source: {summary.get('source')}."
    )
