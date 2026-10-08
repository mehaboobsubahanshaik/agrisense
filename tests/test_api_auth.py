"""Integration test for the OTP flow.

Skipped automatically when Postgres/Redis are not reachable, so `pytest tests`
works on a laptop without the stack running. CI provides both services.
"""
import os

import pytest

pytestmark = pytest.mark.asyncio

try:
    import redis.asyncio  # noqa: F401
    from httpx import ASGITransport, AsyncClient
except Exception:  # pragma: no cover
    pytest.skip("http/redis client unavailable", allow_module_level=True)


async def _client():
    from app.main import app

    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


async def _stack_ready() -> bool:
    try:
        from app.core.redis_client import get_redis
        from app.db.session import engine
        from sqlalchemy import text

        await get_redis().ping()
        async with engine.connect() as c:
            await c.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def test_full_otp_login_flow():
    if not await _stack_ready():
        pytest.skip("postgres/redis not running")

    from app.db.models import Base
    from app.db.session import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    phone = "9" + os.urandom(2).hex().rjust(9, "0")[:9]
    async with await _client() as c:
        r = await c.post("/api/v1/auth/request-otp", json={"phone": phone})
        assert r.status_code == 200
        body = r.json()
        assert body["expires_in"] == 300 and body["max_attempts"] == 5
        otp = body["dev_otp"]
        assert otp and len(otp) == 6

        # a second request inside the 30-second window must be refused
        again = await c.post("/api/v1/auth/request-otp", json={"phone": phone})
        assert again.status_code == 429

        wrong = await c.post("/api/v1/auth/verify-otp", json={"phone": phone, "otp": "000000"})
        assert wrong.status_code == 400

        ok = await c.post("/api/v1/auth/verify-otp", json={"phone": phone, "otp": otp})
        assert ok.status_code == 200
        tokens = ok.json()
        assert tokens["user"]["phone"] == phone

        me = await c.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
        assert me.status_code == 200

        # the code is single use
        reuse = await c.post("/api/v1/auth/verify-otp", json={"phone": phone, "otp": otp})
        assert reuse.status_code == 400


async def test_protected_route_rejects_missing_token():
    if not await _stack_ready():
        pytest.skip("postgres/redis not running")
    async with await _client() as c:
        r = await c.get("/api/v1/dashboard/summary")
        assert r.status_code == 401
