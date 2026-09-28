from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.entities import IntegrationAccount, EncryptedCredential
from app.models.schemas import IntegrationConnectRequest, IntegrationResponse
from app.security import encrypt_token
from app.integrations import get_integration_adapter
from app.services.audit_service import AuditService

router = APIRouter(prefix="/integrations", tags=["Integrations"])

@router.get("", response_model=List[IntegrationResponse])
async def list_integrations(
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    if not x_workspace_id:
        # Default fallback to first workspace
        res = await db.execute(select(IntegrationAccount).limit(10))
        return list(res.scalars().all())

    stmt = select(IntegrationAccount).where(IntegrationAccount.workspace_id == x_workspace_id)
    result = await db.execute(stmt)
    return list(result.scalars().all())

@router.post("/{provider}/connect")
async def connect_integration(
    provider: str,
    payload: IntegrationConnectRequest,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id
    if not ws_id:
        raise HTTPException(status_code=400, detail="X-Workspace-Id header required")

    # Upsert integration
    stmt = select(IntegrationAccount).where(
        IntegrationAccount.workspace_id == ws_id,
        IntegrationAccount.provider == provider.lower()
    )
    integ = (await db.execute(stmt)).scalar_one_or_none()
    if not integ:
        integ = IntegrationAccount(
            workspace_id=ws_id,
            provider=provider.lower(),
            account_name=payload.account_name,
            scopes=payload.scopes or [],
            status="connected",
            last_synced_at=datetime.utcnow()
        )
        db.add(integ)
        await db.commit()
        await db.refresh(integ)

    # Store encrypted credentials
    token_str = payload.credentials.get("token") or payload.credentials.get("access_token", "default_token")
    enc = encrypt_token(token_str)
    
    cred_stmt = select(EncryptedCredential).where(EncryptedCredential.integration_id == integ.id)
    cred = (await db.execute(cred_stmt)).scalar_one_or_none()
    if not cred:
        cred = EncryptedCredential(
            integration_id=integ.id,
            ciphertext=enc["ciphertext"],
            iv=enc["iv"]
        )
        db.add(cred)
    else:
        cred.ciphertext = enc["ciphertext"]
        cred.iv = enc["iv"]
    
    await db.commit()

    # Test connection
    adapter = get_integration_adapter(provider, ws_id, {"access_token": token_str})
    test_res = await adapter.test_connection()

    await AuditService.log_event(
        db=db,
        workspace_id=ws_id,
        action_type="integration_connected",
        resource=f"provider:{provider}",
        details={"account_name": payload.account_name, "test_result": test_res}
    )

    return {
        "success": True,
        "integration_id": integ.id,
        "provider": provider,
        "connection_test": test_res
    }

@router.post("/{provider}/test")
async def test_integration_connection(
    provider: str,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    adapter = get_integration_adapter(provider, x_workspace_id or "default", {"access_token": "mock_token"})
    res = await adapter.test_connection()
    return res

@router.post("/{provider}/disconnect")
@router.delete("/{provider}")
async def disconnect_integration(
    provider: str,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id or "default"
    p_lower = provider.lower()
    
    # Select any integration accounts matching provider and workspace (or fallback to provider match)
    stmt = select(IntegrationAccount).where(
        (IntegrationAccount.provider == p_lower) & 
        ((IntegrationAccount.workspace_id == ws_id) | (IntegrationAccount.workspace_id == "default") | (IntegrationAccount.workspace_id == None))
    )
    result = await db.execute(stmt)
    integs = list(result.scalars().all())
    
    if not integs:
        # Fallback to any matching provider regardless of workspace ID
        stmt_fallback = select(IntegrationAccount).where(IntegrationAccount.provider == p_lower)
        result_fallback = await db.execute(stmt_fallback)
        integs = list(result_fallback.scalars().all())

    for integ in integs:
        # Remove credentials
        cred_stmt = select(EncryptedCredential).where(EncryptedCredential.integration_id == integ.id)
        cred_res = await db.execute(cred_stmt)
        creds = list(cred_res.scalars().all())
        for cred in creds:
            await db.delete(cred)
            
        await db.delete(integ)

    # Wipe all cached/synced evidence items for this provider
    source_map = {
        "gmail": ["gmail", "google"],
        "google": ["gmail", "google"],
        "github": ["github"],
        "slack": ["slack"],
        "hubspot": ["hubspot", "crm", "salesforce"],
        "crm": ["hubspot", "crm", "salesforce"]
    }
    sources = source_map.get(p_lower, [p_lower])
    ev_stmt = select(EvidenceItem).where(EvidenceItem.source.in_(sources))
    ev_res = await db.execute(ev_stmt)
    for ev in list(ev_res.scalars().all()):
        await db.delete(ev)
    
    await db.commit()

    await AuditService.log_event(
        db=db,
        workspace_id=ws_id,
        action_type="integration_disconnected",
        resource=f"provider:{provider}",
        details={"provider": provider, "status": "disconnected"}
    )

    return {
        "success": True,
        "provider": provider,
        "message": f"Successfully disconnected {provider.upper()}"
    }

