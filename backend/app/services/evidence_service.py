import hashlib
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.entities import EvidenceItem

class EvidenceService:
    @staticmethod
    def compute_evidence_hash(source: str, actor: str, action: str, object_id: str, timestamp: datetime) -> str:
        payload = f"{source}:{actor}:{action}:{object_id}:{timestamp.isoformat()}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    async def create_evidence(
        db: AsyncSession,
        workspace_id: str,
        source: str,
        actor: str,
        action: str,
        object_id: str,
        title: str,
        content_summary: str,
        raw_payload: Dict[str, Any],
        event_timestamp: datetime
    ) -> EvidenceItem:
        evidence = EvidenceItem(
            workspace_id=workspace_id,
            source=source,
            actor=actor,
            action=action,
            object_id=object_id,
            title=title,
            content_summary=content_summary,
            raw_payload=raw_payload,
            event_timestamp=event_timestamp
        )
        db.add(evidence)
        await db.commit()
        await db.refresh(evidence)
        return evidence

    @staticmethod
    async def query_evidence(
        db: AsyncSession,
        workspace_id: str,
        source: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 50
    ) -> List[EvidenceItem]:
        stmt = select(EvidenceItem).where(EvidenceItem.workspace_id == workspace_id)
        if source:
            stmt = stmt.where(EvidenceItem.source == source)
        stmt = stmt.order_by(desc(EvidenceItem.event_timestamp)).limit(limit)
        result = await db.execute(stmt)
        items = result.scalars().all()

        if query:
            q_lower = query.lower()
            return [
                it for it in items
                if q_lower in it.title.lower() or (it.content_summary and q_lower in it.content_summary.lower())
            ]
        return list(items)
