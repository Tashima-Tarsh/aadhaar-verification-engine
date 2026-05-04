import uuid
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException

from src.api.v1.dependencies.auth import get_current_tenant
from src.db.models import Tenant
from src.utils.storage import storage as storage_manager

router = APIRouter()


@router.post("/storage/upload-url", response_model=Dict[str, str])
async def get_upload_url(
    file_name: str,
    tenant: Tenant = Depends(get_current_tenant),
):
    """Generate a pre-signed S3 URL for direct CRM document upload."""
    object_name = f"uploads/{tenant.id}/{uuid.uuid4().hex}-{file_name}"
    url = storage_manager.generate_presigned_upload_url(object_name)
    if not url:
        raise HTTPException(status_code=500, detail="Could not generate upload URL")
    return {"upload_url": url, "object_key": object_name}


@router.get("/storage/download-url", response_model=Dict[str, str])
async def get_download_url(
    object_key: str,
    tenant: Tenant = Depends(get_current_tenant),
):
    """Generate a pre-signed S3 URL to download a stored document."""
    if not object_key.startswith(f"uploads/{tenant.id}/"):
        raise HTTPException(status_code=403, detail="Access denied")
    url = storage_manager.generate_presigned_download_url(object_key)
    if not url:
        raise HTTPException(status_code=500, detail="Could not generate download URL")
    return {"download_url": url, "object_key": object_key}
