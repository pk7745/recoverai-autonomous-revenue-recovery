from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogItem

router = APIRouter(prefix="/audit", tags=["Audit Trail"])

@router.get("/logs", response_model=List[AuditLogItem])
async def list_audit_logs(
    limit: int = Query(50, le=200),
    actor: Optional[str] = Query(None),
    transaction_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    if actor:
        stmt = stmt.where(AuditLog.actor == actor)
    if transaction_id:
        stmt = stmt.where(AuditLog.transaction_id == transaction_id)

    res = await db.execute(stmt)
    logs = res.scalars().all()
    return logs
