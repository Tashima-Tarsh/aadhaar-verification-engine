from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.db.models import VerificationRequest, VerificationResult, AuditLog
from typing import Optional, List
from uuid import UUID

class VerificationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_request(self, request_data: dict) -> VerificationRequest:
        request = VerificationRequest(**request_data)
        self.session.add(request)
        await self.session.commit()
        await self.session.refresh(request)
        return request

    async def get_request_by_id(self, request_id: UUID) -> Optional[VerificationRequest]:
        result = await self.session.execute(
            select(VerificationRequest).where(VerificationRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_request_by_reference(self, reference_id: str, tenant_id: UUID) -> Optional[VerificationRequest]:
        result = await self.session.execute(
            select(VerificationRequest)
            .where(VerificationRequest.reference_id == reference_id)
            .where(VerificationRequest.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def update_request_status(self, request_id: UUID, status: str):
        request = await self.get_request_by_id(request_id)
        if request:
            request.status = status
            await self.session.commit()

    async def save_result(self, result_data: dict) -> VerificationResult:
        result = VerificationResult(**result_data)
        self.session.add(result)
        await self.session.commit()
        await self.session.refresh(result)
        return result

    async def create_audit_log(self, log_data: dict):
        log = AuditLog(**log_data)
        self.session.add(log)
        await self.session.commit()
