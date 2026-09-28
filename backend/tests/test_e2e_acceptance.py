import pytest
import pytest_asyncio
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select
from app.database import Base
from app.models.entities import Workspace, User, Signal, Investigation, ActionPlan, ActionItem, AuditLog
from app.services.seed_service import SeedService
from app.agents import OperationsAgentHub
from app.services.action_service import ActionService

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture
async def test_session():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    
    await engine.dispose()

@pytest.mark.asyncio
async def test_complete_acceptance_scenario(test_session: AsyncSession):
    # Step 1: Connect & Seed acceptance scenario dataset
    seed_result = await SeedService.seed_acceptance_scenario(test_session)
    assert seed_result["success"] is True
    workspace_id = seed_result["workspace_id"]
    assert seed_result["evidence_count"] >= 5

    # Step 2: Ask "What needs my attention today?"
    resp_today = await OperationsAgentHub.run(
        db=test_session,
        workspace_id=workspace_id,
        query="What needs my attention today?"
    )
    assert resp_today["intent"] == "attention_summary"
    assert "Checkout" in resp_today["final_response"] or "payment" in resp_today["final_response"].lower()
    assert len(resp_today["evidence_refs"]) > 0

    # Step 3: Ask "Investigate it."
    resp_investigate = await OperationsAgentHub.run(
        db=test_session,
        workspace_id=workspace_id,
        query="Investigate it."
    )
    assert resp_investigate["intent"] == "investigate"
    assert resp_investigate["confidence_score"] >= 0.90
    assert len(resp_investigate["hypotheses"]) >= 1
    assert "PR #138" in resp_investigate["final_response"]

    # Step 4: Ask "Prepare the fix workflow."
    resp_actions = await OperationsAgentHub.run(
        db=test_session,
        workspace_id=workspace_id,
        query="Prepare the fix workflow."
    )
    assert resp_actions["intent"] == "prepare_actions"
    assert len(resp_actions["proposed_actions"]) == 3
    
    # Check that proposed actions have awaiting_approval status
    gh_action = next(a for a in resp_actions["proposed_actions"] if a["provider"] == "github")
    slack_action = next(a for a in resp_actions["proposed_actions"] if a["provider"] == "slack")
    gmail_action = next(a for a in resp_actions["proposed_actions"] if a["provider"] == "gmail")
    
    assert gh_action["status"] == "awaiting_approval"
    assert slack_action["status"] == "awaiting_approval"
    assert gmail_action["status"] == "awaiting_approval"

    # Step 5: Approve ONLY the GitHub issue
    approved, msg, updated_action = await ActionService.approve_action(
        db=test_session,
        workspace_id=workspace_id,
        action_id=gh_action["id"],
        user_id="usr_admin",
        notes="Approved hotfix issue creation"
    )
    assert approved is True
    assert updated_action.status == "approved"

    # Step 6: Execute the approved GitHub issue
    exec_success, exec_msg, exec_result = await ActionService.execute_action(
        db=test_session,
        workspace_id=workspace_id,
        action_id=gh_action["id"],
        user_id="usr_admin"
    )
    assert exec_success is True
    assert "issue_id" in exec_result["execution"]
    assert exec_result["verification"]["verified"] is True

    # Step 7: Verify other actions (Slack & Gmail) remain UNEXECUTED
    slack_item = (await test_session.execute(select(ActionItem).where(ActionItem.id == slack_action["id"]))).scalar_one()
    gmail_item = (await test_session.execute(select(ActionItem).where(ActionItem.id == gmail_action["id"]))).scalar_one()
    
    assert slack_item.status == "awaiting_approval"
    assert gmail_item.status == "awaiting_approval"

    # Attempting to execute unapproved Slack action MUST fail with policy violation
    blocked_success, blocked_msg, _ = await ActionService.execute_action(
        db=test_session,
        workspace_id=workspace_id,
        action_id=slack_action["id"],
        user_id="usr_admin"
    )
    assert blocked_success is False
    assert "E_POLICY_VIOLATION" in blocked_msg

    # Step 8: Verify Audit Logs contain complete provenance chain
    audit_stmt = select(AuditLog).where(AuditLog.workspace_id == workspace_id)
    audit_entries = list((await test_session.execute(audit_stmt)).scalars().all())
    action_types = [a.action_type for a in audit_entries]
    
    assert "action_approved" in action_types
    assert "action_executed_verified" in action_types
