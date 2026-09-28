from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.database import get_db
from app.models.entities import AuditLog
from app.models.schemas import AuditLogResponse

router = APIRouter(prefix="/audit", tags=["Audit Logs"])

@router.get("", response_model=List[AuditLogResponse])
async def list_audit_logs(
    x_workspace_id: Optional[str] = Header(None),
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id or "default"
    stmt = select(AuditLog).where(AuditLog.workspace_id == ws_id).order_by(desc(AuditLog.timestamp)).limit(limit)
    res = await db.execute(stmt)
    return list(res.scalars().all())
