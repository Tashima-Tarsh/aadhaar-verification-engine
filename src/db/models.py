"""
DB models — merged: user's Tenant + BulkJob multi-tenancy
                    + mine's complete VerificationJob fields + AuditLog.
"""
import uuid
import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name            = Column(String(100), nullable=False)
    api_key_hash    = Column(String(64), nullable=False, unique=True, index=True)
    webhook_url     = Column(String(500), nullable=True)
    webhook_secret  = Column(String(255), nullable=True)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)

    requests  = relationship("VerificationRequest", back_populates="tenant")
    bulk_jobs = relationship("BulkJob", back_populates="tenant")


class BulkJob(Base):
    __tablename__ = "bulk_jobs"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id       = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    status          = Column(String(20), default="QUEUED")   # QUEUED | IN_PROGRESS | COMPLETED | PARTIAL | FAILED
    total_count     = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    failed_count    = Column(Integer, default=0)
    webhook_url     = Column(String(500), nullable=True)
    created_at      = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at    = Column(DateTime, nullable=True)

    tenant   = relationship("Tenant", back_populates="bulk_jobs")
    requests = relationship("VerificationRequest", back_populates="bulk_job")


class VerificationRequest(Base):
    __tablename__ = "verification_requests"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id    = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    bulk_job_id  = Column(UUID(as_uuid=True), ForeignKey("bulk_jobs.id"), nullable=True, index=True)
    reference_id = Column(String(128), index=True, nullable=False)
    source_type  = Column(String(20), nullable=False)   # IMAGE | PDF | XML
    status       = Column(String(20), default="PENDING", index=True)  # PENDING | PROCESSING | COMPLETED | FAILED
    created_at   = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    started_at   = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    tenant   = relationship("Tenant", back_populates="requests")
    bulk_job = relationship("BulkJob", back_populates="requests")
    result   = relationship("VerificationResult", uselist=False, back_populates="request")
    audit_logs = relationship("AuditLog", back_populates="request")


class VerificationResult(Base):
    __tablename__ = "verification_results"

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id         = Column(UUID(as_uuid=True), ForeignKey("verification_requests.id"), unique=True)
    full_name          = Column(String(200), nullable=True)
    masked_uid         = Column(String(20),  nullable=True)
    dob                = Column(String(20),  nullable=True)
    gender             = Column(String(10),  nullable=True)
    address_json       = Column(JSONB,       nullable=True)
    photo_storage_key  = Column(String(500), nullable=True)
    qr_valid           = Column(Boolean,     nullable=True)
    risk_score         = Column(String(20),  nullable=True)  # LOW | MEDIUM | HIGH
    risk_numeric       = Column(Integer,     nullable=True)
    liveness_result    = Column(String(20),  nullable=True)
    image_quality_score = Column(Float,      nullable=True)
    processing_time_ms = Column(Integer,     nullable=True)
    error_code         = Column(String(50),  nullable=True)
    error_message      = Column(Text,        nullable=True)

    request = relationship("VerificationRequest", back_populates="result")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id     = Column(UUID(as_uuid=True), ForeignKey("verification_requests.id"), nullable=True, index=True)
    event_type     = Column(String(50),  nullable=False, index=True)
    event_metadata = Column(JSONB,       nullable=True)
    timestamp      = Column(DateTime,    default=datetime.datetime.utcnow, index=True)

    request = relationship("VerificationRequest", back_populates="audit_logs")
