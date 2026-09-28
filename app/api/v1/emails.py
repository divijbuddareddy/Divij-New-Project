from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.database import get_db
from app.models.entities import EvidenceItem, IntegrationAccount, EncryptedCredential
from app.security import decrypt_token
from app.integrations import get_integration_adapter
from app.agents.graph import OperationsAgentHub
from app.services.audit_service import AuditService

router = APIRouter(prefix="/emails", tags=["Interactive Emails"])

class EmailItemResponse(BaseModel):
    id: str
    sender: str
    subject: str
    snippet: str
    body: Optional[str] = None
    date: str
    raw_payload: Dict[str, Any]

class DraftReplyRequest(BaseModel):
    email_id: Optional[str] = None
    sender: str
    subject: str
    original_text: str
    custom_instructions: Optional[str] = "Be professional, helpful, and concise."

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str

@router.get("", response_model=List[EmailItemResponse])
async def list_workspace_emails(
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    ws_id = x_workspace_id or "default"
    
    # Verify gmail is actually connected
    int_stmt = select(IntegrationAccount).where(
        (IntegrationAccount.provider.in_(["gmail", "google"])) &
        (IntegrationAccount.status == "connected") &
        ((IntegrationAccount.workspace_id == ws_id) | (IntegrationAccount.workspace_id == "default") | (IntegrationAccount.workspace_id == None))
    )
    gmail_acc = (await db.execute(int_stmt)).scalars().first()
    if not gmail_acc:
        return []

    stmt = select(EvidenceItem).where(
        EvidenceItem.workspace_id == ws_id,
        EvidenceItem.source == "gmail"
    ).order_by(desc(EvidenceItem.event_timestamp)).limit(30)
    
    res = await db.execute(stmt)
    items = list(res.scalars().all())

    email_list = []
    for it in items:
        payload = it.raw_payload or {}
        email_list.append({
            "id": it.id,
            "sender": it.actor,
            "subject": payload.get("subject") or it.title.replace("Email: ", ""),
            "snippet": it.content_summary or "",
            "body": payload.get("body") or it.content_summary,
            "date": payload.get("date") or it.event_timestamp.strftime("%b %d, %H:%M"),
            "raw_payload": payload
        })
    return email_list

@router.post("/draft-reply")
async def generate_ai_draft_reply(
    payload: DraftReplyRequest,
    x_workspace_id: Optional[str] = Header(None)
):
    """
    Uses Google Gemini to craft a contextual reply to the email.
    """
    prompt = (
        f"Incoming Email:\n"
        f"From: {payload.sender}\n"
        f"Subject: {payload.subject}\n"
        f"Content:\n{payload.original_text}\n\n"
        f"Instructions: {payload.custom_instructions}\n"
        f"Write an email reply. Return ONLY the body text of the response."
    )
    system_prompt = "You are an executive operations and customer success assistant writing a clear, professional email reply."

    gemini_reply = await OperationsAgentHub.call_gemini(prompt, system_prompt)

    if not gemini_reply:
        # High quality template fallback
        gemini_reply = (
            f"Hi {payload.sender.split('<')[0].strip() or 'there'},\n\n"
            f"Thank you for reaching out regarding '{payload.subject}'.\n\n"
            f"We have received your message and are looking into this immediately. Our engineering and operations team has been notified, and we will follow up with you as soon as possible.\n\n"
            f"Best regards,\nOperations Team"
        )

    reply_subject = payload.subject if payload.subject.lower().startswith("re:") else f"Re: {payload.subject}"

    return {
        "to": payload.sender,
        "subject": reply_subject,
        "draft_body": gemini_reply
    }

@router.post("/send")
async def send_email_reply(
    payload: SendEmailRequest,
    x_workspace_id: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Sends the real email reply through the connected Gmail account.
    """
    ws_id = x_workspace_id or "default"

    # Get Gmail integration account
    stmt = select(IntegrationAccount).where(
        IntegrationAccount.workspace_id == ws_id,
        IntegrationAccount.provider == "gmail"
    )
    integ = (await db.execute(stmt)).scalar_one_or_none()
    if not integ:
        stmt_any = select(IntegrationAccount).where(IntegrationAccount.provider == "gmail")
        integ = (await db.execute(stmt_any)).scalar_one_or_none()
        if not integ:
            raise HTTPException(status_code=400, detail="Gmail account is not connected.")

    token = ""
    cred_stmt = select(EncryptedCredential).where(EncryptedCredential.integration_id == integ.id)
    cred = (await db.execute(cred_stmt)).scalar_one_or_none()
    if cred:
        try:
            token = decrypt_token(cred.ciphertext, cred.iv)
        except Exception:
            token = ""

    adapter = get_integration_adapter(
        provider="gmail",
        workspace_id=ws_id,
        credentials={
            "access_token": token,
            "token": token,
            "account_name": integ.account_name
        }
    )

    try:
        exec_res = await adapter.execute_action(
            action_type="gmail_send_email",
            parameters={
                "to": payload.to,
                "subject": payload.subject,
                "body": payload.body
            }
        )

        await AuditService.log_event(
            db=db,
            workspace_id=ws_id,
            action_type="email_dispatched",
            resource=f"gmail:{payload.to}",
            details={"to": payload.to, "subject": payload.subject, "result": exec_res}
        )

        return {
            "success": True,
            "message": f"Email successfully sent to {payload.to}!",
            "details": exec_res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
