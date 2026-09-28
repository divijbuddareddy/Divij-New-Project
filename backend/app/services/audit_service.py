from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import AuditLog

class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        workspace_id: str,
        action_type: str,
        resource: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        ip_address: Optional[str] = "127.0.0.1"
    ) -> AuditLog:
        """
        Creates an immutable audit record for sensitive operations.
        """
        log_entry = AuditLog(
            workspace_id=workspace_id,
            user_id=user_id,
            actor_email=actor_email or "system@startupops.ai",
            action_type=action_type,
            resource=resource,
            details=details,
            ip_address=ip_address,
            timestamp=datetime.utcnow()
        )
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        return log_entry
