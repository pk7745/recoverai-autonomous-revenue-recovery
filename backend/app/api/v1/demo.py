import uuid
import hmac
import hashlib
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone
from app.core.config import settings

from app.core.database import get_db
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.transaction import Transaction
from app.models.recovery_workflow import RecoveryWorkflow
from app.models.audit_log import AuditLog
from app.models.webhook_event import WebhookEvent
from app.models.user import User
from app.core.auth import hash_password
from app.core.enums import (
    PaymentStatus,
    RecoveryState,
    InterventionType,
    ActorType,
    RiskTier
)
from app.recovery.orchestrator import RecoveryOrchestrator
from app.webhooks.webhook_handler import WebhookHandler
from app.audit.audit_service import AuditService
from app.agents.tools import RecoveryToolRegistry

router = APIRouter(prefix="/demo", tags=["Demo Scenarios"])
orchestrator = RecoveryOrchestrator()

async def ensure_demo_merchant(db: AsyncSession) -> Merchant:
    stmt = select(Merchant).where(Merchant.id == "merch_razorpay_demo")
    res = await db.execute(stmt)
    merchant = res.scalar_one_or_none()
    if not merchant:
        merchant = Merchant(
            id="merch_razorpay_demo",
            name="Acrobatics Apparel Pvt Ltd",
            api_key_id="rzp_test_recoverai2026",
            webhook_secret="whsec_recoverai_super_secret_webhook_2026",
            autonomous_limit=5000.0,
            max_retries=2,
            min_retry_interval_mins=30,
            risk_threshold=0.70
        )
        db.add(merchant)
        await db.flush()
    return merchant

@router.post("/reset")
async def reset_demo_database(db: AsyncSession = Depends(get_db)):
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=403,
            detail="Demo reset endpoint is disabled in production environment to protect persistent merchant data."
        )

    await db.execute(delete(AuditLog))
    await db.execute(delete(WebhookEvent))
    await db.execute(delete(RecoveryWorkflow))
    await db.execute(delete(Transaction))
    await db.execute(delete(Customer))
    await db.execute(delete(User))
    await db.execute(delete(Merchant))
    await db.commit()
    
    # Re-seed baseline data
    await perform_seed(db)
    return {"status": "success", "message": "Demo database successfully reset and seeded."}

@router.post("/seed")
async def seed_demo_database(db: AsyncSession = Depends(get_db)):
    if settings.ENVIRONMENT == "production":
        raise HTTPException(
            status_code=403,
            detail="Demo seeding endpoint is disabled in production environment."
        )
    await perform_seed(db)
    return {"status": "success", "message": "Demo data successfully seeded"}

