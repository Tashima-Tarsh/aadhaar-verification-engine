from fastapi import APIRouter, Depends, HTTPException
from src.utils.storage import StorageManager
from src.api.v1.schemas.verify import TokenData # Assume basic auth schema
from typing import Dict
import uuid

router = APIRouter()
storage = StorageManager()

@router.post("/upload-url", response_model=Dict[str, str])
async def get_upload_url(file_name: str, file_type: str):
    """
    Generates a pre-signed S3 URL for direct document upload from CRM.
    Used to prevent large files from hitting the FastAPI application directly.
    """
    object_name = f"uploads/{uuid.uuid4()}-{file_name}"
    url = storage.generate_presigned_upload_url(object_name)
    
    if not url:
        raise HTTPException(status_code=500, detail="Could not generate upload URL")
        
    return {
        "upload_url": url,
        "object_key": object_name
    }
