import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.routes import advisory, auth, chat, dashboard, disease, misc, schemes, voice, weather
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.redis_client import close_redis, get_redis
from app.db.models import Base
from app.db.session import SessionLocal, engine
from app.seed import seed
from app.db import migrate
from app.services import llm, rag

setup_logging()
log = logging.getLogger("agrisense")


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)   # auto-migration on boot
    await migrate.run()                                 # idempotent ALTERs for older databases
    async with SessionLocal() as db:
        await seed(db)
    await rag.sync_to_chroma()
    await llm.warm_up()                                 # first question should not pay for index build
    log.info("AgriSense AI backend ready (env=%s)", settings.ENV)
    yield
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="AgriSense AI",
    version="1.0.0",
    description=(
        "AI advisory backend for smallholder farmers: passwordless OTP auth, RAG chat, "
        "crop disease detection, soil and fertiliser planning, weather advisories, "
        "yield prediction and government scheme lookup."
    ),
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    """Fixed-window limiter in Redis. Auth endpoints get a much tighter budget
    because they are the ones that cost money (SMS) when abused."""
    path = request.url.path
    if request.method == "OPTIONS" or path in ("/health", "/metrics"):
        return await call_next(request)

    ip = request.client.host if request.client else "anon"
    tight = path.startswith(f"{settings.API_V1}/auth")
    limit = 12 if tight else settings.RATE_LIMIT_REQUESTS
    window = 60 if tight else settings.RATE_LIMIT_WINDOW
    key = f"rl:{'auth' if tight else 'api'}:{ip}:{int(time.time() // window)}"
    try:
        r = get_redis()
        used = await r.incr(key)
        if used == 1:
            await r.expire(key, window)
        if used > limit:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Wait a minute and try again."},
            )
    except Exception:  # Redis down must not take the API down
        pass

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


for router in (auth.router, chat.router, disease.router, weather.router, advisory.router,
               schemes.router, dashboard.router, voice.router, misc.router):
    app.include_router(router, prefix=settings.API_V1)

app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR, check_dir=False), name="uploads")
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/health", tags=["system"])
async def health():
    checks = {"api": "ok"}
    try:
        await get_redis().ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "down"
    try:
        async with engine.connect() as conn:
            from sqlalchemy import text
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "down"
    healthy = checks["database"] == "ok"
    return JSONResponse(status_code=200 if healthy else 503,
                        content={"status": "healthy" if healthy else "degraded", "checks": checks,
                                 "version": app.version})


@app.get(f"{settings.API_V1}/config", tags=["system"])
async def public_config():
    return {
        "app": settings.APP_NAME,
        "dev_mode": settings.DEV_MODE,
        "otp": {
            "length": settings.OTP_LENGTH,
            "ttl_seconds": settings.OTP_TTL_SECONDS,
            "resend_after": settings.OTP_RESEND_SECONDS,
            "max_attempts": settings.OTP_MAX_ATTEMPTS,
        },
        "ai": {"llm": "gemini" if settings.GEMINI_API_KEY else "offline-rag",
               "weather": settings.WEATHER_PROVIDER},
    }
