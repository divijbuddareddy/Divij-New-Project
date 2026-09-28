from pydantic import BaseModel, Field
from typing import List, Optional
from app.tools.registry import registry

class GmailSearchThreadsInput(BaseModel):
    query: str = Field(description="Search query string, e.g. 'checkout failure' or 'label:support'")
    limit: Optional[int] = Field(default=10, description="Max threads to search")

class GmailSendEmailInput(BaseModel):
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email message content")

@registry.register(
    name="gmail_search_threads",
    description="Search and read email threads in Gmail.",
    provider="gmail",
    is_write=False,
    risk_level="low",
    schema=GmailSearchThreadsInput
)
async def gmail_search_threads(query: str, limit: int = 10):
    return {"query": query, "threads_found": 3}

@registry.register(
    name="gmail_send_email",
    description="Send an email to a customer or external partner.",
    provider="gmail",
    is_write=True,
    risk_level="high",
    schema=GmailSendEmailInput
)
async def gmail_send_email(to: str, subject: str, body: str):
    return {
        "status": "proposed_action",
        "action_type": "gmail_send_email",
        "parameters": {"to": to, "subject": subject, "body": body}
    }
