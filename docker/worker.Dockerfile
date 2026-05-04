# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libzbar0 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir ".[liveness]" || pip install --no-cache-dir .

# Production stage
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libzbar0 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src/ ./src/
COPY certs/ ./certs/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# K8s liveness probe: worker writes heartbeat every 15s; probe checks file age < 45s
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=30s \
  CMD python3 -c "import os,time; age=time.time()-os.path.getmtime('/tmp/worker_healthy'); exit(0 if age<45 else 1)"

CMD ["celery", "-A", "src.workers.tasks", "worker", "--loglevel=info", "-Q", "aadhaar_verification", "--concurrency=4"]
