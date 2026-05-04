from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, Any, List
from datetime import date
from enum import Enum


class VerificationStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"


class PhotoStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    FAILED = "FAILED"


class AddressStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


class RiskScore(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class AddressSchema(BaseModel):
    full: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    pincode: Optional[str] = None
    status: AddressStatus


class VerifyRequestSchema(BaseModel):
    reference_id: str = Field(..., max_length=128)
    password: Optional[str] = None
    enable_liveness: bool = False
    metadata: Optional[Dict[str, Any]] = None


class VerifyResponseSchema(BaseModel):
    request_id: UUID4
    reference_id: str
    status: VerificationStatus
    qr_valid: Optional[bool] = None
    name: Optional[str] = None
    dob: Optional[str] = None
    gender: Optional[str] = None
    masked_aadhaar: Optional[str] = None
    photo_status: PhotoStatus = PhotoStatus.NOT_AVAILABLE
    photo_data: Optional[str] = None
    address: Optional[AddressSchema] = None
    risk_score: RiskScore = RiskScore.NOT_APPLICABLE
    liveness_result: Optional[str] = None
    image_quality_score: Optional[float] = None
    processing_time_ms: int = 0
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class BulkSubmitResponseSchema(BaseModel):
    job_id: UUID4
    status: str
    total_count: int
    message: str


class BulkStatusSchema(BaseModel):
    job_id: UUID4
    status: str
    total_count: int
    completed_count: int
    failed_count: int
    created_at: str
    completed_at: Optional[str] = None


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TenantCreateSchema(BaseModel):
    name: str = Field(..., max_length=100)
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None


class TenantResponseSchema(BaseModel):
    id: UUID4
    name: str
    api_key: str
    webhook_url: Optional[str] = None
    is_active: bool
    created_at: str

    class Config:
        from_attributes = True


class StorageUploadSchema(BaseModel):
    upload_url: str
    object_key: str
    download_url: Optional[str] = None


class ReportSummarySchema(BaseModel):
    total_verifications: int
    completed: int
    failed: int
    risk_breakdown: Dict[str, int]
    avg_processing_time_ms: float
    period_days: int
