import os
import time
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from src.config.settings import settings
from src.api.v1.routes import verify, auth, batch, reports, health, storage

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Aadhaar Offline Verification Platform",
    version=settings.APP_VERSION,
    description="Enterprise-grade Aadhaar identity verification — offline only, no UIDAI online APIs",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = request.headers.get("X-Request-ID", uuid.uuid4().hex)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Static dashboard
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_path):
    app.mount("/static", StaticFiles(directory=static_path), name="static")

    @app.get("/", include_in_schema=False)
    async def root():
        return FileResponse(os.path.join(static_path, "dashboard.html"))

    @app.get("/dashboard", include_in_schema=False)
    async def get_dashboard():
        return FileResponse(os.path.join(static_path, "dashboard.html"))


# API routers
PREFIX = "/api/v1"
app.include_router(health.router,   tags=["Health"])
app.include_router(auth.router,     prefix=PREFIX, tags=["Auth"])
app.include_router(verify.router,   prefix=PREFIX, tags=["Verification"])
app.include_router(batch.router,    prefix=PREFIX, tags=["Bulk"])
app.include_router(reports.router,  prefix=PREFIX, tags=["Reports"])
app.include_router(storage.router,  prefix=PREFIX, tags=["Storage"])


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=False)
