import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Enum, Text, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class SourceType(enum.Enum):
    IMAGE = "IMAGE"
    PDF = "PDF"
    XML = "XML"
    ZIP = "ZIP"

class VerificationStatus(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class PhotoStatus(enum.Enum):
    AVAILABLE = "AVAILABLE"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    FAILED = "FAILED"

class AddressStatus(enum.Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"

class RiskScore(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    NOT_APPLICABLE = "NOT_APPLICABLE"

class VerificationRequest(Base):
    __tablename__ = "verification_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    reference_id = Column(String(128), unique=True, nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    source_type = Column(Enum(SourceType), nullable=False)
    file_path = Column(Text, nullable=False)
    password_hint = Column(Text, nullable=True)
    status = Column(Enum(VerificationStatus), nullable=False, default=VerificationStatus.PENDING)
    attempt_count = Column(Integer, default=0)
    worker_id = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    result = relationship("VerificationResult", back_populates="request", uselist=False)

class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("verification_requests.id"), unique=True, nullable=False)
    qr_valid = Column(Boolean, nullable=True)
    name = Column(Text, nullable=True)
    dob = Column(Date, nullable=True)
    gender = Column(String(1), nullable=True)
    masked_aadhaar = Column(String(19), nullable=True)
    photo_status = Column(Enum(PhotoStatus), nullable=False)
    photo_data = Column(Text, nullable=True)  # Encrypted at app layer
    address_full = Column(Text, nullable=True)
    state = Column(String(64), nullable=True)
    district = Column(String(64), nullable=True)
    pincode = Column(String(6), nullable=True)
    address_status = Column(Enum(AddressStatus), nullable=False)
    image_quality_score = Column(Numeric(4, 3), nullable=True)
    risk_score = Column(Enum(RiskScore), nullable=False)
    liveness_result = Column(String(32), nullable=True)
    error_code = Column(String(32), nullable=True)
    error_message = Column(Text, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    request = relationship("VerificationRequest", back_populates="result")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    request_id = Column(UUID(as_uuid=True), nullable=True)
    event_type = Column(String(64), nullable=False)
    actor = Column(String(128), nullable=False)
    event_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
