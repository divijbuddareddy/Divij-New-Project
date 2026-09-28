from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.entities import AgentRun
from app.models.schemas import AgentRunRequest, AgentRunResponse
from app.agents import OperationsAgentHub

router = APIRouter(prefix="/agent", tags=["Agent"])

@router.post("/runs", response_model=AgentRunResponse)
async def dispatch_agent_run(
    payload: AgentRunRequest,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id
    if not ws_id:
        raise HTTPException(status_code=400, detail="X-Workspace-Id header required")

    agent_run = AgentRun(
        workspace_id=ws_id,
        query=payload.query,
        status="running",
        started_at=datetime.utcnow()
    )
    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)

    # Execute Multi-Agent Graph
    result_state = await OperationsAgentHub.run(
        db=db,
        workspace_id=ws_id,
        query=payload.query,
        user_id="usr_admin"
    )

    agent_run.status = "completed"
    agent_run.intent = result_state.get("intent")
    agent_run.plan = result_state.get("plan", [])
    agent_run.final_response = result_state.get("final_response")
    agent_run.evidence_refs = result_state.get("evidence_refs", [])
    agent_run.proposed_actions = result_state.get("proposed_actions", [])
    agent_run.completed_at = datetime.utcnow()

    await db.commit()
    await db.refresh(agent_run)
    return agent_run

@router.get("/runs/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    run_id: str,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AgentRun).where(AgentRun.id == run_id)
    run = (await db.execute(stmt)).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")
    return run

@router.get("/runs", response_model=List[AgentRunResponse])
async def list_agent_runs(
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id or "default"
    stmt = select(AgentRun).where(AgentRun.workspace_id == ws_id).order_by(desc(AgentRun.started_at)).limit(20)
    res = await db.execute(stmt)
    return list(res.scalars().all())
