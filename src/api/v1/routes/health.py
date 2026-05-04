import time
import logging

from fastapi import APIRouter
from sqlalchemy import text

from src.core.database import async_session_factory
from src.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
async def health_live():
    return {"status": "ok", "timestamp": time.time(), "version": settings.APP_VERSION}


@router.get("/health/ready")
async def health_ready():
    checks: dict = {}

    # DB check
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Redis check
    try:
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "ready" if all_ok else "degraded",
        "checks": checks,
        "timestamp": time.time(),
    }
