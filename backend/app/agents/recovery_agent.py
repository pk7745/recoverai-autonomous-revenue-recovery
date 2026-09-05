from typing import Optional
from app.agents.ai_provider import BaseAIProvider, HybridExpertAIProvider
from app.schemas.recovery import AIReasoning

class RecoveryAgent:
    """
    Agentic Orchestrator for payment failure diagnosis and structured recovery planning.
    """
    def __init__(self, provider: Optional[BaseAIProvider] = None):
        self.provider = provider or HybridExpertAIProvider()

    async def plan_recovery(
        self,
        transaction_amount: float,
        failure_code: str,
        failure_reason: str,
        payment_method: str,
        attempts_count: int,
        customer_name: str,
        customer_successful_payments: int,
        customer_failed_payments: int,
        is_returning: bool
    ) -> AIReasoning:
        return await self.provider.generate_recovery_plan(
            transaction_amount=transaction_amount,
            failure_code=failure_code,
            failure_reason=failure_reason,
            payment_method=payment_method,
            attempts_count=attempts_count,
            customer_name=customer_name,
            customer_successful_payments=customer_successful_payments,
            customer_failed_payments=customer_failed_payments,
            is_returning=is_returning
        )

    async def plan_checkout_recovery(
        self,
        cart_value: float,
        exit_step: str,
        detected_friction: str,
        customer_name: str,
        is_returning: bool
    ) -> AIReasoning:
        return await self.provider.generate_checkout_recovery_plan(
            cart_value=cart_value,
            exit_step=exit_step,
            detected_friction=detected_friction,
            customer_name=customer_name,
            is_returning=is_returning
        )

    async def plan_subscription_recovery(
        self,
        recurring_amount: float,
        plan_name: str,
        failed_attempts: int,
        last_failure_reason: str,
        customer_name: str,
        is_returning: bool
    ) -> AIReasoning:
        return await self.provider.generate_subscription_recovery_plan(
            recurring_amount=recurring_amount,
            plan_name=plan_name,
            failed_attempts=failed_attempts,
            last_failure_reason=last_failure_reason,
            customer_name=customer_name,
            is_returning=is_returning
        )

    async def plan_receivable_chasing(
        self,
        invoice_amount: float,
        overdue_days: int,
        contact_count: int,
        customer_name: str,
        risk_score: float
    ) -> AIReasoning:
        return await self.provider.generate_receivable_chasing_plan(
            invoice_amount=invoice_amount,
            overdue_days=overdue_days,
            contact_count=contact_count,
            customer_name=customer_name,
            risk_score=risk_score
        )

    async def plan_mandate_sequence(
        self,
        scheduled_amount: float,
        attempt_number: int,
        mandate_type: str,
        failure_code: str,
        customer_name: str
    ) -> AIReasoning:
        return await self.provider.generate_mandate_sequence_plan(
            scheduled_amount=scheduled_amount,
            attempt_number=attempt_number,
            mandate_type=mandate_type,
            failure_code=failure_code,
            customer_name=customer_name
        )

    async def plan_voice_recovery(
        self,
        amount: float,
        failure_reason: str,
        language: str,
        customer_name: str,
        order_reference: str
    ) -> tuple[AIReasoning, str]:
        return await self.provider.generate_voice_recovery_plan(
            amount=amount,
            failure_reason=failure_reason,
            language=language,
            customer_name=customer_name,
            order_reference=order_reference
        )

    async def plan_promise_to_pay(
        self,
        promised_amount: float,
        overdue_days: int,
        previous_breaches_count: int,
        customer_name: str
    ) -> AIReasoning:
        return await self.provider.generate_promise_to_pay_plan(
            promised_amount=promised_amount,
            overdue_days=overdue_days,
            previous_breaches_count=previous_breaches_count,
            customer_name=customer_name
        )
