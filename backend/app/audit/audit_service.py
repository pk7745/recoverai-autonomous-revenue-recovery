import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog
from app.core.enums import ActorType
from app.core.notifications import broadcaster

class AuditService:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        actor: ActorType | str,
        action: str,
        transaction_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        actor_str = actor.value if isinstance(actor, ActorType) else str(actor)
        details_dict = details or {}

        audit_entry = AuditLog(
            id=f"aud_{uuid.uuid4().hex[:14]}",
            workflow_id=workflow_id,
            transaction_id=transaction_id,
            actor=actor_str,
            action=action,
            details=details_dict
        )
        db.add(audit_entry)
        await db.flush()

        # Translate key business events into real-time notifications
        try:
            if action == "RECOVERY_SETTLED_SUCCESSFULLY":
                amount = details_dict.get("recovered_amount", 0.0)
                await broadcaster.broadcast(
                    event_type="PAYMENT_RECOVERED",
                    title="Payment Recovered",
                    message=f"₹{amount:,.2f} successfully recovered and captured via Razorpay.",
                    severity="SUCCESS",
                    workflow_id=workflow_id,
                    transaction_id=transaction_id,
                    amount=amount
                )
            elif action == "ACTION_OVERRIDDEN_TO_HUMAN_ESCALATION":
                reason = details_dict.get("reason", "Requires operational oversight.")
                await broadcaster.broadcast(
                    event_type="HUMAN_REVIEW_REQUIRED",
                    title="Human Review Required",
                    message=f"Automated recovery blocked by Policy Engine. Reason: {reason}",
                    severity="WARNING",
                    workflow_id=workflow_id,
                    transaction_id=transaction_id
                )
            elif action == "WORKFLOW_STOPPED_BY_POLICY" or action == "WORKFLOW_STOPPED":
                reason = details_dict.get("reason", "Stopping rule enforced.")
                await broadcaster.broadcast(
                    event_type="RETRY_STOPPED",
                    title="Recovery Stopped",
                    message=f"Workflow halted by guardrail: {reason}",
                    severity="ERROR",
                    workflow_id=workflow_id,
                    transaction_id=transaction_id
                )
            elif action == "AI_DIAGNOSIS_AND_PLAN_CREATED":
                rec = details_dict.get("recommended_action", "Action")
                conf = details_dict.get("confidence", 0.0)
                await broadcaster.broadcast(
                    event_type="AI_DIAGNOSIS_COMPLETED",
                    title="AI Diagnosis Completed",
                    message=f"Diagnosed root cause. Recommended: {rec} ({int(conf * 100)}% confidence).",
                    severity="INFO",
                    workflow_id=workflow_id,
                    transaction_id=transaction_id
                )
            elif action == "POLICY_APPROVED":
                await broadcaster.broadcast(
                    event_type="RECOVERY_AUTHORIZED",
                    title="Recovery Authorized",
                    message="Deterministic Policy Gate approved automated recovery execution.",
                    severity="SUCCESS",
                    workflow_id=workflow_id,
                    transaction_id=transaction_id
                )
            elif action == "DUPLICATE_WEBHOOK_IGNORED":
                await broadcaster.broadcast(
                    event_type="DUPLICATE_WEBHOOK_DETECTED",
                    title="Duplicate Webhook Detected",
                    message="Replayed webhook event dropped safely via SHA-256 hash deduplication.",
                    severity="INFO",
                    workflow_id=workflow_id,
                    transaction_id=transaction_id
                )
        except Exception:
            pass  # Notifications should never break audit logging

        return audit_entry
