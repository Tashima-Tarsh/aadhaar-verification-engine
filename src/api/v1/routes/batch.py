import uuid
import logging
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies.auth import get_current_tenant
from src.api.v1.schemas.verify import BulkSubmitResponseSchema, BulkStatusSchema, VerifyResponseSchema
from src.core.database import get_db
from src.db.models import Tenant, BulkJob
from src.db.repositories.verification_repo import VerificationRepository
from src.utils.crypto import encrypt_value
from src.utils.storage import storage
from src.workers.tasks import process_verification_task
from src.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_BULK = 500


@router.post("/batch", response_model=BulkSubmitResponseSchema, status_code=status.HTTP_202_ACCEPTED)
async def submit_bulk(
    files: List[UploadFile] = File(...),
    password: str = Form(None),
    webhook_url: str = Form(None),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Submit up to 500 Aadhaar documents for bulk offline verification."""
    if len(files) > MAX_BULK:
        raise HTTPException(status_code=400, detail=f"Max {MAX_BULK} files per batch")
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    password_encrypted = encrypt_value(password) if password else None
    effective_webhook = webhook_url or tenant.webhook_url

    bulk_job = BulkJob(
        tenant_id=tenant.id,
        status="QUEUED",
        total_count=len(files),
        webhook_url=effective_webhook,
    )
    db.add(bulk_job)
    await db.flush()

    repo = VerificationRepository(db)

    for f in files:
        raw = await f.read()
        if not raw:
            continue

        source_type = "IMAGE"
        fn = (f.filename or "").lower()
        ct = (f.content_type or "").lower()
        if "pdf" in ct or fn.endswith(".pdf"):
            source_type = "PDF"
        elif fn.endswith(".xml") or "xml" in ct:
            source_type = "XML"

        storage_key = storage.save_upload(raw, f.filename or f"upload.{source_type.lower()}")
        reference_id = f"bulk-{bulk_job.id}-{uuid.uuid4().hex[:8]}"

        request = await repo.create_request({
            "reference_id": reference_id,
            "tenant_id": tenant.id,
            "bulk_job_id": bulk_job.id,
            "source_type": source_type,
            "status": "PENDING",
        })

        process_verification_task.apply_async(
            kwargs={
                "tenant_id": str(tenant.id),
                "reference_id": reference_id,
                "storage_key": storage_key,
                "source_type": source_type,
                "password_encrypted": password_encrypted,
                "webhook_url": effective_webhook,
                "webhook_secret": tenant.webhook_secret,
            },
            queue="aadhaar_verification",
        )

    await db.commit()

    return {
        "job_id": bulk_job.id,
        "status": "QUEUED",
        "total_count": len(files),
        "message": f"{len(files)} documents queued for processing",
    }


@router.get("/batch/{job_id}/status", response_model=BulkStatusSchema)
async def get_batch_status(
    job_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    result = await db.execute(select(BulkJob).where(BulkJob.id == job_id, BulkJob.tenant_id == tenant.id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    return {
        "job_id": job.id,
        "status": job.status,
        "total_count": job.total_count,
        "completed_count": job.completed_count,
        "failed_count": job.failed_count,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
    }


@router.get("/batch/{job_id}/results")
async def get_batch_results(
    job_id: uuid.UUID,
    page: int = 1,
    page_size: int = 50,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    from sqlalchemy import select
    from src.db.models import VerificationRequest

    result = await db.execute(select(BulkJob).where(BulkJob.id == job_id, BulkJob.tenant_id == tenant.id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Batch job not found")

    offset = (page - 1) * page_size
    result = await db.execute(
        select(VerificationRequest)
        .where(VerificationRequest.bulk_job_id == job_id)
        .offset(offset)
        .limit(page_size)
    )
    requests = result.scalars().all()

    items = []
    for req in requests:
        item = {
            "request_id": str(req.id),
            "reference_id": req.reference_id,
            "status": req.status,
        }
        if req.result:
            r = req.result
            item.update({
                "qr_valid": r.qr_valid,
                "name": r.full_name,
                "risk_score": r.risk_score,
                "error_code": r.error_code,
            })
        items.append(item)

    return {
        "job_id": str(job_id),
        "page": page,
        "page_size": page_size,
        "total": job.total_count,
        "results": items,
    }
