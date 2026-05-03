from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.v1.schemas.verify import VerifyResponseSchema
from src.db.repositories.verification_repo import VerificationRepository
from src.services.verification_service import VerificationService
from src.config.settings import settings
from typing import Optional
import uuid

router = APIRouter()

# Mock Dependency for DB Session
async def get_db():
    # In real app, use sessionmaker
    yield None 

async def get_tenant_id(x_api_key: str = Header(...)):
    # Mock tenant identification
    if x_api_key != "test_key":
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return uuid.UUID("00000000-0000-0000-0000-000000000000")

@router.post("/verify", response_model=VerifyResponseSchema)
async def verify_aadhaar(
    file: UploadFile = File(...),
    reference_id: str = Form(...),
    password: Optional[str] = Form(None),
    enable_liveness: bool = Form(False),
    tenant_id: uuid.UUID = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db)
):
    # Mocking Repo and Service since DB is not fully set up
    repo = VerificationRepository(db)
    service = VerificationService(repo)
    
    file_bytes = await file.read()
    source_type = "IMAGE" if file.content_type.startswith("image") else "PDF"
    
    # Overriding service for demo purposes if DB is missing
    try:
        result = await service.process_single_verification(
            tenant_id=tenant_id,
            reference_id=reference_id,
            file_bytes=file_bytes,
            source_type=source_type
        )
        return result
    except Exception as e:
        # Fallback for demo without DB
        from src.core.orchestrator import VerificationOrchestrator
        orchestrator = VerificationOrchestrator()
        result = await orchestrator.verify_image(file_bytes)
        return {**result, "request_id": uuid.uuid4(), "reference_id": reference_id}
