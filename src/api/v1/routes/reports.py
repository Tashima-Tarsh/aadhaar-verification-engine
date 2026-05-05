import io
import csv
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from src.api.v1.dependencies.auth import get_current_tenant
from src.api.v1.schemas.verify import ReportSummarySchema
from src.core.database import get_db
from src.db.models import Tenant, VerificationRequest, VerificationResult

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/reports/summary", response_model=ReportSummarySchema)
async def get_summary(
    days: int = Query(30, ge=1, le=365),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(
            func.count(VerificationRequest.id).label("total"),
            func.sum(
                case((VerificationRequest.status == "COMPLETED", 1), else_=0)
            ).label("completed"),
        ).where(
            VerificationRequest.tenant_id == tenant.id,
            VerificationRequest.created_at >= since,
        )
    )
    row = result.one()

    total = row.total or 0
    completed = row.completed or 0
    failed = total - completed

    risk_result = await db.execute(
        select(VerificationResult.risk_score, func.count(VerificationResult.id))
        .join(VerificationRequest, VerificationResult.request_id == VerificationRequest.id)
        .where(VerificationRequest.tenant_id == tenant.id, VerificationRequest.created_at >= since)
        .group_by(VerificationResult.risk_score)
    )
    risk_breakdown = {row[0] or "UNKNOWN": row[1] for row in risk_result}

    avg_result = await db.execute(
        select(func.avg(VerificationResult.processing_time_ms))
        .join(VerificationRequest, VerificationResult.request_id == VerificationRequest.id)
        .where(VerificationRequest.tenant_id == tenant.id, VerificationRequest.created_at >= since)
    )
    avg_ms = avg_result.scalar() or 0.0

    return {
        "total_verifications": total,
        "completed": completed,
        "failed": failed,
        "risk_breakdown": risk_breakdown,
        "avg_processing_time_ms": float(avg_ms),
        "period_days": days,
    }


@router.get("/reports/export/csv")
async def export_csv(
    days: int = Query(30, ge=1, le=365),
    tenant: Tenant = Depends(get_current_tenant),
    db: AsyncSession = Depends(get_db),
):
    since = datetime.utcnow() - timedelta(days=days)

    result = await db.execute(
        select(VerificationRequest, VerificationResult)
        .outerjoin(VerificationResult, VerificationResult.request_id == VerificationRequest.id)
        .where(
            VerificationRequest.tenant_id == tenant.id,
            VerificationRequest.created_at >= since,
        )
        .order_by(VerificationRequest.created_at.desc())
    )
    rows = result.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "request_id", "reference_id", "status", "source_type",
        "created_at", "completed_at", "full_name", "masked_uid",
        "dob", "gender", "qr_valid", "risk_score", "processing_time_ms",
        "error_code",
    ])

    for req, res in rows:
        writer.writerow([
            str(req.id), req.reference_id, req.status, req.source_type,
            req.created_at.isoformat() if req.created_at else "",
            req.completed_at.isoformat() if req.completed_at else "",
            res.full_name if res else "",
            res.masked_uid if res else "",
            res.dob if res else "",
            res.gender if res else "",
            res.qr_valid if res else "",
            res.risk_score if res else "",
            res.processing_time_ms if res else "",
            res.error_code if res else "",
        ])

    output.seek(0)
    filename = f"aadhaar_verifications_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