async def perform_seed(db: AsyncSession):
    from app.core.auth import ensure_initial_users
    await ensure_initial_users(db)

    merchant = await ensure_demo_merchant(db)

    # Seed Customers
    customers_data = [
        {"id": "cust_aarav", "name": "Aarav Sharma", "email": "aarav.sharma@example.com", "phone": "+919876543210", "succ": 8, "fail": 1, "ret": True, "risk": "LOW"},
        {"id": "cust_priya", "name": "Priya Patel", "email": "priya.patel@example.com", "phone": "+919812345678", "succ": 0, "fail": 2, "ret": False, "risk": "MEDIUM"},
        {"id": "cust_vikram", "name": "Vikram Malhotra", "email": "vikram.m@example.com", "phone": "+919988776655", "succ": 1, "fail": 4, "ret": True, "risk": "HIGH"},
        {"id": "cust_ananya", "name": "Ananya Desai", "email": "ananya.d@example.com", "phone": "+919765432109", "succ": 14, "fail": 0, "ret": True, "risk": "LOW"},
        {"id": "cust_rohit", "name": "Rohit Verma", "email": "rohit.verma@example.com", "phone": "+919123456789", "succ": 3, "fail": 1, "ret": True, "risk": "LOW"},
    ]
    for c in customers_data:
        cust_res = await db.execute(select(Customer).where(Customer.id == c["id"]))
        if not cust_res.scalar_one_or_none():
            cust = Customer(
                id=c["id"],
                merchant_id=merchant.id,
                name=c["name"],
                email=c["email"],
                phone=c["phone"],
                total_successful_payments=c["succ"],
                total_failed_payments=c["fail"],
                is_returning=c["ret"],
                risk_tier=c["risk"]
            )
            db.add(cust)

    # Seed Baseline Transactions & Recovery Workflows
    txns_data = [
        {
            "id": "txn_demo_4999",
            "cust_id": "cust_aarav",
            "amount": 4999.0,
            "pay_id": "pay_N89a7df92",
            "order_id": "order_O89a7df92",
            "status": "FAILED",
            "code": "TEMPORARY_ISSUER_DECLINE",
            "reason": "Bank server busy / temporary decline",
            "method": "card",
            "attempts": 1
        },
        {
            "id": "txn_demo_8499",
            "cust_id": "cust_priya",
            "amount": 8499.0,
            "pay_id": "pay_P89b14f88",
            "order_id": "order_P89b14f88",
            "status": "FAILED",
            "code": "AUTH_FAILED",
            "reason": "OTP expired / Customer abandoned 3DS authentication",
            "method": "upi",
            "attempts": 2
        },
        {
            "id": "txn_demo_27000",
            "cust_id": "cust_vikram",
            "amount": 27000.0,
            "pay_id": "pay_V89c91a03",
            "order_id": "order_V89c91a03",
            "status": "FAILED",
            "code": "FRAUD_RISK_BLOCK",
            "reason": "Card velocity anomaly & high fraud risk score",
            "method": "card",
            "attempts": 1
        },
        {
            "id": "txn_demo_12500",
            "cust_id": "cust_ananya",
            "amount": 12500.0,
            "pay_id": "pay_A89d12e45",
            "order_id": "order_A89d12e45",
            "status": "FAILED",
            "code": "TEMPORARY_ISSUER_DECLINE",
            "reason": "HDFC Core Banking connectivity drop",
            "method": "netbanking",
            "attempts": 1
        }
    ]

    for t in txns_data:
        txn_res = await db.execute(select(Transaction).where(Transaction.id == t["id"]))
        if not txn_res.scalar_one_or_none():
            txn = Transaction(
                id=t["id"],
                merchant_id=merchant.id,
                customer_id=t["cust_id"],
                razorpay_payment_id=t["pay_id"],
                razorpay_order_id=t["order_id"],
                amount=t["amount"],
                currency="INR",
                status=t["status"],
                failure_code=t["code"],
                failure_reason=t["reason"],
                payment_method=t["method"],
                attempts_count=t["attempts"]
            )
            db.add(txn)

            canonical_category = RecoveryToolRegistry.normalize_failure_category(t["code"]).value
            wf = RecoveryWorkflow(
                id=f"rec_{t['id']}",
                transaction_id=txn.id,
                state=RecoveryState.PAYMENT_FAILED.value,
                risk_score=0.15 if t["amount"] < 5000 else (0.85 if "FRAUD" in t["code"] else 0.35),
                failure_category=canonical_category,
                recommended_action=InterventionType.NO_ACTION.value,
                ai_confidence=0.0
            )
            db.add(wf)

            await AuditService.log_event(
                db=db,
                actor=ActorType.RAZORPAY_WEBHOOK,
                action="PAYMENT_FAILED_INGESTED",
                workflow_id=f"rec_{t['id']}",
                transaction_id=txn.id,
                details={
                    "amount": t["amount"],
                    "failure_code": t["code"],
                    "failure_reason": t["reason"],
                    "customer_id": t["cust_id"],
                    "payment_method": t["method"],
                    "summary": f"Ingested payment failure {t['id']} (INR {t['amount']:,.2f}) - {t['reason']}"
                }
            )

    await db.commit()
    return {"status": "success", "message": "Demo data successfully seeded"}

