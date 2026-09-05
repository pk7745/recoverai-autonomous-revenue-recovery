from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.models.recovery_workflow import RecoveryWorkflow
from app.models.checkout_session import CheckoutSession
from app.models.subscription import Subscription
from app.models.receivable_invoice import ReceivableInvoice
from app.models.mandate import Mandate
from app.models.promise_to_pay import PromiseToPay
from app.models.voice_session import VoiceRecoverySession
from app.models.customer import Customer
from app.recovery.orchestrator import RecoveryOrchestrator
from app.schemas.recovery import RecoveryWorkflowResponse

router = APIRouter(prefix="/programs", tags=["Recovery Programs"])
orchestrator = RecoveryOrchestrator()


# ==========================================
# 0. Programs Overview
# ==========================================
@router.get("/overview")
async def get_programs_overview(db: AsyncSession = Depends(get_db)):
    """Aggregate KPI overview across all 7 recovery programs."""
    chk_count = (await db.execute(select(func.count(CheckoutSession.id)))).scalar_one_or_none() or 0
    sub_count = (await db.execute(select(func.count(Subscription.id)))).scalar_one_or_none() or 0
    rec_count = (await db.execute(select(func.count(ReceivableInvoice.id)))).scalar_one_or_none() or 0
    man_count = (await db.execute(select(func.count(Mandate.id)))).scalar_one_or_none() or 0
    ptp_count = (await db.execute(select(func.count(PromiseToPay.id)))).scalar_one_or_none() or 0
    voc_count = (await db.execute(select(func.count(VoiceRecoverySession.id)))).scalar_one_or_none() or 0

    workflows = (await db.execute(select(RecoveryWorkflow))).scalars().all()
    recovered_by_type: Dict[str, float] = {}
    active_by_type: Dict[str, int] = {}
    
    for wf in workflows:
        ptype = wf.recovery_type or "PAYMENT"
        recovered_by_type[ptype] = recovered_by_type.get(ptype, 0.0) + (wf.recovered_amount or 0.0)
        if wf.state not in ["RECOVERED", "FAILED", "STOPPED"]:
            active_by_type[ptype] = active_by_type.get(ptype, 0) + 1

    return {
        "programs": {
            "payment": {
                "name": "Payment Degradation Engine",
                "total_records": len([w for w in workflows if (w.recovery_type or "PAYMENT") == "PAYMENT"]),
                "active_workflows": active_by_type.get("PAYMENT", 0),
                "recovered_amount": round(recovered_by_type.get("PAYMENT", 0.0), 2),
                "status": "ACTIVE"
            },
            "checkout": {
                "name": "Checkout Drop-off Recovery",
                "total_records": chk_count,
                "active_workflows": active_by_type.get("CHECKOUT", 0),
                "recovered_amount": round(recovered_by_type.get("CHECKOUT", 0.0), 2),
                "status": "ACTIVE"
            },
            "subscription": {
                "name": "Subscription Smart Dunning",
                "total_records": sub_count,
                "active_workflows": active_by_type.get("SUBSCRIPTION", 0),
                "recovered_amount": round(recovered_by_type.get("SUBSCRIPTION", 0.0), 2),
                "status": "ACTIVE"
            },
            "receivables": {
                "name": "B2B Receivables Chaser",
                "total_records": rec_count,
                "active_workflows": active_by_type.get("RECEIVABLE", 0),
                "recovered_amount": round(recovered_by_type.get("RECEIVABLE", 0.0), 2),
                "status": "ACTIVE"
            },
            "mandates": {
                "name": "Mandate Retry Sequencer",
                "total_records": man_count,
                "active_workflows": active_by_type.get("MANDATE", 0),
                "recovered_amount": round(recovered_by_type.get("MANDATE", 0.0), 2),
                "status": "ACTIVE"
            },
            "voice": {
                "name": "Hinglish Voice Recovery",
                "total_records": voc_count,
                "active_workflows": active_by_type.get("VOICE_RECOVERY", 0),
                "recovered_amount": round(recovered_by_type.get("VOICE_RECOVERY", 0.0), 2),
                "status": "ACTIVE"
            },
            "promises": {
                "name": "Promise-to-Pay Tracker",
                "total_records": ptp_count,
                "active_workflows": active_by_type.get("PROMISE_TO_PAY", 0),
                "recovered_amount": round(recovered_by_type.get("PROMISE_TO_PAY", 0.0), 2),
                "status": "ACTIVE"
            }
        },
        "total_active_pipelines": sum(active_by_type.values()),
        "total_recovered_inr": round(sum(recovered_by_type.values()), 2)
    }


