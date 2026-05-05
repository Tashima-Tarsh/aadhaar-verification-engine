#!/bin/bash

echo ""
echo "=================================================="
echo "  Aadhaar Verification Platform — Starting..."
echo "=================================================="

export PYTHONPATH=$(pwd)
set -a; source .env 2>/dev/null || true; set +a

# PostgreSQL
echo "→ Starting PostgreSQL..."
sudo service postgresql start 2>/dev/null || true
sleep 2
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" 2>/dev/null || true
sudo -u postgres createdb aadhaar_platform 2>/dev/null || true

# DB tables
python3 -c "
import asyncio, os
from sqlalchemy.ext.asyncio import create_async_engine
from src.db.models import Base
async def init():
    e = create_async_engine(os.environ['DATABASE_URL'])
    async with e.begin() as c:
        await c.run_sync(Base.metadata.create_all)
    await e.dispose()
asyncio.run(init())
" 2>/dev/null && echo "  DB tables ready." || echo "  DB tables pending."

# Redis
echo "→ Starting Redis..."
sudo service redis-server start 2>/dev/null || redis-server --daemonize yes 2>/dev/null || true
sleep 1

# Celery
echo "→ Starting Celery worker..."
pkill -f "celery worker" 2>/dev/null || true
celery -A src.workers.tasks worker \
  --loglevel=error -Q aadhaar_verification \
  --concurrency=8 --detach \
  --logfile=/tmp/celery.log \
  --pidfile=/tmp/celery.pid 2>/dev/null || true

# API
echo "→ Starting API on port 8000..."
pkill -f "uvicorn src.main" 2>/dev/null || true
sleep 1
nohup uvicorn src.main:app \
  --host 0.0.0.0 --port 8000 \
  --workers 2 --log-level warning \
  > /tmp/api.log 2>&1 &

# Wait for API
echo "  Waiting for API..."
for i in {1..15}; do
  if curl -s http://localhost:8000/health | grep -q "ok"; then
    echo "  ✅ API is live on port 8000"
    break
  fi
  sleep 2
done

# Frontend
echo "→ Starting Dashboard on port 3000..."
pkill -f "next" 2>/dev/null || true
cd frontend
NEXT_PUBLIC_API_URL=http://localhost:8000 \
  nohup npm start > /tmp/frontend.log 2>&1 &
cd ..

# Wait for Dashboard
echo "  Waiting for Dashboard..."
for i in {1..20}; do
  if curl -s http://localhost:3000 | grep -q "html"; then
    echo "  ✅ Dashboard is live on port 3000"
    break
  fi
  sleep 3
done

echo ""
echo "=================================================="
echo "  PLATFORM IS RUNNING"
echo ""
echo "  Dashboard  → Go to PORTS tab, click 🌐 port 3000"
echo "  API Docs   → Go to PORTS tab, click 🌐 port 8000"
echo "             → then add /api/docs to the URL"
echo ""
echo "  First time: create a tenant account:"
echo "  curl -X POST http://localhost:8000/api/v1/tenants \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"name\": \"MyCompany\"}'"
echo "=================================================="
