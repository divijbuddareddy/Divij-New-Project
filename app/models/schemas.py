from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Auth & User schemas
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: datetime
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Workspace schemas
class WorkspaceCreate(BaseModel):
    name: str
    slug: Optional[str] = None

class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime
    class Config:
        from_attributes = True

# Integrations
class IntegrationConnectRequest(BaseModel):
    provider: str
    account_name: str
    credentials: Dict[str, Any]
    scopes: Optional[List[str]] = []

class IntegrationResponse(BaseModel):
    id: str
    workspace_id: str
    provider: str
    account_name: str
    status: str
    scopes: List[str]
    last_synced_at: Optional[datetime]
    created_at: datetime
    class Config:
        from_attributes = True

# Evidence
class EvidenceResponse(BaseModel):
    id: str
    workspace_id: str
    source: str
    actor: str
    action: str
    object_id: str
    title: str
    content_summary: Optional[str]
    raw_payload: Dict[str, Any]
    event_timestamp: datetime
    class Config:
        from_attributes = True

# Signal
class SignalResponse(BaseModel):
    id: str
    workspace_id: str
    title: str
    description: str
    severity: str
    signal_type: str
    status: str
    confidence_score: float
    evidence_refs: List[str]
    metadata_json: Dict[str, Any]
    detected_at: datetime
    class Config:
        from_attributes = True

# Investigation
class InvestigationCreate(BaseModel):
    signal_id: Optional[str] = None
    title: str
    query: Optional[str] = None

class InvestigationResponse(BaseModel):
    id: str
    workspace_id: str
    signal_id: Optional[str]
    title: str
    summary: str
    status: str
    confidence_score: float
    timeline: List[Dict[str, Any]]
    hypotheses: List[Dict[str, Any]]
    evidence_refs: List[str]
    created_at: datetime
    class Config:
        from_attributes = True

# Actions & Approval
class ActionItemResponse(BaseModel):
    id: str
    action_plan_id: str
    workspace_id: str
    provider: str
    action_type: str
    target: str
    parameters: Dict[str, Any]
    risk_level: str
    status: str
    idempotency_key: str
    created_at: datetime
    class Config:
        from_attributes = True

class ActionPlanResponse(BaseModel):
    id: str
    investigation_id: str
    workspace_id: str
    title: str
    summary: str
    status: str
    actions: List[ActionItemResponse] = []
    created_at: datetime
    class Config:
        from_attributes = True

class ApprovalDecisionRequest(BaseModel):
    decision: str  # approved, rejected
    notes: Optional[str] = None

class ActionExecuteRequest(BaseModel):
    idempotency_key: Optional[str] = None

# Agent Runs
class AgentRunRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None

class AgentRunResponse(BaseModel):
    id: str
    workspace_id: str
    query: str
    intent: Optional[str]
    status: str
    plan: List[Dict[str, Any]]
    final_response: Optional[str]
    evidence_refs: List[str]
    proposed_actions: List[Dict[str, Any]]
    started_at: datetime
    completed_at: Optional[datetime]
    class Config:
        from_attributes = True

# Audit
class AuditLogResponse(BaseModel):
    id: str
    workspace_id: str
    actor_email: Optional[str]
    action_type: str
    resource: str
    details: Dict[str, Any]
    timestamp: datetime
    class Config:
        from_attributes = True