# ==========================================
# 1. Checkout Drop-off Recovery
# ==========================================
@router.get("/checkout")
async def list_checkout_sessions(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(CheckoutSession)
        .options(selectinload(CheckoutSession.customer))
        .order_by(CheckoutSession.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    sessions = res.scalars().all()
    
    result = []
    for s in sessions:
        wf = (await db.execute(
            select(RecoveryWorkflow)
            .where(RecoveryWorkflow.reference_id == s.id)
            .order_by(RecoveryWorkflow.created_at.desc())
        )).scalars().first()
        result.append({
            "id": s.id,
            "customer_id": s.customer_id,
            "customer_name": s.customer.name if s.customer else "Unknown",
            "customer_email": s.customer.email if s.customer else "Unknown",
            "cart_value": s.cart_value,
            "currency": s.currency,
            "items_count": s.items_count,
            "exit_step": s.exit_step,
            "detected_friction": s.detected_friction,
            "recovery_status": s.recovery_status,
            "recovery_link_url": s.recovery_link_url,
            "created_at": s.created_at,
            "workflow": {
                "id": wf.id,
                "state": wf.state,
                "recommended_action": wf.recommended_action,
                "execution_mode": wf.execution_mode,
                "ai_confidence": wf.ai_confidence,
                "ai_reasoning": wf.ai_reasoning,
                "policy_evaluation": wf.policy_evaluation,
                "execution_payload": wf.execution_payload
            } if wf else None
        })
    return result

@router.post("/checkout/{session_id}/plan")
async def plan_checkout_recovery(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.plan_checkout_recovery(db, session_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "recommended_action": wf.recommended_action, "ai_reasoning": wf.ai_reasoning}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/checkout/{session_id}/execute")
async def execute_checkout_recovery(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.execute_checkout_recovery(db, session_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "execution_mode": wf.execution_mode, "execution_payload": wf.execution_payload, "recovered_amount": wf.recovered_amount}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 2. Failed-Subscription Recovery
# ==========================================
@router.get("/subscriptions")
async def list_subscriptions(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Subscription)
        .options(selectinload(Subscription.customer))
        .order_by(Subscription.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    subs = res.scalars().all()
    
    result = []
    for s in subs:
        wf = (await db.execute(
            select(RecoveryWorkflow)
            .where(RecoveryWorkflow.reference_id == s.id)
            .order_by(RecoveryWorkflow.created_at.desc())
        )).scalars().first()
        result.append({
            "id": s.id,
            "customer_id": s.customer_id,
            "customer_name": s.customer.name if s.customer else "Unknown",
            "customer_email": s.customer.email if s.customer else "Unknown",
            "plan_name": s.plan_name,
            "recurring_amount": s.recurring_amount,
            "currency": s.currency,
            "billing_interval": s.billing_interval,
            "status": s.status,
            "failed_attempts": s.failed_attempts,
            "max_retries": s.max_retries,
            "last_failure_reason": s.last_failure_reason,
            "next_retry_at": s.next_retry_at,
            "created_at": s.created_at,
            "workflow": {
                "id": wf.id,
                "state": wf.state,
                "recommended_action": wf.recommended_action,
                "execution_mode": wf.execution_mode,
                "ai_confidence": wf.ai_confidence,
                "ai_reasoning": wf.ai_reasoning,
                "policy_evaluation": wf.policy_evaluation,
                "execution_payload": wf.execution_payload
            } if wf else None
        })
    return result

@router.post("/subscriptions/{subscription_id}/plan")
async def plan_subscription_recovery(subscription_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.plan_subscription_recovery(db, subscription_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "recommended_action": wf.recommended_action, "ai_reasoning": wf.ai_reasoning}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/subscriptions/{subscription_id}/execute")
async def execute_subscription_recovery(subscription_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.execute_subscription_recovery(db, subscription_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "execution_mode": wf.execution_mode, "execution_payload": wf.execution_payload, "recovered_amount": wf.recovered_amount}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 3. B2B Receivables Chaser
# ==========================================
@router.get("/receivables")
async def list_receivable_invoices(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(ReceivableInvoice)
        .options(selectinload(ReceivableInvoice.customer))
        .order_by(ReceivableInvoice.overdue_days.desc(), ReceivableInvoice.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    invoices = res.scalars().all()
    
    result = []
    for inv in invoices:
        wf = (await db.execute(
            select(RecoveryWorkflow)
            .where(RecoveryWorkflow.reference_id == inv.id)
            .order_by(RecoveryWorkflow.created_at.desc())
        )).scalars().first()
        result.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "customer_id": inv.customer_id,
            "customer_name": inv.customer.name if inv.customer else "B2B Client",
            "customer_email": inv.customer.email if inv.customer else "accounts@client.com",
            "invoice_amount": inv.invoice_amount,
            "currency": inv.currency,
            "issue_date": inv.issue_date,
            "due_date": inv.due_date,
            "overdue_days": inv.overdue_days,
            "chasing_stage": inv.chasing_stage,
            "status": inv.status,
            "last_contact_at": inv.last_contact_at,
            "contact_count": inv.contact_count,
            "created_at": inv.created_at,
            "workflow": {
                "id": wf.id,
                "state": wf.state,
                "recommended_action": wf.recommended_action,
                "execution_mode": wf.execution_mode,
                "ai_confidence": wf.ai_confidence,
                "ai_reasoning": wf.ai_reasoning,
                "policy_evaluation": wf.policy_evaluation,
                "execution_payload": wf.execution_payload
            } if wf else None
        })
    return result

@router.post("/receivables/{invoice_id}/plan")
async def plan_receivable_chasing(invoice_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.plan_receivable_chasing(db, invoice_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "recommended_action": wf.recommended_action, "ai_reasoning": wf.ai_reasoning}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/receivables/{invoice_id}/execute")
async def execute_receivable_chasing(invoice_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.execute_receivable_chasing(db, invoice_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "execution_mode": wf.execution_mode, "execution_payload": wf.execution_payload, "recovered_amount": wf.recovered_amount}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 4. Mandate Retry Sequencer
# ==========================================
@router.get("/mandates")
async def list_mandates(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Mandate)
        .options(selectinload(Mandate.customer))
        .order_by(Mandate.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    mandates = res.scalars().all()
    
    result = []
    for m in mandates:
        wf = (await db.execute(
            select(RecoveryWorkflow)
            .where(RecoveryWorkflow.reference_id == m.id)
            .order_by(RecoveryWorkflow.created_at.desc())
        )).scalars().first()
        result.append({
            "id": m.id,
            "customer_id": m.customer_id,
            "customer_name": m.customer.name if m.customer else "Unknown",
            "mandate_token": m.mandate_token,
            "mandate_type": m.mandate_type,
            "max_amount": m.max_amount,
            "scheduled_amount": m.scheduled_amount,
            "currency": m.currency,
            "frequency": m.frequency,
            "status": m.status,
            "attempt_number": m.attempt_number,
            "max_attempts": m.max_attempts,
            "failure_code": m.failure_code,
            "next_attempt_at": m.next_attempt_at,
            "created_at": m.created_at,
            "workflow": {
                "id": wf.id,
                "state": wf.state,
                "recommended_action": wf.recommended_action,
                "execution_mode": wf.execution_mode,
                "ai_confidence": wf.ai_confidence,
                "ai_reasoning": wf.ai_reasoning,
                "policy_evaluation": wf.policy_evaluation,
                "execution_payload": wf.execution_payload
            } if wf else None
        })
    return result

@router.post("/mandates/{mandate_id}/plan")
async def plan_mandate_sequence(mandate_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.plan_mandate_sequence(db, mandate_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "recommended_action": wf.recommended_action, "ai_reasoning": wf.ai_reasoning}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mandates/{mandate_id}/execute")
async def execute_mandate_sequence(mandate_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.execute_mandate_sequence(db, mandate_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "execution_mode": wf.execution_mode, "execution_payload": wf.execution_payload, "recovered_amount": wf.recovered_amount}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 5. Hinglish Voice Recovery
# ==========================================
@router.get("/voice")
async def list_voice_sessions(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(VoiceRecoverySession)
        .options(selectinload(VoiceRecoverySession.customer))
        .order_by(VoiceRecoverySession.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    sessions = res.scalars().all()
    
    result = []
    for v in sessions:
        wf = (await db.execute(
            select(RecoveryWorkflow)
            .where(RecoveryWorkflow.reference_id == v.id)
            .order_by(RecoveryWorkflow.created_at.desc())
        )).scalars().first()
        result.append({
            "id": v.id,
            "customer_id": v.customer_id,
            "customer_name": v.customer.name if v.customer else "Customer",
            "phone_number": v.phone_number,
            "language": v.language,
            "generated_script": v.generated_script,
            "audio_simulation_state": v.audio_simulation_state,
            "call_status": v.call_status,
            "detected_intent": v.detected_intent,
            "payment_link_sent": v.payment_link_sent,
            "duration_seconds": v.duration_seconds,
            "execution_mode": v.execution_mode,
            "created_at": v.created_at,
            "workflow": {
                "id": wf.id,
                "state": wf.state,
                "recommended_action": wf.recommended_action,
                "execution_mode": wf.execution_mode,
                "ai_confidence": wf.ai_confidence,
                "ai_reasoning": wf.ai_reasoning,
                "policy_evaluation": wf.policy_evaluation,
                "execution_payload": wf.execution_payload
            } if wf else None
        })
    return result

@router.post("/voice/{session_id}/plan")
async def plan_voice_recovery(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.plan_voice_recovery(db, session_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "recommended_action": wf.recommended_action, "ai_reasoning": wf.ai_reasoning}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/voice/{session_id}/execute")
async def execute_voice_recovery(session_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.execute_voice_recovery(db, session_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "execution_mode": wf.execution_mode, "execution_payload": wf.execution_payload, "recovered_amount": wf.recovered_amount}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 6. Promise-to-Pay Tracker
# ==========================================
@router.get("/promises")
async def list_promises_to_pay(
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(PromiseToPay)
        .options(selectinload(PromiseToPay.customer))
        .order_by(PromiseToPay.promised_date.asc(), PromiseToPay.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    res = await db.execute(stmt)
    promises = res.scalars().all()
    
    result = []
    for p in promises:
        wf = (await db.execute(
            select(RecoveryWorkflow)
            .where(RecoveryWorkflow.reference_id == p.id)
            .order_by(RecoveryWorkflow.created_at.desc())
        )).scalars().first()
        result.append({
            "id": p.id,
            "customer_id": p.customer_id,
            "customer_name": p.customer.name if p.customer else "Debtor",
            "reference_type": p.reference_type,
            "reference_id": p.reference_id,
            "promised_amount": p.promised_amount,
            "currency": p.currency,
            "promised_date": p.promised_date,
            "grace_period_hours": p.grace_period_hours,
            "status": p.status,
            "reminder_sent_count": p.reminder_sent_count,
            "notes": p.notes,
            "fulfilled_at": p.fulfilled_at,
            "breached_at": p.breached_at,
            "created_at": p.created_at,
            "workflow": {
                "id": wf.id,
                "state": wf.state,
                "recommended_action": wf.recommended_action,
                "execution_mode": wf.execution_mode,
                "ai_confidence": wf.ai_confidence,
                "ai_reasoning": wf.ai_reasoning,
                "policy_evaluation": wf.policy_evaluation,
                "execution_payload": wf.execution_payload
            } if wf else None
        })
    return result

@router.post("/promises/{ptp_id}/plan")
async def plan_promise_to_pay(ptp_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.plan_promise_to_pay(db, ptp_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "recommended_action": wf.recommended_action, "ai_reasoning": wf.ai_reasoning}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/promises/{ptp_id}/fulfill")
async def fulfill_promise_to_pay(ptp_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.fulfill_promise_to_pay(db, ptp_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "recovered_amount": wf.recovered_amount}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/promises/{ptp_id}/breach")
async def breach_promise_to_pay(ptp_id: str, db: AsyncSession = Depends(get_db)):
    try:
        _, wf = await orchestrator.breach_promise_to_pay(db, ptp_id)
        await db.commit()
        return {"workflow_id": wf.id, "state": wf.state, "escalation_reason": wf.escalation_reason}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
