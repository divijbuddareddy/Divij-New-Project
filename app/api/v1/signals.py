from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db
from app.models.schemas import SignalResponse
from app.services.signal_service import SignalService

router = APIRouter(prefix="/signals", tags=["Signals"])

@router.get("", response_model=List[SignalResponse])
async def list_signals(
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id or "default"
    signals = await SignalService.get_active_signals(db, ws_id)
    if not signals:
        signals = await SignalService.detect_signals(db, ws_id)
    return signals

@router.post("/detect", response_model=List[SignalResponse])
async def trigger_signal_detection(
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id or "default"
    signals = await SignalService.detect_signals(db, ws_id)
    return signals
