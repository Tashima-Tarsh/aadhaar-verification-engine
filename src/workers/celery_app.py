from celery import Celery
from kombu import Queue, Exchange
from src.config.settings import settings

celery_app = Celery(
    "aadhaar_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# ── Routing ────────────────────────────────────────────────────────────────
celery_app.conf.task_routes = {
    "src.workers.tasks.process_verification_task": {"queue": "aadhaar_verification"},
    "src.workers.tasks.dead_letter_handler":        {"queue": "aadhaar_dlq"},
}

# ── Reliability (at-least-once delivery) ──────────────────────────────────
celery_app.conf.task_acks_late = True
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.worker_prefetch_multiplier = 1      # one task at a time per worker slot

# ── Retry / DLQ ───────────────────────────────────────────────────────────
celery_app.conf.task_max_retries = 3
celery_app.conf.task_default_retry_delay = 2

# ── Throughput tuning for 5 000 verifications/day ─────────────────────────
# 5 000/day = 208/hr = ~3.5/min peak.
# 8 concurrent slots across 2 workers handles 10x this comfortably.
celery_app.conf.worker_concurrency = 8              # overridden by --concurrency CLI flag
celery_app.conf.task_soft_time_limit = 55           # warn at 55 s
celery_app.conf.task_time_limit      = 90           # hard kill at 90 s
celery_app.conf.worker_max_tasks_per_child = 200    # recycle worker after 200 tasks (prevents memory leak)

# ── Redis broker pool ─────────────────────────────────────────────────────
celery_app.conf.broker_pool_limit         = 20
celery_app.conf.broker_connection_retry_on_startup = True

celery_app.conf.update(
    result_expires=86400,           # keep results 24 h for status polling
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_queues=(
        Queue("aadhaar_verification", Exchange("aadhaar_verification"), routing_key="aadhaar_verification"),
        Queue("aadhaar_dlq",          Exchange("aadhaar_dlq"),          routing_key="aadhaar_dlq"),
    ),
)
