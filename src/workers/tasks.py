from src.workers.celery_app import celery_app
from src.services.verification_service import VerificationService
from src.db.repositories.verification_repo import VerificationRepository
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.config.settings import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

# Manual async session management for Celery workers
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@celery_app.task(bind=True, max_retries=3)
def process_verification_task(self, tenant_id: str, reference_id: str, file_path: str, source_type: str):
    """Background task to process a single Aadhaar verification."""
    async def _run():
        async with AsyncSessionLocal() as session:
            repo = VerificationRepository(session)
            service = VerificationService(repo)
            
            # In real scenario, download file from S3 first
            # Here we mock the file_bytes for demonstration
            file_bytes = b"..." 
            
            try:
                await service.process_single_verification(
                    tenant_id=tenant_id,
                    reference_id=reference_id,
                    file_bytes=file_bytes,
                    source_type=source_type
                )
            except Exception as e:
                logger.error(f"Task failed for {reference_id}: {e}")
                # Retry with exponential backoff
                self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

    return asyncio.run(_run())
