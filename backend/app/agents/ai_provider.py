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

    @abstractmethod
    async def generate_checkout_recovery_plan(
        self,
        cart_value: float,
        exit_step: str,
        detected_friction: str,
        customer_name: str,
        is_returning: bool
    ) -> AIReasoning:
        pass

    @abstractmethod
    async def generate_subscription_recovery_plan(
        self,
        recurring_amount: float,
        plan_name: str,
        failed_attempts: int,
        last_failure_reason: str,
        customer_name: str,
        is_returning: bool
    ) -> AIReasoning:
        pass

    @abstractmethod
    async def generate_receivable_chasing_plan(
        self,
        invoice_amount: float,
        overdue_days: int,
        contact_count: int,
        customer_name: str,
        risk_score: float
    ) -> AIReasoning:
        pass

    @abstractmethod
    async def generate_mandate_sequence_plan(
        self,
        scheduled_amount: float,
        attempt_number: int,
        mandate_type: str,
        failure_code: str,
        customer_name: str
    ) -> AIReasoning:
        pass

    @abstractmethod
    async def generate_voice_recovery_plan(
        self,
        amount: float,
        failure_reason: str,
        language: str,
        customer_name: str,
        order_reference: str
    ) -> tuple[AIReasoning, str]:
        pass

    @abstractmethod
    async def generate_promise_to_pay_plan(
        self,
        promised_amount: float,
        overdue_days: int,
        previous_breaches_count: int,
        customer_name: str
    ) -> AIReasoning:
        pass

