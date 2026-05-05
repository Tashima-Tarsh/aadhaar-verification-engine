#!/bin/bash
set -e

echo "=================================================="
echo "  Installing platform dependencies (one-time)..."
echo "=================================================="

# Python packages
echo "→ Python packages..."
pip install --quiet --upgrade pip
pip install --quiet \
  fastapi "uvicorn[standard]" "sqlalchemy[asyncio]" aiosqlite asyncpg \
  pydantic "pydantic-settings" "python-jose[cryptography]" "passlib[bcrypt]" \
  python-multipart "celery[redis]" redis \
  cryptography pillow opencv-python-headless numpy \
  pyzbar "zxing-cpp" pikepdf pyzipper lxml \
  boto3 pandas aiofiles structlog

# Frontend build (pre-built so port 3000 opens instantly)
echo "→ Frontend build..."
cd frontend
npm install --silent 2>/dev/null || true
npm run build 2>/dev/null || true
cd ..

# Generate .env
echo "→ Generating .env..."
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
LOG_LEVEL=WARNING
SENTRY_DSN=
EOF

echo "=================================================="
echo "  Setup complete!"
echo "  Type: bash start.sh   to launch the platform"
echo "=================================================="
