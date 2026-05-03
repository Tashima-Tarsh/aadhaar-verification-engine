from pydantic import BaseModel, Field, UUID4
from typing import Optional, Dict, Any
from datetime import date
from enum import Enum

class VerificationStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

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
    reference_id: str = Field(..., max_length=128, description="Client UUID for idempotency")
    password: Optional[str] = None
    enable_liveness: bool = False
    metadata: Optional[Dict[str, Any]] = None

class VerifyResponseSchema(BaseModel):
    request_id: UUID4
    reference_id: str
    status: VerificationStatus
    qr_valid: Optional[bool] = None
    name: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    masked_aadhaar: Optional[str] = None
    photo_status: PhotoStatus
    photo_data: Optional[str] = None
    address: AddressSchema
    risk_score: RiskScore
    liveness_result: Optional[str] = None
    image_quality_score: Optional[float] = None
    processing_time_ms: int
    error_code: Optional[str] = None
    error_message: Optional[str] = None
