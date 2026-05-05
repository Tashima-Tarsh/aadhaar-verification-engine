from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.core.database import get_db
from src.db.models import Tenant
from src.utils.crypto import AuthHandler
from src.core.security import hash_api_key

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_tenant(
    token: str = Depends(oauth2_scheme),
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    # Try API key first
    if api_key:
        key_hash = hash_api_key(api_key)
        result = await db.execute(select(Tenant).where(Tenant.api_key_hash == key_hash, Tenant.is_active == True))
        tenant = result.scalar_one_or_none()
        if tenant:
            return tenant

    # Try JWT
    if token:
        payload = AuthHandler.decode_token(token)
        if payload and payload.get("type") == "access":
            import uuid as _uuid
            try:
                tenant_uuid = _uuid.UUID(payload.get("sub"))
            except (TypeError, ValueError):
                pass
            else:
                result = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid, Tenant.is_active == True))
                tenant = result.scalar_one_or_none()
                if tenant:
                    return tenant

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing credentials")
