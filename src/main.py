from fastapi import FastAPI
from src.api.v1.routes import verify
from src.config.settings import settings
import uvicorn

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI(
    title="Aadhaar Offline Verification Platform",
    version="1.0.0",
    description="Enterprise-grade identity verification service"
)

# Mount Static Files
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/dashboard")
async def get_dashboard():
    return FileResponse(os.path.join(static_path, "dashboard.html"))

# Include Routers
app.include_router(verify.router, prefix="/api/v1", tags=["Verification"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
