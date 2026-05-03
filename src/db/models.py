from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum, JSON, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, declarative_base
import uuid
import datetime

Base = declarative_base()

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    api_key_hash = Column(String(255), nullable=False)
    webhook_url = Column(String(255))
    webhook_secret = Column(String(255))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    requests = relationship("VerificationRequest", back_populates="tenant")
    bulk_jobs = relationship("BulkJob", back_populates="tenant")

class BulkJob(Base):
    __tablename__ = "bulk_jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    total_count = Column(Integer, default=0)
    processed_count = Column(Integer, default=0)
    status = Column(String(20), default="QUEUED") # QUEUED, IN_PROGRESS, COMPLETED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="bulk_jobs")
    requests = relationship("VerificationRequest", back_populates="bulk_job")

class VerificationRequest(Base):
    __tablename__ = "verification_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"))
    bulk_job_id = Column(UUID(as_uuid=True), ForeignKey("bulk_jobs.id"), nullable=True)
    reference_id = Column(String(100), index=True)
    status = Column(String(20), default="PENDING") # PENDING, PROCESSING, COMPLETED, FAILED
    source_type = Column(String(20)) # IMAGE, PDF, XML
    risk_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    tenant = relationship("Tenant", back_populates="requests")
    bulk_job = relationship("BulkJob", back_populates="requests")
    result = relationship("VerificationResult", uselist=False, back_populates="request")
    audit_logs = relationship("AuditLog", back_populates="request")

class VerificationResult(Base):
    __tablename__ = "verification_results"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("verification_requests.id"))
    full_name = Column(String(200))
    masked_uid = Column(String(20))
    dob = Column(Date)
    gender = Column(String(10))
    address_json = Column(JSONB)
    photo_storage_key = Column(String(255))
    processing_time_ms = Column(Integer)

    request = relationship("VerificationRequest", back_populates="result")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("verification_requests.id"))
    event_type = Column(String(50))
    event_metadata = Column(JSONB)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    request = relationship("VerificationRequest", back_populates="audit_logs")
