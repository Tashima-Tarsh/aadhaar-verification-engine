#!/bin/bash

echo ""
echo "=================================================="
echo "  Aadhaar Platform — Starting All Services"
echo "=================================================="

# ── Load environment ─────────────────────────────────────────────────────────
set -a; source .env; set +a
export PYTHONPATH=$(pwd)

# ── Start PostgreSQL ─────────────────────────────────────────────────────────
echo "[1/5] Starting PostgreSQL..."
sudo service postgresql start 2>/dev/null || true
sleep 2

# ── Start Redis ──────────────────────────────────────────────────────────────
echo "[2/5] Starting Redis..."
sudo service redis-server start 2>/dev/null || redis-server --daemonize yes 2>/dev/null || true
sleep 1

# ── Init DB tables if needed ─────────────────────────────────────────────────
python3 -c "
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
from src.db.models import Base
async def init():
    engine = create_async_engine(os.environ['DATABASE_URL'])
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
asyncio.run(init())
" 2>/dev/null || true

# ── Start Celery worker ──────────────────────────────────────────────────────
echo "[3/5] Starting Celery worker..."
celery -A src.workers.tasks worker \
  --loglevel=warning \
  -Q aadhaar_verification \
  --concurrency=8 \
  --detach \
  --logfile=/tmp/celery.log \
  --pidfile=/tmp/celery.pid 2>/dev/null || true
sleep 2

# ── Start FastAPI backend ────────────────────────────────────────────────────
echo "[4/5] Starting API server on port 8000..."
nohup uvicorn src.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  --log-level warning \
  > /tmp/api.log 2>&1 &
sleep 3

# ── Start Next.js frontend ───────────────────────────────────────────────────
echo "[5/5] Starting dashboard on port 3000..."
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 nohup npm run dev \
  > /tmp/frontend.log 2>&1 &
cd ..

# ── Wait and confirm ─────────────────────────────────────────────────────────
echo ""
echo "Waiting for services to be ready..."
sleep 8

API_OK=$(curl -s http://localhost:8000/health 2>/dev/null | grep -c "ok" || true)

echo ""
echo "=================================================="
if [ "$API_OK" -ge 1 ]; then
  echo "  ALL SERVICES RUNNING"
  echo ""
  echo "  Dashboard  → port 3000 (check PORTS tab)"
  echo "  API Docs   → port 8000/api/docs"
  echo ""
  echo "  Go to PORTS tab → click globe icon on port 3000"
else
  echo "  Services starting... check /tmp/api.log if needed"
  echo "  Run: curl http://localhost:8000/health"
fi
echo "=================================================="
echo ""
