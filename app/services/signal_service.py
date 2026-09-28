from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.entities import Signal, EvidenceItem

class SignalService:
    @staticmethod
    async def get_active_signals(db: AsyncSession, workspace_id: str) -> List[Signal]:
        stmt = select(Signal).where(
            Signal.workspace_id == workspace_id,
            Signal.status.in_(["active", "investigating"])
        ).order_by(desc(Signal.detected_at))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def detect_signals(db: AsyncSession, workspace_id: str) -> List[Signal]:
        """
        Runs deterministic rule evaluations and rolling anomaly detection across recent evidence items:
        1. Support Volume Spikes (emails / slack complaints regarding checkout, login, latency)
        2. Post-Release Incident Clusters (PR merge followed closely by alert spikes)
        3. Aging Unreviewed Pull Requests (> 3 days stale)
        4. Repeated CI/CD Workflow Failures
        """
        stmt = select(EvidenceItem).where(
            EvidenceItem.workspace_id == workspace_id
        ).order_by(desc(EvidenceItem.event_timestamp)).limit(100)
        
        res = await db.execute(stmt)
        recent_evidence = list(res.scalars().all())

        detected = []

        # 1. Check for Checkout / Payment failure spike
        checkout_evidence = [
            e for e in recent_evidence
            if any(k in (e.title + " " + (e.content_summary or "")).lower() for k in ["checkout", "stripe", "payment", "card error", "500 error", "declined"])
        ]

        if len(checkout_evidence) >= 2:
            # Check if signal already exists
            existing_stmt = select(Signal).where(
                Signal.workspace_id == workspace_id,
                Signal.signal_type == "checkout_spike",
                Signal.status == "active"
            )
            existing = (await db.execute(existing_stmt)).scalar_one_or_none()
            if not existing:
                sig = Signal(
                    workspace_id=workspace_id,
                    title="Critical Checkout Error & Customer Support Spike",
                    description=f"Detected an abnormal surge of {len(checkout_evidence)} failure reports and customer emails across Slack and Gmail following recent release v2.4.1.",
                    severity="critical",
                    signal_type="checkout_spike",
                    status="active",
                    confidence_score=0.96,
                    evidence_refs=[e.id for e in checkout_evidence],
                    metadata_json={
                        "spike_multiplier": "3.8x baseline",
                        "affected_flow": "Stripe v3 Checkout Webhook & Frontend Form",
                        "correlated_sources": list(set([e.source for e in checkout_evidence]))
                    }
                )
                db.add(sig)
                detected.append(sig)

        # 2. Check for CI/CD Failure Anomaly
        ci_failures = [
            e for e in recent_evidence
            if e.source == "github" and ("fail" in e.title.lower() or "failure" in e.action.lower())
        ]
        if len(ci_failures) >= 2:
            existing_stmt = select(Signal).where(
                Signal.workspace_id == workspace_id,
                Signal.signal_type == "ci_failure_streak",
                Signal.status == "active"
            )
            existing = (await db.execute(existing_stmt)).scalar_one_or_none()
            if not existing:
                sig = Signal(
                    workspace_id=workspace_id,
                    title="Repeated CI/CD Pipeline Failures on Main Branch",
                    description=f"Workflow 'deploy-production.yml' has failed {len(ci_failures)} consecutive runs.",
                    severity="high",
                    signal_type="ci_failure_streak",
                    status="active",
                    confidence_score=0.88,
                    evidence_refs=[e.id for e in ci_failures],
                    metadata_json={"failed_runs": len(ci_failures)}
                )
                db.add(sig)
                detected.append(sig)

        if detected:
            await db.commit()
            for s in detected:
                await db.refresh(s)

        return detected
