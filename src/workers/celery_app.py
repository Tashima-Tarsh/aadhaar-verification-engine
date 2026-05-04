from celery import Celery
from src.config.settings import settings

celery_app = Celery(
    "aadhaar_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.task_routes = {
    "src.workers.tasks.*": {"queue": "aadhaar_verification"}
}

# Reliability settings
celery_app.conf.task_acks_late = True
celery_app.conf.task_reject_on_worker_lost = True
celery_app.conf.worker_prefetch_multiplier = 1

# Retry / DLQ config
celery_app.conf.task_max_retries = 3
celery_app.conf.task_default_retry_delay = 2   # seconds, overridden per-task with exponential

celery_app.conf.update(
    result_expires=3600,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Dead-letter: failed tasks after max_retries go to dedicated queue
    task_queues={
        "aadhaar_verification": {"exchange": "aadhaar_verification"},
        "aadhaar_dlq":          {"exchange": "aadhaar_dlq"},
    },
)
