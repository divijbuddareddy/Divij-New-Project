from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.database import get_db
from app.models.entities import Investigation
from app.models.schemas import InvestigationCreate, InvestigationResponse
from app.services.investigation_service import InvestigationService

router = APIRouter(prefix="/investigations", tags=["Investigations"])

@router.get("", response_model=List[InvestigationResponse])
async def list_investigations(
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id or "default"
    stmt = select(Investigation).where(Investigation.workspace_id == ws_id).order_by(desc(Investigation.created_at))
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.post("", response_model=InvestigationResponse)
async def create_investigation(
    payload: InvestigationCreate,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id
    if not ws_id:
        raise HTTPException(status_code=400, detail="X-Workspace-Id header required")

    inv = await InvestigationService.create_investigation_from_signal(
        db=db,
        workspace_id=ws_id,
        signal_id=payload.signal_id,
        custom_title=payload.title
    )
    return inv

@router.get("/{investigation_id}", response_model=InvestigationResponse)
async def get_investigation(
    investigation_id: str,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Investigation).where(Investigation.id == investigation_id)
    inv = (await db.execute(stmt)).scalar_one_or_none()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv
