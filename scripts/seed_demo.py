"""Populate a demo account so a presentation opens with a full dashboard.

    docker compose exec backend python -m scripts.seed_demo   # (copy into the image first)
    or run locally:  python scripts/seed_demo.py 9999999999
"""
import asyncio
import sys

import httpx

BASE = "http://localhost:8080/api/v1"


async def main(phone: str) -> None:
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{BASE}/auth/request-otp", json={"phone": phone})
        otp = r.json().get("dev_otp")
        if not otp:
            print("DEV_MODE is off - read the code from the backend log and pass it manually.")
            return
        r = await c.post(f"{BASE}/auth/verify-otp", json={"phone": phone, "otp": otp})
        token = r.json()["access_token"]
        h = {"Authorization": f"Bearer {token}"}

        await c.post(f"{BASE}/soil/analyze", headers=h, json={
            "crop": "rice", "n": 235, "p": 11, "k": 190, "ph": 6.4, "oc": 0.42,
            "moisture": 24, "area_acres": 2.5})
        await c.post(f"{BASE}/yield/predict", headers=h, json={
            "crop": "rice", "area_acres": 2.5, "soil_score": 62, "rainfall_mm": 900,
            "irrigation": "borewell", "disease_pressure": "medium", "fertilizer_applied": True})
        await c.post(f"{BASE}/chat", headers=h, json={
            "message": "Grey spots with brown edges on my paddy leaves. What do I spray?", "language": "en"})
        print("Demo data seeded for", phone)


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "9999999999"))
