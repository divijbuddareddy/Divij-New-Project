from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.entities import IntegrationAccount, EncryptedCredential, EvidenceItem, Workspace
from app.security import decrypt_token
from app.integrations import get_integration_adapter
from app.services.signal_service import SignalService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/sync", tags=["Sync"])

@router.post("/{provider}")
async def sync_provider_live(
    provider: str,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Connects to the specified live integration (GitHub, Gmail, Slack), fetches live items,
    normalizes them into Evidence items, and triggers live signal detection.
    """
    ws_id = x_workspace_id or "default"
    
    # 1. Fetch integration account & decrypt token
    stmt = select(IntegrationAccount).where(
        IntegrationAccount.workspace_id == ws_id,
        IntegrationAccount.provider == provider.lower()
    )
    integ = (await db.execute(stmt)).scalar_one_or_none()
    if not integ:
        stmt_any = select(IntegrationAccount).where(IntegrationAccount.provider == provider.lower())
        integ = (await db.execute(stmt_any)).scalar_one_or_none()
        if not integ:
            raise HTTPException(status_code=400, detail=f"No connected account found for provider '{provider}'.")

    token = ""
    cred_stmt = select(EncryptedCredential).where(EncryptedCredential.integration_id == integ.id)
    cred = (await db.execute(cred_stmt)).scalar_one_or_none()
    if cred:
        try:
            token = decrypt_token(cred.ciphertext, cred.iv)
        except Exception:
            token = ""

    # 2. Call live integration sync
    adapter = get_integration_adapter(
        provider=provider,
        workspace_id=ws_id,
        credentials={
            "access_token": token,
            "token": token,
            "account_name": integ.account_name
        }
    )
    raw_evidence_list = await adapter.sync_evidence()

    # 3. Store normalized evidence in DB
    created_count = 0
    for item in raw_evidence_list:
        ev_exists_stmt = select(EvidenceItem).where(
            EvidenceItem.workspace_id == ws_id,
            EvidenceItem.object_id == item["object_id"]
        )
        existing = (await db.execute(ev_exists_stmt)).scalar_one_or_none()
        if not existing:
            ev = EvidenceItem(
                workspace_id=ws_id,
                source=item["source"],
                actor=item["actor"],
                action=item["action"],
                object_id=item["object_id"],
                title=item["title"],
                content_summary=item["content_summary"],
                raw_payload=item["raw_payload"],
                event_timestamp=item.get("timestamp", datetime.utcnow())
            )
            db.add(ev)
            created_count += 1

    integ.last_synced_at = datetime.utcnow()
    await db.commit()

    # 4. Run real signal detection
    signals = await SignalService.detect_signals(db, ws_id)

    await AuditService.log_event(
        db=db,
        workspace_id=ws_id,
        action_type="live_sync_completed",
        resource=f"provider:{provider}",
        details={"items_synced": len(raw_evidence_list), "new_items_saved": created_count, "signals_detected": len(signals)}
    )

    return {
        "success": True,
        "provider": provider,
        "items_fetched": len(raw_evidence_list),
        "new_evidence_saved": created_count,
        "signals_count": len(signals)
    }
