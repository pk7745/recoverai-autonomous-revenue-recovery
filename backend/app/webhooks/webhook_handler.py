import uuid
from typing import Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.webhook_event import WebhookEvent
from app.models.transaction import Transaction
from app.models.merchant import Merchant
from app.core.security import verify_razorpay_signature, compute_payload_hash
from app.core.config import settings
from app.core.enums import ActorType, PaymentStatus
from app.audit.audit_service import AuditService
from app.recovery.orchestrator import RecoveryOrchestrator

class WebhookHandler:
    @staticmethod
    async def process_webhook(
        db: AsyncSession,
        raw_body: bytes,
        signature: str,
        payload_data: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        # 1. Strict Cryptographic Signature Verification
        secret = settings.RAZORPAY_WEBHOOK_SECRET
        if not signature or not verify_razorpay_signature(raw_body, signature, secret):
            await AuditService.log_event(
                db=db,
                actor=ActorType.RAZORPAY_WEBHOOK,
                action="INVALID_WEBHOOK_SIGNATURE_REJECTED",
                details={"event": payload_data.get("event", "unknown")}
            )
            await db.flush()
            return False, "Invalid or missing HMAC webhook signature", {
                "error": "INVALID_SIGNATURE",
                "is_duplicate": False
            }

        event_id = payload_data.get("event_id") or payload_data.get("id") or f"evt_{uuid.uuid4().hex[:12]}"
        event_type = payload_data.get("event", "unknown")
        payload_hash = compute_payload_hash(payload_data)

        # 2. Idempotency & Duplicate Check
        existing_event_stmt = select(WebhookEvent).where(WebhookEvent.razorpay_event_id == event_id)
        res = await db.execute(existing_event_stmt)
        existing_event = res.scalar_one_or_none()

        if existing_event:
            # Mark duplicate and stop processing immediately
            existing_event.is_duplicate = True
            await AuditService.log_event(
                db=db,
                actor=ActorType.RAZORPAY_WEBHOOK,
                action="DUPLICATE_WEBHOOK_IGNORED",
                details={"event_id": event_id, "event_type": event_type}
            )
            await db.flush()
            return True, "Duplicate webhook detected. Ignored idempotently.", {
                "event_id": event_id,
                "is_duplicate": True,
                "event_type": event_type
            }

        # 3. Persist raw event
        event_record = WebhookEvent(
            id=f"whe_{uuid.uuid4().hex[:14]}",
            razorpay_event_id=event_id,
            event_type=event_type,
            payload_hash=payload_hash,
            payload=payload_data,
            signature=signature,
            is_duplicate=False,
            processed=True
        )
        db.add(event_record)
        await db.flush()

        # 4. Route event based on type
        orchestrator = RecoveryOrchestrator()
        entity_payload = payload_data.get("payload", {}).get("payment", {}).get("entity", {})
        payment_id = entity_payload.get("id")
        amount = float(entity_payload.get("amount", 0)) / 100.0 if entity_payload.get("amount") else 0.0

        if event_type in ["payment.captured", "payment.authorized", "order.paid"]:
            # Check if this maps to a transaction
            txn_stmt = select(Transaction).where(Transaction.razorpay_payment_id == payment_id)
            txn_res = await db.execute(txn_stmt)
            txn = txn_res.scalar_one_or_none()
            if txn:
                await orchestrator.settle_recovery_success(db, txn.id, amount or txn.amount)

        await AuditService.log_event(
            db=db,
            actor=ActorType.RAZORPAY_WEBHOOK,
            action="WEBHOOK_PROCESSED_SUCCESSFULLY",
            details={"event_id": event_id, "event_type": event_type, "payment_id": payment_id}
        )
        await db.flush()
        return True, "Webhook processed successfully", {
            "event_id": event_id,
            "is_duplicate": False,
            "event_type": event_type
        }
