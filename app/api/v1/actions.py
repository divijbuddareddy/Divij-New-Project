from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from app.database import get_db
from app.models.entities import ActionItem, ActionPlan
from app.models.schemas import ActionItemResponse, ActionPlanResponse, ApprovalDecisionRequest, ActionExecuteRequest
from app.services.action_service import ActionService

router = APIRouter(prefix="/actions", tags=["Actions & Approvals"])

@router.get("/pending", response_model=List[ActionItemResponse])
async def list_pending_actions(
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id or "default"
    stmt = select(ActionItem).where(
        ActionItem.workspace_id == ws_id,
        ActionItem.status.in_(["awaiting_approval", "approved"])
    ).order_by(desc(ActionItem.created_at))
    res = await db.execute(stmt)
    return list(res.scalars().all())

@router.get("/plans/{plan_id}", response_model=ActionPlanResponse)
async def get_action_plan(
    plan_id: str,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(ActionPlan).where(ActionPlan.id == plan_id)
    plan = (await db.execute(stmt)).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Action plan not found")

    act_stmt = select(ActionItem).where(ActionItem.action_plan_id == plan.id)
    actions = list((await db.execute(act_stmt)).scalars().all())
    
    return {
        "id": plan.id,
        "investigation_id": plan.investigation_id,
        "workspace_id": plan.workspace_id,
        "title": plan.title,
        "summary": plan.summary,
        "status": plan.status,
        "actions": actions,
        "created_at": plan.created_at
    }

@router.post("/{action_id}/approve")
async def approve_action(
    action_id: str,
    payload: ApprovalDecisionRequest,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id or "default"
    success, msg, action = await ActionService.approve_action(
        db=db,
        workspace_id=ws_id,
        action_id=action_id,
        user_id="usr_admin",
        notes=payload.notes
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"success": True, "message": msg, "action_id": action.id, "status": action.status}

@router.post("/{action_id}/reject")
async def reject_action(
    action_id: str,
    payload: ApprovalDecisionRequest,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id or "default"
    success, msg, action = await ActionService.reject_action(
        db=db,
        workspace_id=ws_id,
        action_id=action_id,
        user_id="usr_admin",
        notes=payload.notes
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"success": True, "message": msg, "action_id": action.id, "status": action.status}

@router.post("/{action_id}/execute")
async def execute_action(
    action_id: str,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id or "default"
    success, msg, result_data = await ActionService.execute_action(
        db=db,
        workspace_id=ws_id,
        action_id=action_id,
        user_id="usr_admin"
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)

    return {"success": True, "message": msg, "result": result_data}
