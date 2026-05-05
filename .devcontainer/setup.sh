#!/bin/bash
set -e

echo ""
echo "=================================================="
echo "  Aadhaar Verification Platform — Codespace Setup"
echo "=================================================="
echo ""

# ── 1. Generate .env if not present ─────────────────────────────────────────
if [ ! -f ".env" ]; then
  echo "[1/4] Generating .env with secure keys..."
  ENCRYPTION_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(48))")

  cat > .env <<EOF
DATABASE_URL=postgresql+asyncpg://admin:password@db:5432/aadhaar_platform
REDIS_URL=redis://redis:6379/0
STORAGE_ENDPOINT=http://minio:9000
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
  echo "    .env created with auto-generated secure keys."
else
  echo "[1/4] .env already exists — skipping."
fi

# ── 2. Verify UIDAI cert is present ─────────────────────────────────────────
echo "[2/4] Checking UIDAI certificate..."
if [ -f "certs/uidai_offline_publickey_2026.cer" ]; then
  echo "    UIDAI offline public key found (valid until Feb 2029)."
else
  echo "    WARNING: UIDAI cert not found at certs/uidai_offline_publickey_2026.cer"
  echo "    Signature validation will be skipped. Add the cert and restart."
fi

# ── 3. Pull Docker images in background ─────────────────────────────────────
echo "[3/4] Pre-pulling Docker base images (speeds up first start)..."
docker pull postgres:15-alpine &
docker pull redis:7-alpine &
docker pull minio/minio &
wait
echo "    Base images ready."

# ── 4. Done ─────────────────────────────────────────────────────────────────
echo "[4/4] Setup complete."
echo ""
echo "=================================================="
echo "  Platform will start automatically."
echo "  Once ready, open the PORTS tab and click"
echo "  the globe icon next to port 3000."
echo ""
echo "  Dashboard  → port 3000"
echo "  API Docs   → port 8000/api/docs"
echo "  MinIO      → port 9001"
echo "  n8n        → port 5678"
echo "=================================================="
echo ""
