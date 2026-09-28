from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.entities import User, Workspace, WorkspaceMember
from app.models.schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from app.security import get_password_hash, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=TokenResponse)
async def register_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == payload.email)
    existing = (await db.execute(stmt)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        name=payload.name,
        hashed_password=get_password_hash(payload.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Auto create personal default workspace
    ws_slug = payload.name.lower().replace(" ", "-") + "-ops"
    workspace = Workspace(name=f"{payload.name}'s Workspace", slug=ws_slug)
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)

    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role="owner")
    db.add(member)
    await db.commit()

    token = create_access_token({"sub": user.id, "email": user.email, "workspace_id": workspace.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/login", response_model=TokenResponse)
async def login_user(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == payload.email)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Get user workspace
    m_stmt = select(WorkspaceMember).where(WorkspaceMember.user_id == user.id)
    membership = (await db.execute(m_stmt)).scalars().first()
    ws_id = membership.workspace_id if membership else None

    token = create_access_token({"sub": user.id, "email": user.email, "workspace_id": ws_id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user
    }
