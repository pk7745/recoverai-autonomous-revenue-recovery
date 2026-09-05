import uuid
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.recovery_workflow import RecoveryWorkflow
from app.models.transaction import Transaction
from app.models.merchant import Merchant
from app.models.customer import Customer
from app.core.enums import (
    RecoveryState,
    PaymentStatus,
    InterventionType,
    PolicyResultStatus,
    ActorType
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
