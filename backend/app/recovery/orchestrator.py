import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.recovery_workflow import RecoveryWorkflow
from app.models.transaction import Transaction
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.models.checkout_session import CheckoutSession
from app.models.subscription import Subscription
from app.models.receivable_invoice import ReceivableInvoice
from app.models.mandate import Mandate
from app.models.promise_to_pay import PromiseToPay
from app.models.voice_session import VoiceRecoverySession
from app.core.enums import (
    RecoveryState,
    PaymentStatus,
    InterventionType,
    PolicyResultStatus,
    ActorType,
    RecoveryType,
    ExecutionMode,
    FailureCategory
)
from app.agents.recovery_agent import RecoveryAgent
from app.policies.policy_engine import PolicyEngine
from app.payments.razorpay_client import RazorpayClientService
from app.recovery.state_machine import RecoveryStateMachine
from app.audit.audit_service import AuditService

class RecoveryOrchestrator:
    def __init__(self):
        self.agent = RecoveryAgent()
        self.razorpay_service = RazorpayClientService()

    async def plan_workflow(self, db: AsyncSession, workflow_id: str) -> RecoveryWorkflow:
        stmt = (
            select(RecoveryWorkflow)
            .where(RecoveryWorkflow.id == workflow_id)
            .options(
                selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.customer),
                selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.merchant)
            )
        )
        res = await db.execute(stmt)
        workflow = res.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        txn: Transaction = workflow.transaction
        cust: Customer = txn.customer
        merch: Merchant = txn.merchant

        # If already settled, do not re-plan or mutate state
        if workflow.state == RecoveryState.RECOVERED.value or txn.status == PaymentStatus.RECOVERED.value:
            return workflow

        # 1. State transition to RECOVERY_ELIGIBLE if needed
        if workflow.state == RecoveryState.PAYMENT_FAILED.value:
            RecoveryStateMachine.validate_transition(RecoveryState.PAYMENT_FAILED, RecoveryState.RECOVERY_ELIGIBLE)
            workflow.state = RecoveryState.RECOVERY_ELIGIBLE.value
            await AuditService.log_event(
                db=db,
                actor=ActorType.SYSTEM_AGENT,
                action="RECOVERY_ELIGIBILITY_CONFIRMED",
                transaction_id=txn.id,
                workflow_id=workflow.id,
                details={"amount": txn.amount, "failure_code": txn.failure_code}
            )

        # 2. AI Reasoning and Plan Generation
        reasoning = await self.agent.plan_recovery(
            transaction_amount=txn.amount,
            failure_code=txn.failure_code or "TEMPORARY_ISSUER_DECLINE",
            failure_reason=txn.failure_reason or "Temporary decline",
            payment_method=txn.payment_method or "card",
            attempts_count=txn.attempts_count,
            customer_name=cust.name or "Valued Customer",
            customer_successful_payments=cust.total_successful_payments,
            customer_failed_payments=cust.total_failed_payments,
            is_returning=cust.is_returning
        )

        workflow.ai_confidence = reasoning.confidence
        workflow.failure_category = reasoning.root_cause_diagnosis
        workflow.recommended_action = reasoning.recommended_intervention.value
        workflow.ai_reasoning = reasoning.model_dump()
        workflow.state = RecoveryState.RECOVERY_PLANNED.value

        await AuditService.log_event(
            db=db,
            actor=ActorType.SYSTEM_AGENT,
            action="AI_DIAGNOSIS_AND_PLAN_CREATED",
            transaction_id=txn.id,
            workflow_id=workflow.id,
            details={
                "confidence": reasoning.confidence,
                "recommended_action": reasoning.recommended_intervention.value,
                "expected_recovery": reasoning.expected_recovery_amount,
                "summary": reasoning.summary
            }
        )

        # 3. Deterministic Policy Evaluation
        policy_result = PolicyEngine.evaluate(
            recommended_action=reasoning.recommended_intervention,
            amount=txn.amount,
            attempts_count=txn.attempts_count,
            risk_score=workflow.risk_score,
            is_returning_customer=cust.is_returning,
            autonomous_limit=merch.autonomous_limit if merch else 5000.0,
            max_retries=merch.max_retries if merch else 2,
            risk_threshold=merch.risk_threshold if merch else 0.70,
            is_already_recovered=(txn.status == PaymentStatus.RECOVERED.value or txn.status == PaymentStatus.CAPTURED.value)
        )

        workflow.policy_evaluation = policy_result.model_dump()

        if policy_result.status == PolicyResultStatus.STOPPED:
            workflow.state = RecoveryState.STOPPED.value
            workflow.stopping_rule_triggered = policy_result.rejection_reason
            await AuditService.log_event(
                db=db,
                actor=ActorType.POLICY_ENGINE,
                action="WORKFLOW_STOPPED_BY_POLICY",
                transaction_id=txn.id,
                workflow_id=workflow.id,
                details={"reason": policy_result.rejection_reason}
            )
        elif policy_result.status == PolicyResultStatus.OVERRIDDEN_TO_ESCALATE or policy_result.requires_human_approval:
            workflow.state = RecoveryState.ESCALATED.value
            workflow.escalation_reason = policy_result.rejection_reason
            await AuditService.log_event(
                db=db,
                actor=ActorType.POLICY_ENGINE,
                action="ACTION_OVERRIDDEN_TO_HUMAN_ESCALATION",
                transaction_id=txn.id,
                workflow_id=workflow.id,
                details={"reason": policy_result.rejection_reason}
            )
        elif policy_result.status == PolicyResultStatus.ALLOWED:
            workflow.state = RecoveryState.POLICY_APPROVED.value
            await AuditService.log_event(
                db=db,
                actor=ActorType.POLICY_ENGINE,
                action="POLICY_APPROVED",
                transaction_id=txn.id,
                workflow_id=workflow.id,
                details={"action": policy_result.allowed_action.value}
            )

        await db.flush()
        return workflow

    async def execute_workflow(self, db: AsyncSession, workflow_id: str) -> RecoveryWorkflow:
        stmt = (
            select(RecoveryWorkflow)
            .where(RecoveryWorkflow.id == workflow_id)
            .options(
                selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.customer),
                selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.merchant)
            )
        )
        res = await db.execute(stmt)
        workflow = res.scalar_one_or_none()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")

        txn: Transaction = workflow.transaction
        cust: Customer = txn.customer

        if workflow.state not in [RecoveryState.POLICY_APPROVED.value, RecoveryState.ESCALATED.value]:
            raise ValueError(f"Workflow in state '{workflow.state}' is not eligible for execution")

        workflow.state = RecoveryState.ACTION_EXECUTING.value
        action = workflow.recommended_action

        # Execute bounded tool via Razorpay Service
        if action == InterventionType.PAYMENT_LINK.value:
            payload = await self.razorpay_service.create_payment_link(
                amount=txn.amount,
                currency=txn.currency,
                customer_name=cust.name or "Customer",
                customer_email=cust.email,
                customer_phone=cust.phone,
                reference_id=f"rec_{txn.id}"
            )
            workflow.execution_payload = payload
            workflow.state = RecoveryState.AWAITING_PAYMENT_EVENT.value
            await AuditService.log_event(
                db=db,
                actor=ActorType.SYSTEM_AGENT,
                action="PAYMENT_LINK_CREATED_AND_DISPATCHED",
                transaction_id=txn.id,
                workflow_id=workflow.id,
                details=payload
            )

        elif action == InterventionType.DELAYED_RETRY.value:
            payload = await self.razorpay_service.schedule_delayed_retry(
                transaction_id=txn.id,
                amount=txn.amount,
                delay_minutes=30
            )
            workflow.execution_payload = payload
            workflow.state = RecoveryState.AWAITING_PAYMENT_EVENT.value
            await AuditService.log_event(
                db=db,
                actor=ActorType.SYSTEM_AGENT,
                action="SMART_DELAYED_RETRY_SCHEDULED",
                transaction_id=txn.id,
                workflow_id=workflow.id,
                details=payload
            )

        elif action == InterventionType.ALTERNATIVE_PAYMENT.value or action == InterventionType.CUSTOMER_NOTIFICATION.value:
            payload = await self.razorpay_service.dispatch_customer_notification(
                customer_email=cust.email,
                customer_phone=cust.phone,
                payment_link_url=f"https://rzp.io/i/alt_{txn.id[:8]}",
                amount=txn.amount
            )
            workflow.execution_payload = payload
            workflow.state = RecoveryState.AWAITING_PAYMENT_EVENT.value
            await AuditService.log_event(
                db=db,
                actor=ActorType.SYSTEM_AGENT,
                action="ALTERNATIVE_PAYMENT_NOTIFICATION_DISPATCHED",
                transaction_id=txn.id,
                workflow_id=workflow.id,
                details=payload
            )

        elif action == InterventionType.STOP.value or action == InterventionType.NO_ACTION.value:
            workflow.state = RecoveryState.STOPPED.value
            workflow.stopping_rule_triggered = "Stopping action determined by policy."
            await AuditService.log_event(
                db=db,
                actor=ActorType.POLICY_ENGINE,
                action="WORKFLOW_STOPPED",
                transaction_id=txn.id,
                workflow_id=workflow.id,
                details={"reason": "Explicit stop/no-action"}
            )
        else:
            workflow.state = RecoveryState.AWAITING_PAYMENT_EVENT.value

        await db.flush()
        return workflow

    async def settle_recovery_success(self, db: AsyncSession, transaction_id: str, amount: float) -> Optional[RecoveryWorkflow]:
        """Called when an asynchronous webhook (payment.captured / payment.authorized) confirms settlement."""
        stmt = (
            select(RecoveryWorkflow)
            .where(RecoveryWorkflow.transaction_id == transaction_id)
            .options(
                selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.customer)
            )
        )
        res = await db.execute(stmt)
        workflow = res.scalar_one_or_none()
        if not workflow:
            return None

        txn = workflow.transaction
        cust = txn.customer

        txn.status = PaymentStatus.RECOVERED.value
        workflow.state = RecoveryState.RECOVERED.value
        workflow.recovered_amount = amount
        cust.total_successful_payments += 1
        cust.is_returning = True

        await AuditService.log_event(
            db=db,
            actor=ActorType.RAZORPAY_WEBHOOK,
            action="RECOVERY_SETTLED_SUCCESSFULLY",
            transaction_id=txn.id,
            workflow_id=workflow.id,
            details={"recovered_amount": amount, "final_status": "RECOVERED"}
        )

        await db.flush()
        return workflow

    # =========================================================================
    # 2. CHECKOUT DROP-OFF RECOVERY ORCHESTRATION
    # =========================================================================
    async def plan_checkout_recovery(self, db: AsyncSession, checkout_id: str) -> tuple[CheckoutSession, RecoveryWorkflow]:
        stmt = select(CheckoutSession).where(CheckoutSession.id == checkout_id).options(
            selectinload(CheckoutSession.customer),
            selectinload(CheckoutSession.merchant)
        )
        res = await db.execute(stmt)
        session_obj = res.scalar_one_or_none()
        if not session_obj:
            raise ValueError(f"CheckoutSession {checkout_id} not found")

        cust = session_obj.customer
        merch = session_obj.merchant

        # Find or create workflow
        wf_stmt = select(RecoveryWorkflow).where(RecoveryWorkflow.reference_id == checkout_id)
        wf_res = await db.execute(wf_stmt)
        workflow = wf_res.scalar_one_or_none()
        if not workflow:
            workflow = RecoveryWorkflow(
                id=f"rec_chk_{session_obj.id[:10]}",
                recovery_type=RecoveryType.CHECKOUT.value,
                reference_id=session_obj.id,
                state=RecoveryState.RECOVERY_ELIGIBLE.value,
                risk_score=0.10 if cust and cust.is_returning else 0.25,
                failure_category=FailureCategory.CUSTOMER_DROPOFF.value,
                execution_mode=ExecutionMode.SIMULATED.value
            )
            db.add(workflow)
            await db.flush()

        # AI Reasoning
        reasoning = await self.agent.plan_checkout_recovery(
            cart_value=session_obj.cart_value,
            exit_step=session_obj.exit_step,
            detected_friction=session_obj.detected_friction,
            customer_name=cust.name if cust else "Shopper",
            is_returning=cust.is_returning if cust else False
        )
        workflow.ai_confidence = reasoning.confidence
        workflow.recommended_action = reasoning.recommended_intervention.value
        workflow.ai_reasoning = reasoning.model_dump()
        workflow.state = RecoveryState.RECOVERY_PLANNED.value

        # Policy Evaluation
        policy_res = PolicyEngine.evaluate(
            recommended_action=reasoning.recommended_intervention,
            amount=session_obj.cart_value,
            attempts_count=1,
            risk_score=workflow.risk_score,
            is_returning_customer=cust.is_returning if cust else False,
            autonomous_limit=merch.autonomous_limit if merch else 5000.0,
            max_retries=2,
            risk_threshold=merch.risk_threshold if merch else 0.70,
            recovery_type=RecoveryType.CHECKOUT
        )
        workflow.policy_evaluation = policy_res.model_dump()

        if policy_res.status == PolicyResultStatus.OVERRIDDEN_TO_ESCALATE or policy_res.requires_human_approval:
            workflow.state = RecoveryState.ESCALATED.value
            workflow.escalation_reason = policy_res.rejection_reason
        elif policy_res.status == PolicyResultStatus.ALLOWED:
            workflow.state = RecoveryState.POLICY_APPROVED.value

        await AuditService.log_event(
            db=db,
            actor=ActorType.SYSTEM_AGENT,
            action="CHECKOUT_DROPOFF_DIAGNOSED",
            workflow_id=workflow.id,
            details={
                "cart_value": session_obj.cart_value,
                "exit_step": session_obj.exit_step,
                "policy_status": policy_res.status.value,
                "recommendation": reasoning.recommended_intervention.value
            }
        )
        await db.flush()
        return session_obj, workflow

    async def execute_checkout_recovery(self, db: AsyncSession, checkout_id: str) -> tuple[CheckoutSession, RecoveryWorkflow]:
        session_obj, workflow = await self.plan_checkout_recovery(db, checkout_id)
        cust = session_obj.customer

        if workflow.state in [RecoveryState.POLICY_APPROVED.value, RecoveryState.RECOVERY_PLANNED.value]:
            workflow.state = RecoveryState.ACTION_EXECUTING.value
            recovery_url = f"https://rzp.io/l/recover_chk_{session_obj.id[:8]}"
            session_obj.recovery_link_url = recovery_url
            session_obj.recovery_status = "RECOVERY_INITIATED"
            workflow.execution_payload = {
                "recovery_url": recovery_url,
                "cart_value": session_obj.cart_value,
                "dispatched_to": cust.email if cust else "customer@example.com",
                "execution_mode": ExecutionMode.SIMULATED.value,
                "status": "DISPATCHED"
            }
            workflow.state = RecoveryState.AWAITING_PAYMENT_EVENT.value
            await AuditService.log_event(
                db=db,
                actor=ActorType.SYSTEM_AGENT,
                action="CHECKOUT_RECOVERY_LINK_DISPATCHED",
                workflow_id=workflow.id,
                details=workflow.execution_payload
            )
        await db.flush()
        return session_obj, workflow

    # =========================================================================
    # 3. FAILED SUBSCRIPTION RECOVERY ORCHESTRATION
    # =========================================================================
    async def plan_subscription_recovery(self, db: AsyncSession, subscription_id: str) -> tuple[Subscription, RecoveryWorkflow]:
        stmt = select(Subscription).where(Subscription.id == subscription_id).options(
            selectinload(Subscription.customer),
            selectinload(Subscription.merchant)
        )
        res = await db.execute(stmt)
        sub = res.scalar_one_or_none()
        if not sub:
            raise ValueError(f"Subscription {subscription_id} not found")

        cust = sub.customer
        merch = sub.merchant

        wf_stmt = select(RecoveryWorkflow).where(RecoveryWorkflow.reference_id == subscription_id)
        wf_res = await db.execute(wf_stmt)
        workflow = wf_res.scalar_one_or_none()
        if not workflow:
            workflow = RecoveryWorkflow(
                id=f"rec_sub_{sub.id[:10]}",
                recovery_type=RecoveryType.SUBSCRIPTION.value,
                reference_id=sub.id,
                state=RecoveryState.RECOVERY_ELIGIBLE.value,
                risk_score=0.15,
                failure_category=FailureCategory.SUBSCRIPTION_RENEWAL_FAILURE.value,
                execution_mode=ExecutionMode.SIMULATED.value
            )
            db.add(workflow)
            await db.flush()

        reasoning = await self.agent.plan_subscription_recovery(
            recurring_amount=sub.recurring_amount,
            plan_name=sub.plan_name,
            failed_attempts=sub.failed_attempts,
            last_failure_reason=sub.last_failure_reason or "Card renewal decline",
            customer_name=cust.name if cust else "Subscriber",
            is_returning=True
        )
        workflow.ai_confidence = reasoning.confidence
        workflow.recommended_action = reasoning.recommended_intervention.value
        workflow.ai_reasoning = reasoning.model_dump()
        workflow.state = RecoveryState.RECOVERY_PLANNED.value

        policy_res = PolicyEngine.evaluate(
            recommended_action=reasoning.recommended_intervention,
            amount=sub.recurring_amount,
            attempts_count=sub.failed_attempts,
            risk_score=workflow.risk_score,
            is_returning_customer=True,
            autonomous_limit=merch.autonomous_limit if merch else 5000.0,
            max_retries=sub.max_retries,
            risk_threshold=merch.risk_threshold if merch else 0.70,
            recovery_type=RecoveryType.SUBSCRIPTION,
            cooldown_passed=True
        )
        workflow.policy_evaluation = policy_res.model_dump()

        if policy_res.status == PolicyResultStatus.STOPPED:
            workflow.state = RecoveryState.STOPPED.value
            workflow.stopping_rule_triggered = policy_res.rejection_reason
            sub.status = "HALTED"
        elif policy_res.status == PolicyResultStatus.OVERRIDDEN_TO_ESCALATE:
            workflow.state = RecoveryState.ESCALATED.value
            workflow.escalation_reason = policy_res.rejection_reason
        elif policy_res.status == PolicyResultStatus.ALLOWED:
            workflow.state = RecoveryState.POLICY_APPROVED.value

        await AuditService.log_event(
            db=db,
            actor=ActorType.SYSTEM_AGENT,
            action="SUBSCRIPTION_RECOVERY_EVALUATED",
            workflow_id=workflow.id,
            details={
                "plan_name": sub.plan_name,
                "amount": sub.recurring_amount,
                "attempt": sub.failed_attempts,
                "policy_decision": policy_res.status.value
            }
        )
        await db.flush()
        return sub, workflow

    async def execute_subscription_recovery(self, db: AsyncSession, subscription_id: str) -> tuple[Subscription, RecoveryWorkflow]:
        sub, workflow = await self.plan_subscription_recovery(db, subscription_id)
        if workflow.state in [RecoveryState.POLICY_APPROVED.value, RecoveryState.RECOVERY_PLANNED.value]:
            workflow.state = RecoveryState.ACTION_EXECUTING.value
            action = workflow.recommended_action
            payload = {
                "subscription_id": sub.id,
                "action": action,
                "cooldown_hours": sub.cooldown_hours,
                "execution_mode": ExecutionMode.SIMULATED.value,
                "status": "RETRY_SCHEDULED" if "RETRY" in action else "UPDATE_LINK_SENT"
            }
            workflow.execution_payload = payload
            workflow.state = RecoveryState.AWAITING_PAYMENT_EVENT.value
            await AuditService.log_event(
                db=db,
                actor=ActorType.SYSTEM_AGENT,
                action="SUBSCRIPTION_RECOVERY_EXECUTED",
                workflow_id=workflow.id,
                details=payload
            )
        await db.flush()
        return sub, workflow

    # =========================================================================
    # 4. B2B RECEIVABLES CHASER ORCHESTRATION
    # =========================================================================
    async def plan_receivable_chasing(self, db: AsyncSession, invoice_id: str) -> tuple[ReceivableInvoice, RecoveryWorkflow]:
        stmt = select(ReceivableInvoice).where(ReceivableInvoice.id == invoice_id).options(
            selectinload(ReceivableInvoice.customer),
            selectinload(ReceivableInvoice.merchant)
        )
        res = await db.execute(stmt)
        invoice = res.scalar_one_or_none()
        if not invoice:
            raise ValueError(f"ReceivableInvoice {invoice_id} not found")

        cust = invoice.customer
        merch = invoice.merchant

        wf_stmt = select(RecoveryWorkflow).where(RecoveryWorkflow.reference_id == invoice_id)
        wf_res = await db.execute(wf_stmt)
        workflow = wf_res.scalar_one_or_none()
        if not workflow:
            workflow = RecoveryWorkflow(
                id=f"rec_inv_{invoice.id[:10]}",
                recovery_type=RecoveryType.RECEIVABLE.value,
                reference_id=invoice.id,
                state=RecoveryState.RECOVERY_ELIGIBLE.value,
                risk_score=0.20 if invoice.overdue_days < 15 else 0.55,
                failure_category=FailureCategory.RECEIVABLE_OVERDUE.value,
                execution_mode=ExecutionMode.SIMULATED.value
            )
            db.add(workflow)
            await db.flush()

        reasoning = await self.agent.plan_receivable_chasing(
            invoice_amount=invoice.invoice_amount,
            overdue_days=invoice.overdue_days,
            contact_count=invoice.contact_count,
            customer_name=cust.name if cust else "B2B Buyer",
            risk_score=workflow.risk_score
        )
        workflow.ai_confidence = reasoning.confidence
        workflow.recommended_action = reasoning.recommended_intervention.value
        workflow.ai_reasoning = reasoning.model_dump()
        workflow.state = RecoveryState.RECOVERY_PLANNED.value

        policy_res = PolicyEngine.evaluate(
            recommended_action=reasoning.recommended_intervention,
            amount=invoice.invoice_amount,
            attempts_count=invoice.contact_count + 1,
            risk_score=workflow.risk_score,
            is_returning_customer=True,
            autonomous_limit=merch.autonomous_limit if merch else 5000.0,
            max_retries=4,
            risk_threshold=merch.risk_threshold if merch else 0.70,
            recovery_type=RecoveryType.RECEIVABLE,
            overdue_days=invoice.overdue_days
        )
        workflow.policy_evaluation = policy_res.model_dump()

        if policy_res.status == PolicyResultStatus.OVERRIDDEN_TO_ESCALATE or policy_res.requires_human_approval:
            workflow.state = RecoveryState.ESCALATED.value
            workflow.escalation_reason = policy_res.rejection_reason
            invoice.chasing_stage = "EXECUTIVE_ESCALATION"
        elif policy_res.status == PolicyResultStatus.ALLOWED:
            workflow.state = RecoveryState.POLICY_APPROVED.value
            invoice.chasing_stage = "FORMAL_FOLLOWUP" if invoice.overdue_days > 14 else "GENTLE_REMINDER"

        await AuditService.log_event(
            db=db,
            actor=ActorType.SYSTEM_AGENT,
            action="B2B_RECEIVABLE_CHASER_PLANNED",
            workflow_id=workflow.id,
            details={
                "invoice_number": invoice.invoice_number,
                "amount": invoice.invoice_amount,
                "overdue_days": invoice.overdue_days,
                "chasing_stage": invoice.chasing_stage,
                "policy_decision": policy_res.status.value
            }
        )
        await db.flush()
        return invoice, workflow

    async def execute_receivable_chasing(self, db: AsyncSession, invoice_id: str) -> tuple[ReceivableInvoice, RecoveryWorkflow]:
        invoice, workflow = await self.plan_receivable_chasing(db, invoice_id)
        cust = invoice.customer
        if workflow.state in [RecoveryState.POLICY_APPROVED.value, RecoveryState.RECOVERY_PLANNED.value]:
            workflow.state = RecoveryState.ACTION_EXECUTING.value
            invoice.contact_count += 1
            payload = {
                "invoice_number": invoice.invoice_number,
                "recipient_email": cust.email if cust else "accounts@client.com",
                "chasing_stage": invoice.chasing_stage,
                "amount": invoice.invoice_amount,
                "payment_url": f"https://rzp.io/i/inv_{invoice.invoice_number}",
                "execution_mode": ExecutionMode.SIMULATED.value,
                "status": "CHASER_DISPATCHED"
            }
            workflow.execution_payload = payload
            workflow.state = RecoveryState.AWAITING_PAYMENT_EVENT.value
            await AuditService.log_event(
                db=db,
                actor=ActorType.SYSTEM_AGENT,
                action="B2B_CHASER_DISPATCHED",
                workflow_id=workflow.id,
                details=payload
            )
        await db.flush()
        return invoice, workflow

    # =========================================================================
    # 5. MANDATE RETRY SEQUENCER ORCHESTRATION
    # =========================================================================
    async def plan_mandate_sequence(self, db: AsyncSession, mandate_id: str) -> tuple[Mandate, RecoveryWorkflow]:
        stmt = select(Mandate).where(Mandate.id == mandate_id).options(
            selectinload(Mandate.customer),
            selectinload(Mandate.merchant)
        )
        res = await db.execute(stmt)
        mandate = res.scalar_one_or_none()
        if not mandate:
            raise ValueError(f"Mandate {mandate_id} not found")

        cust = mandate.customer
        merch = mandate.merchant

        wf_stmt = select(RecoveryWorkflow).where(RecoveryWorkflow.reference_id == mandate_id)
        wf_res = await db.execute(wf_stmt)
        workflow = wf_res.scalar_one_or_none()
        if not workflow:
            workflow = RecoveryWorkflow(
                id=f"rec_man_{mandate.id[:10]}",
                recovery_type=RecoveryType.MANDATE.value,
                reference_id=mandate.id,
                state=RecoveryState.RECOVERY_ELIGIBLE.value,
                risk_score=0.12,
                failure_category=FailureCategory.MANDATE_CLEARING_ERROR.value,
                execution_mode=ExecutionMode.SIMULATED.value
            )
            db.add(workflow)
            await db.flush()

        reasoning = await self.agent.plan_mandate_sequence(
            scheduled_amount=mandate.scheduled_amount,
            attempt_number=mandate.attempt_number,
            mandate_type=mandate.mandate_type,
            failure_code=mandate.failure_code,
            customer_name=cust.name if cust else "Mandate Holder"
        )
        workflow.ai_confidence = reasoning.confidence
        workflow.recommended_action = reasoning.recommended_intervention.value
        workflow.ai_reasoning = reasoning.model_dump()
        workflow.state = RecoveryState.RECOVERY_PLANNED.value

        policy_res = PolicyEngine.evaluate(
            recommended_action=reasoning.recommended_intervention,
            amount=mandate.scheduled_amount,
            attempts_count=mandate.attempt_number,
            risk_score=workflow.risk_score,
            is_returning_customer=True,
            autonomous_limit=merch.autonomous_limit if merch else 5000.0,
            max_retries=mandate.max_attempts,
            risk_threshold=merch.risk_threshold if merch else 0.70,
            recovery_type=RecoveryType.MANDATE
        )
        workflow.policy_evaluation = policy_res.model_dump()

        if policy_res.status == PolicyResultStatus.STOPPED:
            workflow.state = RecoveryState.STOPPED.value
            workflow.stopping_rule_triggered = policy_res.rejection_reason
            mandate.status = "STOPPED"
        elif policy_res.status == PolicyResultStatus.ALLOWED:
            workflow.state = RecoveryState.POLICY_APPROVED.value
            mandate.status = "SEQUENCED"

        await AuditService.log_event(
            db=db,
            actor=ActorType.POLICY_ENGINE if policy_res.status == PolicyResultStatus.STOPPED else ActorType.SYSTEM_AGENT,
            action="MANDATE_SEQUENCE_PLANNED",
            workflow_id=workflow.id,
            details={
                "mandate_id": mandate.id,
                "attempt": mandate.attempt_number,
                "max_attempts": mandate.max_attempts,
                "policy_status": policy_res.status.value,
                "rejection_reason": policy_res.rejection_reason
            }
        )
        await db.flush()
        return mandate, workflow

    async def execute_mandate_sequence(self, db: AsyncSession, mandate_id: str) -> tuple[Mandate, RecoveryWorkflow]:
        mandate, workflow = await self.plan_mandate_sequence(db, mandate_id)
        if workflow.state in [RecoveryState.POLICY_APPROVED.value, RecoveryState.RECOVERY_PLANNED.value]:
            workflow.state = RecoveryState.ACTION_EXECUTING.value
            payload = {
                "mandate_id": mandate.id,
                "mandate_token": mandate.mandate_token,
                "amount": mandate.scheduled_amount,
                "attempt_number": mandate.attempt_number,
                "clearing_cycle": "NACH_SESSION_2",
                "execution_mode": ExecutionMode.SIMULATED.value,
                "status": "DEBIT_PRESENTED"
            }
            workflow.execution_payload = payload
            workflow.state = RecoveryState.AWAITING_PAYMENT_EVENT.value
            await AuditService.log_event(
                db=db,
                actor=ActorType.SYSTEM_AGENT,
                action="MANDATE_DEBIT_PRESENTED",
                workflow_id=workflow.id,
                details=payload
            )
        await db.flush()
        return mandate, workflow

    # =========================================================================
    # 6. HINGLISH VOICE RECOVERY ORCHESTRATION
    # =========================================================================
    async def plan_voice_recovery(self, db: AsyncSession, session_id: str) -> tuple[VoiceRecoverySession, RecoveryWorkflow]:
        stmt = select(VoiceRecoverySession).where(VoiceRecoverySession.id == session_id).options(
            selectinload(VoiceRecoverySession.customer),
            selectinload(VoiceRecoverySession.merchant)
        )
        res = await db.execute(stmt)
        voice_sess = res.scalar_one_or_none()
        if not voice_sess:
            raise ValueError(f"VoiceRecoverySession {session_id} not found")

        cust = voice_sess.customer
        merch = voice_sess.merchant

        wf_stmt = select(RecoveryWorkflow).where(RecoveryWorkflow.reference_id == session_id)
        wf_res = await db.execute(wf_stmt)
        workflow = wf_res.scalar_one_or_none()
        if not workflow:
            workflow = RecoveryWorkflow(
                id=f"rec_voc_{voice_sess.id[:10]}",
                recovery_type=RecoveryType.VOICE_RECOVERY.value,
                reference_id=voice_sess.id,
                state=RecoveryState.RECOVERY_ELIGIBLE.value,
                risk_score=0.15,
                failure_category=FailureCategory.VOICE_OUTREACH_REQUIRED.value,
                execution_mode=ExecutionMode.SIMULATED.value
            )
            db.add(workflow)
            await db.flush()

        reasoning, script = await self.agent.plan_voice_recovery(
            amount=4999.0,
            failure_reason="Temporary decline",
            language=voice_sess.language,
            customer_name=cust.name if cust else "Customer",
            order_reference=f"ORD-{session_id[:6]}"
        )
        voice_sess.generated_script = script
        workflow.ai_confidence = reasoning.confidence
        workflow.recommended_action = reasoning.recommended_intervention.value
        workflow.ai_reasoning = reasoning.model_dump()
        workflow.state = RecoveryState.RECOVERY_PLANNED.value

        policy_res = PolicyEngine.evaluate(
            recommended_action=reasoning.recommended_intervention,
            amount=4999.0,
            attempts_count=1,
            risk_score=workflow.risk_score,
            is_returning_customer=True,
            autonomous_limit=merch.autonomous_limit if merch else 5000.0,
            max_retries=1,
            risk_threshold=merch.risk_threshold if merch else 0.70,
            recovery_type=RecoveryType.VOICE_RECOVERY,
            is_within_contact_hours=True
        )
        workflow.policy_evaluation = policy_res.model_dump()

        if policy_res.status == PolicyResultStatus.ALLOWED:
            workflow.state = RecoveryState.POLICY_APPROVED.value

        await AuditService.log_event(
            db=db,
            actor=ActorType.VOICE_AGENT,
            action="VOICE_RECOVERY_SCRIPT_SYNTHESIZED",
            workflow_id=workflow.id,
            details={
                "language": voice_sess.language,
                "phone": voice_sess.phone_number,
                "script_preview": script[:80] + "...",
                "policy_decision": policy_res.status.value
            }
        )
        await db.flush()
        return voice_sess, workflow

    async def execute_voice_recovery(self, db: AsyncSession, session_id: str) -> tuple[VoiceRecoverySession, RecoveryWorkflow]:
        voice_sess, workflow = await self.plan_voice_recovery(db, session_id)
        if workflow.state in [RecoveryState.POLICY_APPROVED.value, RecoveryState.RECOVERY_PLANNED.value]:
            voice_sess.call_status = "CONNECTED"
            voice_sess.payment_link_sent = True
            payload = {
                "session_id": voice_sess.id,
                "phone": voice_sess.phone_number,
                "language": voice_sess.language,
                "intent_detected": voice_sess.detected_intent,
                "payment_link_dispatched": True,
                "execution_mode": ExecutionMode.SIMULATED.value,
                "status": "VOICE_CALL_SIMULATED"
            }
            voice_sess.audio_simulation_state = payload
            workflow.execution_payload = payload
            workflow.state = RecoveryState.AWAITING_PAYMENT_EVENT.value
            await AuditService.log_event(
                db=db,
                actor=ActorType.VOICE_AGENT,
                action="VOICE_RECOVERY_CALL_EXECUTED",
                workflow_id=workflow.id,
                details=payload
            )
        await db.flush()
        return voice_sess, workflow

    # =========================================================================
    # 7. PROMISE-TO-PAY (PTP) TRACKER ORCHESTRATION
    # =========================================================================
    async def plan_promise_to_pay(self, db: AsyncSession, promise_id: str) -> tuple[PromiseToPay, RecoveryWorkflow]:
        stmt = select(PromiseToPay).where(PromiseToPay.id == promise_id).options(
            selectinload(PromiseToPay.customer),
            selectinload(PromiseToPay.merchant)
        )
        res = await db.execute(stmt)
        ptp = res.scalar_one_or_none()
        if not ptp:
            raise ValueError(f"PromiseToPay {promise_id} not found")

        cust = ptp.customer
        merch = ptp.merchant

        wf_stmt = select(RecoveryWorkflow).where(RecoveryWorkflow.reference_id == promise_id)
        wf_res = await db.execute(wf_stmt)
        workflow = wf_res.scalar_one_or_none()
        if not workflow:
            workflow = RecoveryWorkflow(
                id=f"rec_ptp_{ptp.id[:10]}",
                recovery_type=RecoveryType.PROMISE_TO_PAY.value,
                reference_id=ptp.id,
                state=RecoveryState.RECOVERY_ELIGIBLE.value,
                risk_score=0.18,
                failure_category=FailureCategory.RECEIVABLE_OVERDUE.value,
                execution_mode=ExecutionMode.SIMULATED.value
            )
            db.add(workflow)
            await db.flush()

        reasoning = await self.agent.plan_promise_to_pay(
            promised_amount=ptp.promised_amount,
            overdue_days=0,
            previous_breaches_count=0,
            customer_name=cust.name if cust else "Debtor"
        )
        workflow.ai_confidence = reasoning.confidence
        workflow.recommended_action = reasoning.recommended_intervention.value
        workflow.ai_reasoning = reasoning.model_dump()
        workflow.state = RecoveryState.RECOVERY_PLANNED.value

        policy_res = PolicyEngine.evaluate(
            recommended_action=reasoning.recommended_intervention,
            amount=ptp.promised_amount,
            attempts_count=ptp.reminder_sent_count,
            risk_score=workflow.risk_score,
            is_returning_customer=True,
            autonomous_limit=merch.autonomous_limit if merch else 5000.0,
            max_retries=3,
            risk_threshold=merch.risk_threshold if merch else 0.70,
            recovery_type=RecoveryType.PROMISE_TO_PAY
        )
        workflow.policy_evaluation = policy_res.model_dump()

        if policy_res.status == PolicyResultStatus.OVERRIDDEN_TO_ESCALATE:
            workflow.state = RecoveryState.ESCALATED.value
            workflow.escalation_reason = policy_res.rejection_reason
            ptp.status = "ESCALATED"
        elif policy_res.status == PolicyResultStatus.ALLOWED:
            workflow.state = RecoveryState.POLICY_APPROVED.value

        await AuditService.log_event(
            db=db,
            actor=ActorType.SYSTEM_AGENT,
            action="PROMISE_TO_PAY_REGISTERED",
            workflow_id=workflow.id,
            details={
                "promised_amount": ptp.promised_amount,
                "promised_date": str(ptp.promised_date),
                "policy_status": policy_res.status.value
            }
        )
        await db.flush()
        return ptp, workflow

    async def fulfill_promise_to_pay(self, db: AsyncSession, promise_id: str) -> tuple[PromiseToPay, RecoveryWorkflow]:
        ptp, workflow = await self.plan_promise_to_pay(db, promise_id)
        from datetime import datetime, timezone
        ptp.status = "FULFILLED"
        ptp.fulfilled_at = datetime.now(timezone.utc)
        workflow.state = RecoveryState.RECOVERED.value
        workflow.recovered_amount = ptp.promised_amount

        await AuditService.log_event(
            db=db,
            actor=ActorType.RAZORPAY_WEBHOOK,
            action="PROMISE_TO_PAY_FULFILLED",
            workflow_id=workflow.id,
            details={
                "promise_id": ptp.id,
                "amount": ptp.promised_amount,
                "status": "FULFILLED"
            }
        )
        await db.flush()
        return ptp, workflow

    async def breach_promise_to_pay(self, db: AsyncSession, promise_id: str) -> tuple[PromiseToPay, RecoveryWorkflow]:
        ptp, workflow = await self.plan_promise_to_pay(db, promise_id)
        from datetime import datetime, timezone
        ptp.status = "BREACHED"
        ptp.breached_at = datetime.now(timezone.utc)
        workflow.state = RecoveryState.ESCALATED.value
        workflow.escalation_reason = "Debtor missed promised commitment date; escalated to human collections."

        await AuditService.log_event(
            db=db,
            actor=ActorType.POLICY_ENGINE,
            action="PROMISE_TO_PAY_BREACHED",
            workflow_id=workflow.id,
            details={
                "promise_id": ptp.id,
                "amount": ptp.promised_amount,
                "status": "BREACHED",
                "escalated": True
            }
        )
        await db.flush()
        return ptp, workflow