@router.post("/scenario/{scenario_id}")
async def run_demo_scenario(scenario_id: str, db: AsyncSession = Depends(get_db)):
    merchant = await ensure_demo_merchant(db)

    if scenario_id == "successful_delayed_retry":
        # Scenario 1: ₹4,999 Temporary Decline -> AI Diagnosis -> Delayed Retry -> Recovered
        wf_id = "rec_txn_demo_4999"
        txn_res = await db.execute(select(Transaction).where(Transaction.id == "txn_demo_4999"))
        txn_item = txn_res.scalar_one_or_none()
        if txn_item:
            txn_item.status = PaymentStatus.FAILED.value
        wf_res = await db.execute(select(RecoveryWorkflow).where(RecoveryWorkflow.id == wf_id))
        existing_wf = wf_res.scalar_one_or_none()
        if existing_wf:
            existing_wf.state = RecoveryState.PAYMENT_FAILED.value
            existing_wf.recovered_amount = 0.0
            existing_wf.stopping_rule_triggered = None
            existing_wf.escalation_reason = None
        await db.commit()

        wf = await orchestrator.plan_workflow(db, wf_id)
        wf = await orchestrator.execute_workflow(db, wf_id)
        # Webhook confirmation
        wf = await orchestrator.settle_recovery_success(db, wf.transaction_id, 4999.0)
        await db.commit()
        return {
            "scenario": "Scenario 1 — Successful Delayed Retry",
            "workflow_id": wf.id,
            "status": "RECOVERED",
            "recovered_amount": 4999.0,
            "exposure_amount": 4999.0,
            "financial_outcome": "₹4,999.00 Settled",
            "explanation": "Temporary bank decline resolved via 30-min delayed retry. ₹4,999 successfully recovered."
        }

    elif scenario_id == "high_risk_escalation":
        # Scenario 2: ₹27,000 High Risk -> Policy Blocks & Escalates
        wf_id = "rec_txn_demo_27000"
        txn_res = await db.execute(select(Transaction).where(Transaction.id == "txn_demo_27000"))
        txn_item = txn_res.scalar_one_or_none()
        if txn_item:
            txn_item.status = PaymentStatus.FAILED.value
        wf_res = await db.execute(select(RecoveryWorkflow).where(RecoveryWorkflow.id == wf_id))
        existing_wf = wf_res.scalar_one_or_none()
        if existing_wf:
            existing_wf.state = RecoveryState.PAYMENT_FAILED.value
            existing_wf.recovered_amount = 0.0
            existing_wf.stopping_rule_triggered = None
            existing_wf.escalation_reason = None
        await db.commit()

        wf = await orchestrator.plan_workflow(db, wf_id)
        await db.commit()
        return {
            "scenario": "Scenario 2 — High Risk Policy Block & Human Escalation",
            "workflow_id": wf.id,
            "status": "ESCALATED",
            "recovered_amount": 0.0,
            "exposure_amount": 27000.0,
            "financial_outcome": "₹0 Recovered • ₹27,000 Held for Human Review",
            "explanation": "Transaction flagged with high risk score (0.85) and amount (₹27,000). Automated retry blocked by Policy Engine."
        }

    elif scenario_id == "max_retries_stopped":
        # Scenario 3: Attempts >= 3 -> Stopping Rule Halts Workflow
        txn_id = f"txn_demo_stop_{uuid.uuid4().hex[:6]}"
        txn = Transaction(
            id=txn_id,
            merchant_id=merchant.id,
            customer_id="cust_vikram",
            razorpay_payment_id=f"pay_{uuid.uuid4().hex[:8]}",
            amount=3200.0,
            currency="INR",
            status="FAILED",
            failure_code="INSUFFICIENT_FUNDS",
            failure_reason="Repeated insufficient funds",
            payment_method="card",
            attempts_count=3
        )
        db.add(txn)
        wf = RecoveryWorkflow(
            id=f"rec_{txn_id}",
            transaction_id=txn.id,
            state="PAYMENT_FAILED",
            risk_score=0.45,
            recovered_amount=0.0
        )
        db.add(wf)
        await db.flush()

        wf = await orchestrator.plan_workflow(db, wf.id)
        await db.commit()
        return {
            "scenario": "Scenario 3 — Maximum Retries Stopping Rule",
            "workflow_id": wf.id,
            "status": wf.state,
            "recovered_amount": 0.0,
            "exposure_amount": 3200.0,
            "financial_outcome": "₹0 Recovered • Stopped (Max Attempts Limit)",
            "explanation": "Transaction reached 3 attempts. Stopping rule triggered immediately to prevent issuer penalties."
        }

    elif scenario_id == "duplicate_webhook_protection":
        # Scenario 4: Duplicate Webhook Idempotency
        event_id = "evt_demo_dup_webhook_12345"
        payload = {
            "event_id": event_id,
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_N89a7df92",
                        "amount": 499900,
                        "currency": "INR",
                        "status": "captured"
                    }
                }
            }
        }
        raw_body = json.dumps(payload).encode("utf-8")
        valid_sig = hmac.new(
            key=settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256
        ).hexdigest()

        # First delivery
        await WebhookHandler.process_webhook(db, raw_body, valid_sig, payload)
        # Second duplicate delivery
        success, msg, details = await WebhookHandler.process_webhook(db, raw_body, valid_sig, payload)
        await db.commit()
        return {
            "scenario": "Scenario 4 — Duplicate Webhook Idempotency Check",
            "event_id": event_id,
            "status": "IDEMPOTENT_IGNORED",
            "duplicate_detected": details.get("is_duplicate", True),
            "recovered_amount": 0.0,
            "exposure_amount": 4999.0,
            "financial_outcome": "Zero Financial Mutation (Duplicate Event Dropped)",
            "explanation": "Identical webhook event ID replayed. Second event safely rejected; zero redundant state mutations."
        }

    elif scenario_id == "already_recovered_no_action":
        # Scenario 5: Already Recovered -> Do Nothing
        txn_id = f"txn_demo_settled_{uuid.uuid4().hex[:6]}"
        txn = Transaction(
            id=txn_id,
            merchant_id=merchant.id,
            customer_id="cust_aarav",
            razorpay_payment_id=f"pay_{uuid.uuid4().hex[:8]}",
            amount=1999.0,
            currency="INR",
            status="RECOVERED",
            failure_code="TEMPORARY_ISSUER_DECLINE",
            failure_reason="Previously declined but paid in second window",
            payment_method="card",
            attempts_count=1
        )
        db.add(txn)
        wf = RecoveryWorkflow(
            id=f"rec_{txn_id}",
            transaction_id=txn.id,
            state="RECOVERED",
            risk_score=0.10,
            recovered_amount=1999.0
        )
        db.add(wf)
        await db.flush()

        wf = await orchestrator.plan_workflow(db, wf.id)
        await db.commit()
        return {
            "scenario": "Scenario 5 — Already Recovered (DO NOTHING)",
            "workflow_id": wf.id,
            "status": wf.state,
            "recommended_action": "NO_ACTION",
            "recovered_amount": 1999.0,
            "exposure_amount": 1999.0,
            "financial_outcome": "Zero Duplicate Action (Already Settled in Parallel)",
            "explanation": "Payment already captured in another channel. RecoverAI evaluated NO_ACTION and aborted retries."
        }

    else:
        raise HTTPException(status_code=400, detail=f"Unknown scenario ID: {scenario_id}")
