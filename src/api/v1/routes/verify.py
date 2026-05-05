import uuid
import logging
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.v1.dependencies.auth import get_current_tenant
from src.api.v1.schemas.verify import VerifyResponseSchema
from src.core.database import get_db
from src.db.models import Tenant
from src.db.repositories.verification_repo import VerificationRepository
from src.services.verification_service import VerificationService
from src.utils.crypto import encrypt_value
from src.utils.storage import storage
from src.workers.tasks import process_verification_task

logger = logging.getLogger(__name__)
router = APIRouter()


def _detect_source_type(content_type: str, filename: str) -> str:
    ct = (content_type or "").lower()
    fn = (filename or "").lower()
    if "pdf" in ct or fn.endswith(".pdf"):
        return "PDF"
    if fn.endswith(".xml") or "xml" in ct:
        return "XML"
    return "IMAGE"


@router.post("/verify", response_model=VerifyResponseSchema, status_code=status.HTTP_202_ACCEPTED)
async def verify_aadhaar(
    file: UploadFile = File(...),
    reference_id: str = Form(..., max_length=128),
    password: Optional[str] = Form(None),
    enable_liveness: bool = Form(False),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    """Submit a single Aadhaar document (image/PDF/XML) for offline verification."""
    file_bytes = await file.read()
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 50 MB)")

    source_type = _detect_source_type(file.content_type, file.filename or "")
    storage_key = storage.save_upload(file_bytes, file.filename or f"upload.{source_type.lower()}")

    password_encrypted = None
    if password:
        password_encrypted = encrypt_value(password)

    repo = VerificationRepository(db)

    existing = await repo.get_request_by_reference(reference_id, tenant.id)
    if existing and existing.status == "COMPLETED":
        return {
            "request_id": existing.id,
            "reference_id": reference_id,
            "status": "COMPLETED",
            "processing_time_ms": 0,
        }

    request = await repo.create_request({
        "reference_id": reference_id,
        "tenant_id": tenant.id,
        "source_type": source_type,
        "status": "PENDING",
    })

    try:
        process_verification_task.apply_async(
            kwargs={
                "tenant_id": str(tenant.id),
                "reference_id": reference_id,
                "storage_key": storage_key,
                "source_type": source_type,
                "password_encrypted": password_encrypted,
                "webhook_url": tenant.webhook_url,
                "webhook_secret": tenant.webhook_secret,
            },
            queue="aadhaar_verification",
        )
    except Exception as e:
        logger.warning(f"Celery dispatch failed (broker unavailable): {e}. Request saved, will retry when broker reconnects.")

    return {
        "request_id": request.id,
        "reference_id": reference_id,
        "status": "PENDING",
        "processing_time_ms": 0,
    }


@router.get("/verify/{request_id}/status", response_model=VerifyResponseSchema)
async def get_verification_status(
    request_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    repo = VerificationRepository(db)
    request = await repo.get_request_by_id(request_id)
    if not request or request.tenant_id != tenant.id:
        raise HTTPException(status_code=404, detail="Request not found")

    response: dict = {
        "request_id": request.id,
        "reference_id": request.reference_id,
        "status": request.status,
        "processing_time_ms": 0,
    }

    if request.result:
        r = request.result
        response.update({
            "qr_valid": r.qr_valid,
            "name": r.full_name,
            "dob": r.dob,
            "gender": r.gender,
            "masked_aadhaar": r.masked_uid,
            "address": r.address_json,
            "risk_score": r.risk_score or "NOT_APPLICABLE",
            "liveness_result": r.liveness_result,
            "image_quality_score": r.image_quality_score,
            "processing_time_ms": r.processing_time_ms or 0,
            "error_code": r.error_code,
            "error_message": r.error_message,
        })

    return response


@router.get("/verify/{request_id}/result", response_model=VerifyResponseSchema)
async def get_verification_result(
    request_id: uuid.UUID,
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    repo = VerificationRepository(db)
    request = await repo.get_request_by_id(request_id)
    if not request or request.tenant_id != tenant.id:
        raise HTTPException(status_code=404, detail="Request not found")
    if request.status != "COMPLETED":
        raise HTTPException(status_code=409, detail=f"Verification is {request.status}")

    r = request.result
    return {
        "request_id": request.id,
        "reference_id": request.reference_id,
        "status": request.status,
        "qr_valid": r.qr_valid,
        "name": r.full_name,
        "dob": r.dob,
        "gender": r.gender,
        "masked_aadhaar": r.masked_uid,
        "address": r.address_json,
        "risk_score": r.risk_score or "NOT_APPLICABLE",
        "liveness_result": r.liveness_result,
        "image_quality_score": r.image_quality_score,
        "processing_time_ms": r.processing_time_ms or 0,
        "error_code": r.error_code,
        "error_message": r.error_message,
    }
