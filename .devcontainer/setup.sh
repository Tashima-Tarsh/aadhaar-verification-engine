#!/bin/bash
set -e

echo ""
echo "=================================================="
echo "  Aadhaar Platform — Installing Dependencies"
echo "=================================================="

# ── Python dependencies ──────────────────────────────────────────────────────
echo "[1/5] Installing Python packages..."
pip install --quiet --upgrade pip
pip install --quiet \
  fastapi uvicorn[standard] sqlalchemy[asyncio] aiosqlite asyncpg \
  pydantic pydantic-settings python-jose[cryptography] passlib[bcrypt] \
  python-multipart celery[redis] redis kombu \
  cryptography pillow opencv-python-headless numpy \
  pyzbar zxing-cpp qreader \
  pikepdf pyzipper lxml \
  boto3 pandas aiofiles \
  structlog sentry-sdk[fastapi] \
  httpx pytest pytest-asyncio
echo "    Python packages installed."

# ── Node / frontend dependencies ─────────────────────────────────────────────
echo "[2/5] Installing frontend dependencies..."
cd frontend && npm install --silent 2>/dev/null || true && cd ..
echo "    Frontend dependencies installed."

# ── Generate .env ────────────────────────────────────────────────────────────
echo "[3/5] Generating .env..."
ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")

cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/aadhaar_platform
REDIS_URL=redis://localhost:6379/0
STORAGE_ENDPOINT=http://localhost:9000
STORAGE_ACCESS_KEY=minioadmin
STORAGE_SECRET_KEY=minioadmin
STORAGE_BUCKET=aadhaar-platform
UIDAI_PUBLIC_KEY_PATH=certs/uidai_offline_publickey_2026.cer
ENCRYPTION_KEY=${ENCRYPTION_KEY}
JWT_SECRET=${JWT_SECRET}
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
API_PREFIX=/api/v1
APP_VERSION=1.0.0
RATE_LIMIT_PER_MINUTE=100
MAX_BULK_UPLOAD_MB=500
MAX_BULK_FILES=500
WEBHOOK_RETRY_COUNT=3
LIVENESS_ENABLED=false
LOG_LEVEL=INFO
SENTRY_DSN=
EOF
echo "    .env created."

# ── Create PostgreSQL database ───────────────────────────────────────────────
echo "[4/5] Setting up PostgreSQL database..."
sudo service postgresql start 2>/dev/null || true
sleep 2
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" 2>/dev/null || true
sudo -u postgres createdb aadhaar_platform 2>/dev/null || true
echo "    Database ready."

# ── Init DB tables ───────────────────────────────────────────────────────────
echo "[5/5] Creating database tables..."
PYTHONPATH=$(pwd) python3 -c "
import asyncio, os
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5432/aadhaar_platform'
from sqlalchemy.ext.asyncio import create_async_engine
from src.db.models import Base
async def init():
    engine = create_async_engine(os.environ['DATABASE_URL'])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
asyncio.run(init())
" 2>/dev/null && echo "    Tables created." || echo "    Tables will be created on first start."

echo ""
echo "=================================================="
echo "  Setup complete. Starting services now..."
echo "=================================================="
