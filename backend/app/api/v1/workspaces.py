from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.database import get_db
from app.models.entities import Workspace, WorkspaceMember
from app.models.schemas import WorkspaceCreate, WorkspaceResponse

router = APIRouter(prefix="/workspaces", tags=["Workspaces"])

@router.get("", response_model=List[WorkspaceResponse])
async def list_workspaces(db: AsyncSession = Depends(get_db)):
    stmt = select(Workspace).order_by(Workspace.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())

@router.post("", response_model=WorkspaceResponse)
async def create_workspace(payload: WorkspaceCreate, db: AsyncSession = Depends(get_db)):
    slug = payload.slug or payload.name.lower().replace(" ", "-")
    stmt = select(Workspace).where(Workspace.slug == slug)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Workspace slug already exists")

    ws = Workspace(name=payload.name, slug=slug)
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    return ws

@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Workspace).where(Workspace.id == workspace_id)
    ws = (await db.execute(stmt)).scalar_one_or_none()
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws
