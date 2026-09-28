from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import Workspace, User, WorkspaceMember, IntegrationAccount, EncryptedCredential, EvidenceItem, Signal
from app.security import encrypt_token, get_password_hash
from app.services.signal_service import SignalService

class SeedService:
    @staticmethod
    async def seed_acceptance_scenario(db: AsyncSession, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Seeds the end-to-end acceptance scenario dataset:
        1. Default Workspace 'Acme Technologies Inc'
        2. Admin user 'founder@acme.com'
        3. Connected Integrations (GitHub, Gmail, Slack)
        4. Cross-system evidence stream:
           - GitHub: PR #138 'Refactor Stripe Webhook Handler' merged to main
           - GitHub: Release v2.4.1 deployed
           - Slack: #alerts-ops Bot posting 'CRITICAL: HTTP 500 spike on /api/checkout/submit'
           - Slack: #incident-room 'Multiple customer tickets coming in for checkout failure'
           - Gmail: Support ticket from Sarah Connor 'Unable to complete checkout - payment failed error'
           - Gmail: Support ticket from Mark Davis 'Checkout stuck on payment processing screen'
           - Gmail: Support ticket from Elena Rostova 'Error 500 when entering corporate card'
        5. Generated Signal & baseline data
        """
        # 1. Create or get default workspace
        workspace = None
        if workspace_id:
            ws_stmt = select(Workspace).where(Workspace.id == workspace_id)
            workspace = (await db.execute(ws_stmt)).scalar_one_or_none()

        if not workspace:
            ws_stmt = select(Workspace).where(Workspace.slug == "acme-technologies")
            workspace = (await db.execute(ws_stmt)).scalar_one_or_none()

        if not workspace:
            workspace = Workspace(
                name="Acme Technologies Inc",
                slug="acme-technologies"
            )
            db.add(workspace)
            await db.commit()
            await db.refresh(workspace)

        # 2. Create or get admin user
        user_stmt = select(User).where(User.email == "founder@acme.com")
        user = (await db.execute(user_stmt)).scalar_one_or_none()
        if not user:
            user = User(
                email="founder@acme.com",
                name="Sarah Jenkins (Founder)",
                hashed_password=get_password_hash("StartupOps2026!Secure")
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            membership = WorkspaceMember(
                workspace_id=workspace.id,
                user_id=user.id,
                role="owner"
            )
            db.add(membership)
            await db.commit()

        # 3. Create or update Integrations (GitHub, Gmail, Slack)
        integrations_data = [
            {
                "provider": "github",
                "account_name": "acme-corp/web-app",
                "scopes": ["repo", "read:org", "workflow"],
                "token": "ghp_mock_token_acme_startupops"
            },
            {
                "provider": "gmail",
                "account_name": "support@acme.com",
                "scopes": ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.compose", "https://www.googleapis.com/auth/gmail.send"],
                "token": "ya29.mock_gmail_oauth_token"
            },
            {
                "provider": "slack",
                "account_name": "Acme Ventures Workspace",
                "scopes": ["channels:read", "chat:write", "groups:read"],
                "token": "xoxb-mock-slack-bot-token"
            }
        ]

        for item in integrations_data:
            stmt = select(IntegrationAccount).where(
                IntegrationAccount.workspace_id == workspace.id,
                IntegrationAccount.provider == item["provider"]
            )
            existing_integ = (await db.execute(stmt)).scalar_one_or_none()
            if not existing_integ:
                integ = IntegrationAccount(
                    workspace_id=workspace.id,
                    provider=item["provider"],
                    account_name=item["account_name"],
                    status="connected",
                    scopes=item["scopes"],
                    last_synced_at=datetime.utcnow()
                )
                db.add(integ)
                await db.commit()
                await db.refresh(integ)

                enc = encrypt_token(item["token"])
                cred = EncryptedCredential(
                    integration_id=integ.id,
                    ciphertext=enc["ciphertext"],
                    iv=enc["iv"]
                )
                db.add(cred)
                await db.commit()

        # 4. Insert Acceptance Scenario Evidence Stream
        now = datetime.utcnow()
        t0 = now - timedelta(hours=2, minutes=30)
        t1 = now - timedelta(hours=2, minutes=15)
        t2 = now - timedelta(hours=1, minutes=45)
        t3 = now - timedelta(hours=1, minutes=30)
        t4 = now - timedelta(hours=1, minutes=10)
        t5 = now - timedelta(minutes=45)
        t6 = now - timedelta(minutes=20)

        evidence_items_data = [
            {
                "source": "github",
                "actor": "alex.dev@acme.com",
                "action": "pr_merged",
                "object_id": "PR-138",
                "title": "PR #138 Merged: Refactor Stripe Webhook and Checkout Payload Validation",
                "content_summary": "Merged 8 files (+142, -58). Modified checkout_handler.py, billing_validator.py to enforce strict billing address fields.",
                "raw_payload": {"pr_number": 138, "branch": "feature/stripe-v3-upgrade", "author": "alex.dev", "merged_by": "dev-lead"},
                "timestamp": t0
            },
            {
                "source": "github",
                "actor": "github-actions[bot]",
                "action": "release_published",
                "object_id": "Release-v2.4.1",
                "title": "Production Release v2.4.1 Tagged & Deployed",
                "content_summary": "Docker build succeeded. Container deployed to production cluster across 4 instances.",
                "raw_payload": {"tag": "v2.4.1", "commit": "a8f39b2", "environment": "production"},
                "timestamp": t1
            },
            {
                "source": "slack",
                "actor": "Datadog Alert Bot",
                "action": "alert_triggered",
                "object_id": "MSG-9021",
                "title": "CRITICAL Alert in #alerts-ops: 500 Internal Server Error Spike",
                "content_summary": "HTTP 500 error rate on POST /api/checkout/submit spiked to 18.4% (Threshold: > 1.0%). Triggered runbook P0.",
                "raw_payload": {"channel": "#alerts-ops", "service": "billing-service", "error_code": "500", "p95_latency_ms": 3400},
                "timestamp": t2
            },
            {
                "source": "slack",
                "actor": "emily.support@acme.com",
                "action": "message_posted",
                "object_id": "MSG-9025",
                "title": "Support Escalation in #incident-room: Customers reporting broken checkout",
                "content_summary": "Hey team, getting multiple live chat messages that the 'Pay Now' button throws an error on guest checkout. Is there a known issue?",
                "raw_payload": {"channel": "#incident-room", "thread_id": "th_incident_001", "urgency": "high"},
                "timestamp": t3
            },
            {
                "source": "gmail",
                "actor": "sarah.connor@cyberdyne.org",
                "action": "email_received",
                "object_id": "EMAIL-101",
                "title": "Support Ticket: Urgent - Cannot complete $4,200 annual enterprise plan payment",
                "content_summary": "Hi Support, I tried paying with our corporate Amex card three times, but every time I click Submit Payment the screen turns red and says 'Server Exception 500'. Please help ASAP.",
                "raw_payload": {"from": "sarah.connor@cyberdyne.org", "to": "support@acme.com", "subject": "Urgent - Cannot complete $4,200 annual plan"},
                "timestamp": t4
            },
            {
                "source": "gmail",
                "actor": "mark.davis@venturecap.com",
                "action": "email_received",
                "object_id": "EMAIL-102",
                "title": "Support Ticket: Checkout page throwing error on credit card entry",
                "content_summary": "Trying to upgrade our 10-seat subscription. The checkout form fails on submit with an uncaught error.",
                "raw_payload": {"from": "mark.davis@venturecap.com", "to": "support@acme.com"},
                "timestamp": t5
            },
            {
                "source": "gmail",
                "actor": "elena.rostova@techsolutions.io",
                "action": "email_received",
                "object_id": "EMAIL-103",
                "title": "Billing inquiry: Order stuck at processing step",
                "content_summary": "We keep receiving a 500 error at checkout. We need this provisioned today for our team kickoff.",
                "raw_payload": {"from": "elena.rostova@techsolutions.io", "to": "support@acme.com"},
                "timestamp": t6
            }
        ]

        # Clear old scenario evidence to keep deterministic
        for item in evidence_items_data:
            stmt = select(EvidenceItem).where(
                EvidenceItem.workspace_id == workspace.id,
                EvidenceItem.object_id == item["object_id"]
            )
            existing_ev = (await db.execute(stmt)).scalar_one_or_none()
            if not existing_ev:
                ev = EvidenceItem(
                    workspace_id=workspace.id,
                    source=item["source"],
                    actor=item["actor"],
                    action=item["action"],
                    object_id=item["object_id"],
                    title=item["title"],
                    content_summary=item["content_summary"],
                    raw_payload=item["raw_payload"],
                    event_timestamp=item["timestamp"]
                )
                db.add(ev)

        await db.commit()

        # Run signal detection
        signals = await SignalService.detect_signals(db, workspace.id)

        return {
            "success": True,
            "workspace_id": workspace.id,
            "workspace_name": workspace.name,
            "user_email": user.email,
            "evidence_count": len(evidence_items_data),
            "signals_detected": len(signals)
        }
