from src.db.repositories.verification_repo import VerificationRepository
from src.core.orchestrator import VerificationOrchestrator
from src.db.models import VerificationStatus
from typing import Dict, Any
from uuid import UUID
import logging

logger = logging.getLogger(__name__)

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
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        # 1. Check idempotency
        existing_request = await self.repo.get_request_by_reference(reference_id, tenant_id)
        if existing_request:
            # If already completed, return result
            if existing_request.status == VerificationStatus.COMPLETED:
                # Return result from DB (simplified)
                return {"status": "COMPLETED", "request_id": existing_request.id, "reference_id": reference_id}
        
        # 2. Create request record
        request_data = {
            "reference_id": reference_id,
            "tenant_id": tenant_id,
            "source_type": source_type,
            "file_path": f"uploads/{reference_id}", # Simplified
            "status": VerificationStatus.PROCESSING
        }
        request = await self.repo.create_request(request_data)

        # 3. Log start
        await self.repo.create_audit_log({
            "tenant_id": tenant_id,
            "request_id": request.id,
            "event_type": "PROCESSING_STARTED",
            "actor": "API_KEY_HOLDER"
        })

        # 4. Run Orchestrator
        try:
            result = await self.orchestrator.verify_image(file_bytes)
            
            # 5. Persist result
            result_data = {
                "request_id": request.id,
                **result,
                # Mapping address dict to flat fields for DB
                "address_full": result.get('address', {}).get('full'),
                "state": result.get('address', {}).get('state'),
                "district": result.get('address', {}).get('district'),
                "pincode": result.get('address', {}).get('pincode'),
                "address_status": "COMPLETE"
            }
            # Clean up result_data to match model
            model_fields = {
                "request_id", "qr_valid", "name", "dob", "gender", "masked_aadhaar",
                "photo_status", "photo_data", "address_full", "state", "district",
                "pincode", "address_status", "risk_score", "processing_time_ms",
                "error_code", "error_message"
            }
            db_result_data = {k: v for k, v in result_data.items() if k in model_fields}
            
            await self.repo.save_result(db_result_data)
            await self.repo.update_request_status(request.id, result['status'])

            # 6. Log completion
            await self.repo.create_audit_log({
                "tenant_id": tenant_id,
                "request_id": request.id,
                "event_type": "COMPLETED" if result['status'] == "COMPLETED" else "FAILED",
                "actor": "SYSTEM"
            })

            return {**result, "request_id": request.id, "reference_id": reference_id}

        except Exception as e:
            logger.error(f"Error in verification service: {e}")
            await self.repo.update_request_status(request.id, VerificationStatus.FAILED)
            return {"status": "FAILED", "error_code": "ERR_INTERNAL_SERVER", "request_id": request.id}
