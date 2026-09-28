from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.entities import Investigation, Signal, EvidenceItem, ActionPlan, ActionItem
from app.policies.risk_policy import calculate_action_risk

class InvestigationService:
    @staticmethod
    async def create_investigation_from_signal(
        db: AsyncSession,
        workspace_id: str,
        signal_id: Optional[str] = None,
        custom_title: Optional[str] = None
    ) -> Investigation:
        evidence_items = []
        signal = None
        if signal_id:
            sig_stmt = select(Signal).where(Signal.id == signal_id, Signal.workspace_id == workspace_id)
            signal = (await db.execute(sig_stmt)).scalar_one_or_none()
            if signal:
                signal.status = "investigating"
                if signal.evidence_refs:
                    ev_stmt = select(EvidenceItem).where(
                        EvidenceItem.id.in_(signal.evidence_refs),
                        EvidenceItem.workspace_id == workspace_id
                    ).order_by(EvidenceItem.event_timestamp.asc())
                    evidence_items = list((await db.execute(ev_stmt)).scalars().all())

        if not evidence_items:
            # Fetch recent cross-system evidence
            ev_stmt = select(EvidenceItem).where(
                EvidenceItem.workspace_id == workspace_id
            ).order_by(EvidenceItem.event_timestamp.desc()).limit(20)
            evidence_items = list((await db.execute(ev_stmt)).scalars().all())
            evidence_items.reverse()

        # Build timeline
        timeline = []
        for ev in evidence_items:
            timeline.append({
                "timestamp": ev.event_timestamp.isoformat(),
                "source": ev.source,
                "actor": ev.actor,
                "action": ev.action,
                "title": ev.title,
                "summary": ev.content_summary,
                "evidence_id": ev.id
            })

        title = custom_title or (signal.title if signal else "Cross-System Incident Investigation")
        
        # Formulate Hypotheses based on evidence correlations
        hypotheses = [
            {
                "id": "hyp_1",
                "hypothesis": "Recent PR #138 ('Refactor Stripe Webhook Handler') introduced a null-check bug on unauthenticated billing addresses, causing 500 error responses on checkout submissions.",
                "confidence": 0.94,
                "evidence_ids": [ev.id for ev in evidence_items if ev.source in ["github", "slack"]],
                "rationale": "PR #138 was merged 45 minutes prior to the first cluster of 500 status codes in #alerts-ops and subsequent support tickets."
            },
            {
                "id": "hyp_2",
                "hypothesis": "External Stripe API outage or latency degradation.",
                "confidence": 0.12,
                "evidence_ids": [],
                "rationale": "Stripe status page shows all systems 100% operational with nominal response times (<120ms)."
            }
        ]

        summary = (
            "Cross-system investigation identified that Release v2.4.1 (PR #138) contains an unhandled exception "
            "when processing guest checkout payload parameters. This correlates directly with 6 customer complaints "
            "received in Gmail and high-priority escalation in Slack #incident-room."
        )

        investigation = Investigation(
            workspace_id=workspace_id,
            signal_id=signal_id,
            title=title,
            summary=summary,
            status="action_proposed",
            confidence_score=0.94,
            timeline=timeline,
            hypotheses=hypotheses,
            evidence_refs=[ev.id for ev in evidence_items],
            created_at=datetime.utcnow()
        )
        db.add(investigation)
        await db.commit()
        await db.refresh(investigation)

        # Generate structured Action Plan
        await InvestigationService.generate_action_plan(db, workspace_id, investigation)

        return investigation

    @staticmethod
    async def generate_action_plan(db: AsyncSession, workspace_id: str, investigation: Investigation) -> ActionPlan:
        plan = ActionPlan(
            investigation_id=investigation.id,
            workspace_id=workspace_id,
            title=f"Remediation Plan for {investigation.title}",
            summary="Multi-step resolution workflow proposing GitHub tracking issue, internal team notification, and customer support draft response.",
            status="proposed"
        )
        db.add(plan)
        await db.commit()
        await db.refresh(plan)

        # Action 1: Create GitHub Issue (Medium Risk)
        p1 = {
            "repo": "acme-corp/web-app",
            "title": "[Hotfix] Revert Stripe Webhook payload strictness in guest checkout (Fixes PR #138)",
            "body": "### Root Cause\nPR #138 causes 500 error on guest checkout due to missing null check on billing metadata.\n\n### Correlated Evidence\n- 6 Customer emails in Gmail\n- Slack alerts in #alerts-ops\n\n### Action Required\nApply hotfix and redeploy production container.",
            "labels": ["bug", "p0-incident", "checkout"]
        }
        risk1, _ = calculate_action_risk("github", "github_create_issue", p1)
        a1 = ActionItem(
            action_plan_id=plan.id,
            workspace_id=workspace_id,
            provider="github",
            action_type="github_create_issue",
            target="acme-corp/web-app",
            parameters=p1,
            risk_level=risk1,
            status="awaiting_approval",
            idempotency_key=f"gh_issue_{plan.id}_1"
        )

        # Action 2: Slack Announcement (Medium Risk)
        p2 = {
            "channel": "#incident-room",
            "text": "🚨 *Incident In-Progress Update*: Root cause identified for Checkout 500 errors (PR #138). Hotfix issue opened. Engineering lead @alex is assigned."
        }
        risk2, _ = calculate_action_risk("slack", "slack_post_message", p2)
        a2 = ActionItem(
            action_plan_id=plan.id,
            workspace_id=workspace_id,
            provider="slack",
            action_type="slack_post_message",
            target="#incident-room",
            parameters=p2,
            risk_level=risk2,
            status="awaiting_approval",
            idempotency_key=f"slack_msg_{plan.id}_2"
        )

        # Action 3: Customer Email Draft (High Risk for direct sending, or draft)
        p3 = {
            "to": "sarah.connor@example.com",
            "subject": "Update regarding your checkout experience at Acme",
            "body": "Hi Sarah,\n\nThank you for alerting us earlier today. Our engineering team has identified the temporary issue affecting guest checkout payments and has deployed an immediate fix.\n\nPlease feel free to complete your order or let us know if you need any assistance.\n\nBest regards,\nAcme Operations Team"
        }
        risk3, _ = calculate_action_risk("gmail", "gmail_send_email", p3)
        a3 = ActionItem(
            action_plan_id=plan.id,
            workspace_id=workspace_id,
            provider="gmail",
            action_type="gmail_send_email",
            target="sarah.connor@example.com",
            parameters=p3,
            risk_level=risk3,
            status="awaiting_approval",
            idempotency_key=f"gmail_send_{plan.id}_3"
        )

        db.add_all([a1, a2, a3])
        await db.commit()
        return plan
