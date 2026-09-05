from abc import ABC, abstractmethod
from typing import Dict, Any, List
from app.core.enums import FailureCategory, InterventionType, RiskTier
from app.schemas.recovery import AIReasoning, DecisionFactor
from app.agents.tools import RecoveryToolRegistry
from app.risk.risk_engine import RiskEngine

class BaseAIProvider(ABC):
    @abstractmethod
    async def generate_recovery_plan(
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
        pass

class HybridExpertAIProvider(BaseAIProvider):
    """
    High-performance, deterministic expert reasoning engine.
    Computes exact, transparent, multi-factor revenue recovery decisions and explanations.
    """

    async def generate_recovery_plan(
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
        category = RecoveryToolRegistry.classify_failure(failure_code, failure_reason, payment_method)
        risk_score, risk_tier, _ = RiskEngine.evaluate_risk(
            amount=transaction_amount,
            failure_category=category,
            customer_successful_payments=customer_successful_payments,
            customer_failed_payments=customer_failed_payments,
            attempts_count=attempts_count,
            is_returning=is_returning
        )

        factors: List[DecisionFactor] = []
        
        # 1. Evaluate failure context
        if category == FailureCategory.TEMPORARY_ISSUER_DECLINE:
            factors.append(DecisionFactor(
                title="Transient Gateway State",
                description="Failure was classified as a temporary bank/issuer outage that typically resolves in 15-45 minutes.",
                impact="POSITIVE",
                icon="clock"
            ))
        elif category == FailureCategory.AUTHENTICATION_FAILURE:
            factors.append(DecisionFactor(
                title="Customer 3DS Dropoff",
                description="Session dropped during two-factor authentication or OTP expired. Payment link allows customer to resume checkout on mobile.",
                impact="NEUTRAL",
                icon="smartphone"
            ))
        elif category == FailureCategory.INSUFFICIENT_FUNDS:
            factors.append(DecisionFactor(
                title="Balance Depletion",
                description="Account had insufficient funds. Immediate retries will fail; offering alternate payment method or split payment is optimal.",
                impact="NEGATIVE",
                icon="credit-card"
            ))
        elif category == FailureCategory.SUSPICIOUS_FRAUD:
            factors.append(DecisionFactor(
                title="Fraud / Risk Anomaly",
                description="Transaction triggered suspicious velocity or card risk indicators. Autonomous action must be suppressed.",
                impact="NEGATIVE",
                icon="shield-alert"
            ))
            
        # 2. Evaluate Customer History
        if is_returning and customer_successful_payments >= 3:
            factors.append(DecisionFactor(
                title="High-Value Returning Customer",
                description=f"Customer has completed {customer_successful_payments} prior successful orders with high lifetime loyalty.",
                impact="POSITIVE",
                icon="user-check"
            ))
        elif not is_returning:
            factors.append(DecisionFactor(
                title="First-Time Customer Profile",
                description="No historical payment profile established. Retries should be limited to prevent friction.",
                impact="NEUTRAL",
                icon="user-plus"
            ))
            
        # 3. Evaluate Attempt History
        if attempts_count == 1:
            factors.append(DecisionFactor(
                title="First Failure Encountered",
                description="Initial attempt only; recovery probability remains high (>80%).",
                impact="POSITIVE",
                icon="zap"
            ))
        elif attempts_count >= 3:
            factors.append(DecisionFactor(
                title="Multiple Prior Attempts",
                description=f"{attempts_count} prior attempts recorded. Continued retries risk merchant card association penalties.",
                impact="NEGATIVE",
                icon="alert-triangle"
            ))

        # Decision synthesis
        if category == FailureCategory.SUSPICIOUS_FRAUD or risk_tier == RiskTier.CRITICAL:
            recommended_action = InterventionType.HUMAN_ESCALATION
            confidence = 0.94
            summary = "Flagged for Human Fraud Review due to elevated risk anomaly indicators."
            expected_amount = 0.0
        elif attempts_count >= 3:
            recommended_action = InterventionType.STOP
            confidence = 0.96
            summary = "Stopping further retries to preserve customer experience and prevent issuer penalties."
            expected_amount = 0.0
        elif category == FailureCategory.TEMPORARY_ISSUER_DECLINE:
            if is_returning:
                recommended_action = InterventionType.DELAYED_RETRY
                confidence = 0.88
                summary = "Executing intelligent 30-minute Delayed Retry based on transient issuer decline and strong customer history."
                expected_amount = transaction_amount
            else:
                recommended_action = InterventionType.PAYMENT_LINK
                confidence = 0.82
                summary = "Generating customized Razorpay Smart Payment Link for new customer."
                expected_amount = transaction_amount
        elif category == FailureCategory.AUTHENTICATION_FAILURE:
            recommended_action = InterventionType.PAYMENT_LINK
            confidence = 0.86
            summary = "Sending Razorpay Smart Payment Link via SMS/WhatsApp with 1-click retry."
            expected_amount = transaction_amount
        elif category == FailureCategory.INSUFFICIENT_FUNDS:
            recommended_action = InterventionType.ALTERNATIVE_PAYMENT
            confidence = 0.79
            summary = "Prompting customer with Alternative Payment options (UPI Intent / EMI)."
            expected_amount = transaction_amount
        else:
            recommended_action = InterventionType.DELAYED_RETRY
            confidence = 0.75
            summary = "Scheduling bounded delayed retry."
            expected_amount = transaction_amount

        return AIReasoning(
            summary=summary,
            confidence=confidence,
            factors=factors,
            root_cause_diagnosis=category.value,
            expected_recovery_amount=expected_amount,
            recommended_intervention=recommended_action
        )
