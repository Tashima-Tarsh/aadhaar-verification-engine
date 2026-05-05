#!/bin/bash
export PYTHONPATH=/workspaces/aadhaar-verification-engine
cd /workspaces/aadhaar-verification-engine
set -a; source .env 2>/dev/null || true; set +a

# Start PostgreSQL
sudo service postgresql start 2>/dev/null || true
sleep 2
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';" 2>/dev/null || true
sudo -u postgres createdb aadhaar_platform 2>/dev/null || true

# Create DB tables
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
" 2>/dev/null || true

# Start Redis
sudo service redis-server start 2>/dev/null || redis-server --daemonize yes 2>/dev/null || true

# Start Celery in background
celery -A src.workers.tasks worker \
  --loglevel=error -Q aadhaar_verification \
  --concurrency=8 --detach \
  --logfile=/tmp/celery.log \
  --pidfile=/tmp/celery.pid 2>/dev/null || true

# Start API — foreground so Codespaces detects port 8000 and opens browser
exec uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1 --log-level warning
