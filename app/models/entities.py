import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    memberships = relationship("WorkspaceMember", back_populates="user", cascade="all, delete-orphan")

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    integrations = relationship("IntegrationAccount", back_populates="workspace", cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceItem", back_populates="workspace", cascade="all, delete-orphan")
    signals = relationship("Signal", back_populates="workspace", cascade="all, delete-orphan")
    investigations = relationship("Investigation", back_populates="workspace", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="workspace", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="workspace", cascade="all, delete-orphan")

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), default="member")  # owner, admin, engineer, support, sales, member
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="memberships")

class IntegrationAccount(Base):
    __tablename__ = "integration_accounts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # github, gmail, slack, jira, etc.
    account_name = Column(String(255), nullable=False)
    external_account_id = Column(String(255), nullable=True)
    status = Column(String(50), default="connected")  # connected, disconnected, error, syncing
    scopes = Column(JSON, default=list)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="integrations")
    credential = relationship("EncryptedCredential", back_populates="integration", uselist=False, cascade="all, delete-orphan")

class EncryptedCredential(Base):
    __tablename__ = "encrypted_credentials"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    integration_id = Column(String(36), ForeignKey("integration_accounts.id", ondelete="CASCADE"), unique=True, nullable=False)
    ciphertext = Column(Text, nullable=False)
    iv = Column(String(255), nullable=False)
    token_type = Column(String(50), default="bearer")
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    integration = relationship("IntegrationAccount", back_populates="credential")

class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    source = Column(String(50), nullable=False, index=True)  # github, gmail, slack, stripe, etc.
    actor = Column(String(255), nullable=False)
    action = Column(String(100), nullable=False)  # commit_pushed, pr_merged, email_received, slack_alert_posted
    object_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    content_summary = Column(Text, nullable=True)
    raw_payload = Column(JSON, default=dict)
    event_timestamp = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="evidence_items")

class Signal(Base):
    __tablename__ = "signals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(50), default="medium")  # low, medium, high, critical
    signal_type = Column(String(100), nullable=False)  # support_spike, checkout_failure, aging_pr, ci_failure
    status = Column(String(50), default="active")  # active, investigating, resolved, dismissed
    confidence_score = Column(Float, default=0.85)
    evidence_refs = Column(JSON, default=list)  # List of EvidenceItem IDs
    metadata_json = Column(JSON, default=dict)
    detected_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="signals")

class Investigation(Base):
    __tablename__ = "investigations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    signal_id = Column(String(36), ForeignKey("signals.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(50), default="in_progress")  # in_progress, concluded, action_proposed, resolved
    confidence_score = Column(Float, default=0.90)
    timeline = Column(JSON, default=list)
    hypotheses = Column(JSON, default=list)  # [{"id": 1, "hypothesis": "...", "confidence": 0.92, "evidence_ids": [...]}]
    evidence_refs = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    workspace = relationship("Workspace", back_populates="investigations")
    action_plans = relationship("ActionPlan", back_populates="investigation", cascade="all, delete-orphan")

class ActionPlan(Base):
    __tablename__ = "action_plans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    investigation_id = Column(String(36), ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    status = Column(String(50), default="proposed")  # proposed, partially_approved, fully_approved, executing, completed
    created_at = Column(DateTime, default=datetime.utcnow)

    investigation = relationship("Investigation", back_populates="action_plans")
    actions = relationship("ActionItem", back_populates="action_plan", cascade="all, delete-orphan")

class ActionItem(Base):
    __tablename__ = "action_items"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action_plan_id = Column(String(36), ForeignKey("action_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # github, slack, gmail
    action_type = Column(String(100), nullable=False)  # create_github_issue, post_slack_notification, send_customer_email
    target = Column(String(255), nullable=False)
    parameters = Column(JSON, default=dict)
    risk_level = Column(String(50), default="medium")  # low, medium, high, critical
    status = Column(String(50), default="awaiting_approval")  # awaiting_approval, approved, rejected, executing, succeeded, failed, verified
    idempotency_key = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    action_plan = relationship("ActionPlan", back_populates="actions")
    approvals = relationship("Approval", back_populates="action", cascade="all, delete-orphan")
    execution_result = relationship("ExecutionResult", back_populates="action", uselist=False, cascade="all, delete-orphan")
    verification_result = relationship("VerificationResult", back_populates="action", uselist=False, cascade="all, delete-orphan")

class Approval(Base):
    __tablename__ = "approvals"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action_id = Column(String(36), ForeignKey("action_items.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    decision = Column(String(50), nullable=False)  # approved, rejected
    notes = Column(Text, nullable=True)
    decided_at = Column(DateTime, default=datetime.utcnow)

    action = relationship("ActionItem", back_populates="approvals")

class ExecutionResult(Base):
    __tablename__ = "execution_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action_id = Column(String(36), ForeignKey("action_items.id", ondelete="CASCADE"), unique=True, nullable=False)
    status = Column(String(50), nullable=False)  # succeeded, failed
    response_payload = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    action = relationship("ActionItem", back_populates="execution_result")

class VerificationResult(Base):
    __tablename__ = "verification_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    action_id = Column(String(36), ForeignKey("action_items.id", ondelete="CASCADE"), unique=True, nullable=False)
    verified = Column(Boolean, default=False)
    details = Column(JSON, default=dict)
    verified_at = Column(DateTime, default=datetime.utcnow)

    action = relationship("ActionItem", back_populates="verification_result")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), nullable=True)
    actor_email = Column(String(255), nullable=True)
    action_type = Column(String(100), nullable=False)  # auth_login, tool_call, approval_granted, action_executed, policy_violation
    resource = Column(String(255), nullable=False)
    details = Column(JSON, default=dict)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    workspace = relationship("Workspace", back_populates="audit_logs")

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(String(36), nullable=True)
    query = Column(Text, nullable=False)
    intent = Column(String(100), nullable=True)
    status = Column(String(50), default="running")  # running, completed, error
    plan = Column(JSON, default=list)
    final_response = Column(Text, nullable=True)
    evidence_refs = Column(JSON, default=list)
    proposed_actions = Column(JSON, default=list)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    workspace = relationship("Workspace", back_populates="agent_runs")
