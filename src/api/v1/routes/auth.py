import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.api.v1.schemas.verify import TokenSchema, TenantCreateSchema, TenantResponseSchema
from src.core.database import get_db
from src.core.security import generate_api_key, hash_api_key, create_access_token, create_refresh_token
from src.db.models import Tenant
from src.utils.crypto import AuthHandler

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/auth/token", response_model=TokenSchema)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with tenant name + API key to obtain JWT tokens."""
    result = await db.execute(
        select(Tenant).where(Tenant.name == form.username, Tenant.is_active == True)
    )
    tenant = result.scalar_one_or_none()

    if not tenant or hash_api_key(form.password) != tenant.api_key_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(str(tenant.id))
    refresh_token = create_refresh_token(str(tenant.id))
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/auth/refresh", response_model=TokenSchema)
async def refresh_token(
    refresh_token_str: str,
    db: AsyncSession = Depends(get_db),
):
    """Exchange a valid refresh token for new access + refresh tokens."""
    payload = AuthHandler.decode_token(refresh_token_str)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    import uuid as _uuid
    try:
        tenant_uuid = _uuid.UUID(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_uuid, Tenant.is_active == True))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tenant not found")

    access_token = create_access_token(str(tenant.id))
    new_refresh = create_refresh_token(str(tenant.id))
    return {"access_token": access_token, "refresh_token": new_refresh, "token_type": "bearer"}


@router.post("/tenants", response_model=TenantResponseSchema, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    body: TenantCreateSchema,
    db: AsyncSession = Depends(get_db),
):
    """Register a new tenant and return their plain-text API key (shown once)."""
    plain_key = generate_api_key()
    key_hash = hash_api_key(plain_key)

    tenant = Tenant(
        name=body.name,
        api_key_hash=key_hash,
        webhook_url=body.webhook_url,
        webhook_secret=body.webhook_secret,
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    return {
        "id": tenant.id,
        "name": tenant.name,
        "api_key": plain_key,
        "webhook_url": tenant.webhook_url,
        "is_active": tenant.is_active,
        "created_at": tenant.created_at.isoformat(),
    }


@router.post("/tenants/{tenant_id}/regenerate-key", response_model=TenantResponseSchema)
async def regenerate_api_key(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Rotate the API key for a tenant (admin operation)."""
    from sqlalchemy import select
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    plain_key = generate_api_key()
    tenant.api_key_hash = hash_api_key(plain_key)
    await db.commit()
    await db.refresh(tenant)

    return {
        "id": tenant.id,
        "name": tenant.name,
        "api_key": plain_key,
        "webhook_url": tenant.webhook_url,
        "is_active": tenant.is_active,
        "created_at": tenant.created_at.isoformat(),
    }