class HybridExpertAIProvider(BaseAIProvider):
    """
    High-performance, deterministic expert reasoning engine.
    Computes exact, transparent, multi-factor revenue recovery decisions and explanations
    across all seven recovery programs.
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

    async def generate_checkout_recovery_plan(
        self,
        cart_value: float,
        exit_step: str,
        detected_friction: str,
        customer_name: str,
        is_returning: bool
    ) -> AIReasoning:
        factors: List[DecisionFactor] = [
            DecisionFactor(
                title="Checkout Exit Analysis",
                description=f"User abandoned at '{exit_step}' with detected friction '{detected_friction}'.",
                impact="NEUTRAL",
                icon="shopping-cart"
            ),
            DecisionFactor(
                title="Cart Value Exposure",
                description=f"High intent cart value of ₹{cart_value:,.2f} identified for rapid re-engagement.",
                impact="POSITIVE" if is_returning else "NEUTRAL",
                icon="dollar-sign"
            )
        ]

        if cart_value > 25000.0:
            recommended_action = InterventionType.HUMAN_ESCALATION
            confidence = 0.91
            summary = f"High-value cart (₹{cart_value:,.2f}) routed to VIP sales ops for personalized assistance."
            expected_amount = cart_value
        else:
            recommended_action = InterventionType.CHECKOUT_RECOVERY_LINK
            confidence = 0.87
            summary = f"Generated personalized Razorpay 1-click Checkout Recovery Link with pre-filled cart."
            expected_amount = cart_value

        return AIReasoning(
            summary=summary,
            confidence=confidence,
            factors=factors,
            root_cause_diagnosis=FailureCategory.CUSTOMER_DROPOFF.value,
            expected_recovery_amount=expected_amount,
            recommended_intervention=recommended_action
        )

    async def generate_subscription_recovery_plan(
        self,
        recurring_amount: float,
        plan_name: str,
        failed_attempts: int,
        last_failure_reason: str,
        customer_name: str,
        is_returning: bool
    ) -> AIReasoning:
        factors: List[DecisionFactor] = [
            DecisionFactor(
                title="Recurring Billing Context",
                description=f"Plan '{plan_name}' (₹{recurring_amount:,.2f}/cycle) failed on renewal. Reason: {last_failure_reason}.",
                impact="NEGATIVE",
                icon="refresh-cw"
            ),
            DecisionFactor(
                title="Attempt Lifecycle",
                description=f"Renewal attempt #{failed_attempts} of 3 maximum permissible cycles.",
                impact="NEUTRAL" if failed_attempts < 3 else "NEGATIVE",
                icon="clock"
            )
        ]

        if failed_attempts >= 3:
            recommended_action = InterventionType.CARD_UPDATE_REQUEST
            confidence = 0.95
            summary = "Maximum renewal retries reached. Triggering secure Payment Method Update email to prevent churn."
            expected_amount = recurring_amount
        elif "EXPIR" in (last_failure_reason or "").upper():
            recommended_action = InterventionType.CARD_UPDATE_REQUEST
            confidence = 0.92
            summary = "Card expired detected. Prompting subscriber to update card credentials."
            expected_amount = recurring_amount
        else:
            recommended_action = InterventionType.SUBSCRIPTION_COOLDOWN_RETRY
            confidence = 0.85
            summary = f"Scheduling 24-hour smart cooldown retry for subscription {plan_name}."
            expected_amount = recurring_amount

        return AIReasoning(
            summary=summary,
            confidence=confidence,
            factors=factors,
            root_cause_diagnosis=FailureCategory.SUBSCRIPTION_RENEWAL_FAILURE.value,
            expected_recovery_amount=expected_amount,
            recommended_intervention=recommended_action
        )

    async def generate_receivable_chasing_plan(
        self,
        invoice_amount: float,
        overdue_days: int,
        contact_count: int,
        customer_name: str,
        risk_score: float
    ) -> AIReasoning:
        factors: List[DecisionFactor] = [
            DecisionFactor(
                title="B2B Aging Analysis",
                description=f"Invoice is {overdue_days} days overdue with {contact_count} previous touches.",
                impact="NEGATIVE" if overdue_days > 15 else "NEUTRAL",
                icon="calendar"
            ),
            DecisionFactor(
                title="Commercial Value",
                description=f"Outstanding receivables of ₹{invoice_amount:,.2f} at risk.",
                impact="POSITIVE" if risk_score < 0.4 else "NEGATIVE",
                icon="file-text"
            )
        ]

        if overdue_days > 30 or invoice_amount > 25000.0 or risk_score >= 0.70:
            recommended_action = InterventionType.HUMAN_ESCALATION
            confidence = 0.92
            summary = f"Invoice overdue by {overdue_days} days (₹{invoice_amount:,.2f}). Escalated to Finance Controller."
            expected_amount = invoice_amount
        elif overdue_days > 14:
            recommended_action = InterventionType.CHASER_NOTIFICATION
            confidence = 0.88
            summary = "Sending Formal Chaser with structured Statement of Account and UPI/NEFT link."
            expected_amount = invoice_amount
        else:
            recommended_action = InterventionType.CHASER_NOTIFICATION
            confidence = 0.84
            summary = "Sending Courteous Reminder Notification for invoice payment."
            expected_amount = invoice_amount

        return AIReasoning(
            summary=summary,
            confidence=confidence,
            factors=factors,
            root_cause_diagnosis=FailureCategory.RECEIVABLE_OVERDUE.value,
            expected_recovery_amount=expected_amount,
            recommended_intervention=recommended_action
        )

    async def generate_mandate_sequence_plan(
        self,
        scheduled_amount: float,
        attempt_number: int,
        mandate_type: str,
        failure_code: str,
        customer_name: str
    ) -> AIReasoning:
        factors: List[DecisionFactor] = [
            DecisionFactor(
                title="Mandate Clearing Diagnostics",
                description=f"{mandate_type} clearing presentation failed with code '{failure_code}'.",
                impact="NEGATIVE",
                icon="credit-card"
            ),
            DecisionFactor(
                title="Clearing Cycle Alignment",
                description=f"Attempt {attempt_number} of 3. Re-presenting during next national interbank clearing window.",
                impact="POSITIVE" if attempt_number < 3 else "NEGATIVE",
                icon="repeat"
            )
        ]

        if attempt_number >= 3:
            recommended_action = InterventionType.STOP
            confidence = 0.97
            summary = "Mandate reached RBI 3-attempt ceiling. Halting automated debit presentation."
            expected_amount = 0.0
        else:
            recommended_action = InterventionType.MANDATE_STEP_SEQUENCE
            confidence = 0.89
            summary = f"Sequencing automated mandate debit retry #{attempt_number + 1} with 48h clearing offset."
            expected_amount = scheduled_amount

        return AIReasoning(
            summary=summary,
            confidence=confidence,
            factors=factors,
            root_cause_diagnosis=FailureCategory.MANDATE_CLEARING_ERROR.value,
            expected_recovery_amount=expected_amount,
            recommended_intervention=recommended_action
        )

    async def generate_voice_recovery_plan(
        self,
        amount: float,
        failure_reason: str,
        language: str,
        customer_name: str,
        order_reference: str
    ) -> tuple[AIReasoning, str]:
        factors: List[DecisionFactor] = [
            DecisionFactor(
                title="High-Touch Recovery Eligibility",
                description="Cart or payment failed at authentication; customer qualifies for conversational voice outreach.",
                impact="POSITIVE",
                icon="phone-call"
            ),
            DecisionFactor(
                title="Multilingual Natural Script",
                description=f"Generated culturally empathetic {language.capitalize()} script with Razorpay 1-click retry.",
                impact="POSITIVE",
                icon="message-circle"
            )
        ]

        if language.upper() == "HINGLISH":
            script = (
                f"Namaste {customer_name}! Main Acrobatics Apparel ki taraf se automated recovery assistant bol raha hoon. "
                f"Aapka order {order_reference} ka payment ₹{amount:,.2f} bank server issue ki wajah se complete nahi ho paya tha. "
                f"Humne aapke phone par ek secure 1-click Razorpay payment link SMS kar diya hai. "
                f"Kya aap safe retry karna chahenge?"
            )
        else:
            script = (
                f"Hello {customer_name}! This is the automated recovery assistant from Acrobatics Apparel. "
                f"Your payment of ₹{amount:,.2f} for order {order_reference} encountered a temporary decline ({failure_reason}). "
                f"We have dispatched a secure 1-click Razorpay payment link to your mobile number for safe completion."
            )

        reasoning = AIReasoning(
            summary=f"Synthesized contextual {language.capitalize()} voice recovery outreach with SMS payment link payload.",
            confidence=0.91,
            factors=factors,
            root_cause_diagnosis=FailureCategory.VOICE_OUTREACH_REQUIRED.value,
            expected_recovery_amount=amount,
            recommended_intervention=InterventionType.HINGLISH_VOICE_OUTREACH
        )
        return reasoning, script

    async def generate_promise_to_pay_plan(
        self,
        promised_amount: float,
        overdue_days: int,
        previous_breaches_count: int,
        customer_name: str
    ) -> AIReasoning:
        factors: List[DecisionFactor] = [
            DecisionFactor(
                title="Promise Reliability Scoring",
                description=f"Debtor committed to pay ₹{promised_amount:,.2f}. Previous broken promises: {previous_breaches_count}.",
                impact="POSITIVE" if previous_breaches_count == 0 else "NEGATIVE",
                icon="shield"
            ),
            DecisionFactor(
                title="Aging & Grace Window",
                description=f"Account is {overdue_days} days overdue with a 24-hour grace tracking window.",
                impact="NEUTRAL",
                icon="clock"
            )
        ]

        if previous_breaches_count >= 2:
            recommended_action = InterventionType.PROMISE_BREACH_ESCALATE
            confidence = 0.94
            summary = f"Debtor has {previous_breaches_count} previous broken promises. Automated extension revoked; escalated to collections manager."
            expected_amount = promised_amount
        else:
            recommended_action = InterventionType.PROMISE_PRE_DUE_REMINDER
            confidence = 0.88
            summary = "Active promise-to-pay registered. Scheduled friendly 24h pre-due reminder and settlement verification."
            expected_amount = promised_amount

        return AIReasoning(
            summary=summary,
            confidence=confidence,
            factors=factors,
            root_cause_diagnosis=FailureCategory.PROMISE_BREACHED.value if previous_breaches_count >= 2 else FailureCategory.RECEIVABLE_OVERDUE.value,
            expected_recovery_amount=expected_amount,
            recommended_intervention=recommended_action
        )
