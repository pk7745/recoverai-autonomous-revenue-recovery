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
