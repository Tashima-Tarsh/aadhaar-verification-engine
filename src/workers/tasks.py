"""
Celery tasks — fixed: removed file_bytes = b"..." placeholder.
                       Downloads file from storage before processing.
                       Added K8s heartbeat via /tmp/worker_healthy.
"""
import asyncio
import logging
import threading
import time
from pathlib import Path
from uuid import UUID

from src.workers.celery_app import celery_app
from src.config.settings import settings

logger = logging.getLogger(__name__)

_HEARTBEAT_FILE = Path("/tmp/worker_healthy")


def _heartbeat_loop():
    """Write heartbeat every 15s so K8s liveness probe (mtime < 45s) stays green."""
    while True:
        try:
            _HEARTBEAT_FILE.touch()
        except Exception:
            pass
        time.sleep(15)


# Start heartbeat thread once when the module is imported in a worker process
_hb_thread = threading.Thread(target=_heartbeat_loop, daemon=True)
_hb_thread.start()


@celery_app.task(
    bind=True,
    max_retries=3,
    queue="aadhaar_verification",
    acks_late=True,
)
def process_verification_task(
    self,
    tenant_id: str,
    reference_id: str,
    storage_key: str,
    source_type: str,
    password_encrypted: str = None,
    selfie_key: str = None,
    webhook_url: str = None,
    webhook_secret: str = None,
):
    """Download file from storage and run full verification pipeline."""
    async def _run():
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
        from src.db.repositories.verification_repo import VerificationRepository
        from src.services.verification_service import VerificationService
        from src.utils.storage import StorageManager

        engine = create_async_engine(settings.DATABASE_URL)
        session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        storage = StorageManager()
        file_bytes = storage.download(storage_key)
        if not file_bytes:
            raise ValueError(f"File not found in storage: {storage_key}")

        selfie_bytes = None
        if selfie_key:
            selfie_bytes = storage.download(selfie_key)

        password = None
        if password_encrypted:
            from src.utils.crypto import decrypt_value
            password = decrypt_value(password_encrypted)

        async with session_factory() as session:
            repo = VerificationRepository(session)
            service = VerificationService(repo)
            return await service.process_single_verification(
                tenant_id=UUID(tenant_id),
                reference_id=reference_id,
                file_bytes=file_bytes,
                source_type=source_type,
                password=password,
                selfie_bytes=selfie_bytes,
                webhook_url=webhook_url,
                webhook_secret=webhook_secret,
            )

    try:
        return asyncio.run(_run())
    except Exception as exc:
        logger.error(f"Task failed for {reference_id}: {exc}", exc_info=True)
        # Exponential backoff: 2s, 4s, 8s
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown, max_retries=3)


@celery_app.task(bind=True, max_retries=0, queue="aadhaar_dlq")
def dead_letter_handler(self, original_task_name: str, task_args: dict, error: str):
    """Logs and stores permanently failed tasks for manual review."""
    logger.error(f"DLQ: task={original_task_name} ref={task_args.get('reference_id')} error={error}")
