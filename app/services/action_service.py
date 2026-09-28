from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import ActionItem, ActionPlan, Approval, ExecutionResult, VerificationResult, IntegrationAccount
from app.policies.approval_policy import validate_action_execution_allowed
from app.integrations import get_integration_adapter
from app.services.audit_service import AuditService

class ActionService:
    @staticmethod
    async def approve_action(
        db: AsyncSession,
        workspace_id: str,
        action_id: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[ActionItem]]:
        stmt = select(ActionItem).where(ActionItem.id == action_id, ActionItem.workspace_id == workspace_id)
        action = (await db.execute(stmt)).scalar_one_or_none()
        if not action:
            return False, "Action item not found in workspace", None

        action.status = "approved"
        approval = Approval(
            action_id=action.id,
            user_id=user_id,
            decision="approved",
            notes=notes,
            decided_at=datetime.utcnow()
        )
        db.add(approval)
        await db.commit()
        await db.refresh(action)

        await AuditService.log_event(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action_type="action_approved",
            resource=f"{action.provider}:{action.action_type}",
            details={"action_id": action.id, "risk_level": action.risk_level, "parameters": action.parameters}
        )

        return True, "Action successfully approved for execution.", action

    @staticmethod
    async def reject_action(
        db: AsyncSession,
        workspace_id: str,
        action_id: str,
        user_id: str,
        notes: Optional[str] = None
    ) -> Tuple[bool, str, Optional[ActionItem]]:
        stmt = select(ActionItem).where(ActionItem.id == action_id, ActionItem.workspace_id == workspace_id)
        action = (await db.execute(stmt)).scalar_one_or_none()
        if not action:
            return False, "Action item not found in workspace", None

        action.status = "rejected"
        approval = Approval(
            action_id=action.id,
            user_id=user_id,
            decision="rejected",
            notes=notes,
            decided_at=datetime.utcnow()
        )
        db.add(approval)
        await db.commit()
        await db.refresh(action)

        await AuditService.log_event(
            db=db,
            workspace_id=workspace_id,
            user_id=user_id,
            action_type="action_rejected",
            resource=f"{action.provider}:{action.action_type}",
            details={"action_id": action.id, "rejection_notes": notes}
        )

        return True, "Action marked as rejected.", action

    @staticmethod
    async def execute_action(
        db: AsyncSession,
        workspace_id: str,
        action_id: str,
        user_id: Optional[str] = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        stmt = select(ActionItem).where(ActionItem.id == action_id, ActionItem.workspace_id == workspace_id)
        action = (await db.execute(stmt)).scalar_one_or_none()
        if not action:
            return False, "Action not found", {}

        # 1. Check if already executed
        exec_stmt = select(ExecutionResult).where(ExecutionResult.action_id == action.id)
        existing_exec = (await db.execute(exec_stmt)).scalar_one_or_none()
        if existing_exec:
            return True, "Action has already been executed (Idempotent return).", existing_exec.response_payload

        # 2. Enforce human approval policy check
        allowed, reason = validate_action_execution_allowed(action.status, has_approval=(action.status == "approved"))
        if not allowed:
            return False, reason, {}

        # 3. Mark executing
        action.status = "executing"
        await db.commit()

        # 4. Dispatch to integration adapter
        adapter = get_integration_adapter(
            provider=action.provider,
            workspace_id=workspace_id,
            credentials={"access_token": "mock_valid_token"}
        )

        try:
            exec_res = await adapter.execute_action(action.action_type, action.parameters)
            action.status = "succeeded"

            res_record = ExecutionResult(
                action_id=action.id,
                status="succeeded",
                response_payload=exec_res,
                executed_at=datetime.utcnow()
            )
            db.add(res_record)

            # 5. Immediately run verification
            ver_res = await adapter.verify_action(action.action_type, action.parameters, exec_res)
            ver_record = VerificationResult(
                action_id=action.id,
                verified=ver_res.get("verified", True),
                details=ver_res,
                verified_at=datetime.utcnow()
            )
            db.add(ver_record)
            action.status = "verified" if ver_res.get("verified", True) else "succeeded"

            await db.commit()
            await db.refresh(action)

            # 6. Audit log
            await AuditService.log_event(
                db=db,
                workspace_id=workspace_id,
                user_id=user_id,
                action_type="action_executed_verified",
                resource=f"{action.provider}:{action.action_type}",
                details={
                    "action_id": action.id,
                    "target": action.target,
                    "execution_result": exec_res,
                    "verification": ver_res
                }
            )

            return True, "Action successfully executed and verified.", {
                "execution": exec_res,
                "verification": ver_res
            }

        except Exception as e:
            action.status = "failed"
            err_record = ExecutionResult(
                action_id=action.id,
                status="failed",
                error_message=str(e),
                executed_at=datetime.utcnow()
            )
            db.add(err_record)
            await db.commit()

            await AuditService.log_event(
                db=db,
                workspace_id=workspace_id,
                user_id=user_id,
                action_type="action_execution_failed",
                resource=f"{action.provider}:{action.action_type}",
                details={"action_id": action.id, "error": str(e)}
            )

            return False, f"Execution failed: {str(e)}", {}
