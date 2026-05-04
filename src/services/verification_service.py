"""
VerificationService — fixed:
  - Removed VerificationStatus import (was missing from models)
  - Uses string literals for status matching models
  - Added idempotency, audit logging, webhook dispatch
"""
import uuid
import logging
from typing import Dict, Any, Optional
from uuid import UUID

from src.db.repositories.verification_repo import VerificationRepository
from src.core.orchestrator import VerificationOrchestrator
from src.services.webhook_service import WebhookService

logger = logging.getLogger(__name__)

PROCESSING = "PROCESSING"
COMPLETED  = "COMPLETED"
FAILED     = "FAILED"


class VerificationService:
    def __init__(self, repo: VerificationRepository):
        self.repo = repo
        self.orchestrator = VerificationOrchestrator()

    async def process_single_verification(
        self,
        tenant_id: UUID,
        reference_id: str,
        file_bytes: bytes,
        source_type: str,
        password: Optional[str] = None,
        selfie_bytes: Optional[bytes] = None,
        webhook_url: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> Dict[str, Any]:

        # 1. Idempotency check
        existing = await self.repo.get_request_by_reference(reference_id, tenant_id)
        if existing and existing.status == COMPLETED:
            return {"status": COMPLETED, "request_id": str(existing.id), "reference_id": reference_id, "idempotent": True}

        # 2. Create request record
        request = await self.repo.create_request({
            "reference_id": reference_id,
            "tenant_id":    tenant_id,
            "source_type":  source_type,
            "status":       PROCESSING,
        })

        # 3. Audit: start
        await self.repo.create_audit_log({
            "request_id":     request.id,
            "event_type":     "PROCESSING_STARTED",
            "event_metadata": {"source_type": source_type, "has_selfie": selfie_bytes is not None},
        })

        # 4. Run orchestrator
        try:
            result = await self.orchestrator.verify_document(
                file_bytes, source_type, password=password, selfie_bytes=selfie_bytes
            )
        except Exception as e:
            logger.error(f"Orchestrator error for {reference_id}: {e}", exc_info=True)
            await self.repo.update_request_status(request.id, FAILED)
            await self.repo.create_audit_log({"request_id": request.id, "event_type": "FAILED", "event_metadata": {"error": str(e)}})
            return {"status": FAILED, "error_code": "ERR_INTERNAL", "request_id": str(request.id), "reference_id": reference_id}

        final_status = COMPLETED if result.get("status") == COMPLETED else FAILED

        # 5. Persist result
        photo = result.get("photo_data")
        addr  = result.get("address", {})
        await self.repo.save_result({
            "request_id":         request.id,
            "full_name":          result.get("name"),
            "masked_uid":         result.get("masked_aadhaar"),
            "dob":                result.get("dob"),
            "gender":             result.get("gender"),
            "address_json":       addr,
            "photo_storage_key":  None,  # populated by photo service when stored
            "processing_time_ms": result.get("processing_time_ms"),
        })
        await self.repo.update_request_status(request.id, final_status)

        # 6. Audit: completion
        await self.repo.create_audit_log({
            "request_id":     request.id,
            "event_type":     final_status,
            "event_metadata": {"risk_score": result.get("risk_score"), "processing_ms": result.get("processing_time_ms")},
        })

        # 7. Webhook dispatch (fire-and-forget)
        if webhook_url:
            import asyncio
            asyncio.create_task(WebhookService.dispatch(
                webhook_url,
                {**result, "request_id": str(request.id), "reference_id": reference_id, "photo_data": None},
                secret=webhook_secret,
            ))

        # Strip raw photo bytes from API response
        result.pop("photo_data", None)
        return {**result, "request_id": str(request.id), "reference_id": reference_id}
