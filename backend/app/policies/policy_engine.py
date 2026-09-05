from typing import List, Dict, Any, Optional
from app.core.enums import InterventionType, PolicyResultStatus, RiskTier, RecoveryType
from app.schemas.recovery import PolicyCheckItem, PolicyEvaluationResult

class PolicyEngine:
    """
    Deterministic Merchant Policy Enforcement Engine.
    Guarantees that AI recommendations never bypass hard business and risk guardrails
    across all seven recovery capabilities: Payment, Checkout, Subscription, Receivables,
    Mandates, Voice Recovery, and Promise-to-Pay.
    """

    @staticmethod
    def evaluate(
        recommended_action: InterventionType,
        amount: float,
        attempts_count: int,
        risk_score: float,
        is_returning_customer: bool,
        autonomous_limit: float = 5000.0,
        max_retries: int = 2,
        risk_threshold: float = 0.70,
        is_already_recovered: bool = False,
        recovery_type: RecoveryType = RecoveryType.PAYMENT,
        cooldown_passed: bool = True,
        is_within_contact_hours: bool = True,
        overdue_days: int = 0,
        previous_breaches_count: int = 0
    ) -> PolicyEvaluationResult:
        checks: List[PolicyCheckItem] = []
        
        # Rule 1: Stopping rule - Already Recovered / Settled
        if is_already_recovered:
            checks.append(PolicyCheckItem(
                rule_name="ALREADY_RECOVERED_CHECK",
                rule_description="Prevent duplicate recovery workflows on settled transactions",
                passed=False,
                details="Record is already in RECOVERED/CAPTURED/PAID state."
            ))
            return PolicyEvaluationResult(
                status=PolicyResultStatus.STOPPED,
                allowed_action=InterventionType.NO_ACTION,
                requires_human_approval=False,
                checks=checks,
                rejection_reason="Payment or debt is already settled. Zero action permitted to avoid double charges."
            )
        else:
            checks.append(PolicyCheckItem(
                rule_name="ALREADY_RECOVERED_CHECK",
                rule_description="Prevent duplicate recovery workflows on settled transactions",
                passed=True,
                details="Record is unsettled and eligible for evaluation."
            ))

        # Program-Specific Rule Checks

        # Mandate Specific: Configured Mandate Max Retries Rule (Default: 3 Attempts)
        if recovery_type == RecoveryType.MANDATE:
            mandate_ceiling = max_retries or 3
            if attempts_count >= mandate_ceiling:
                checks.append(PolicyCheckItem(
                    rule_name="CONFIGURED_MANDATE_RETRY_CEILING",
                    rule_description=f"Mandate presentation capped at configured limit of {mandate_ceiling} attempts",
                    passed=False,
                    details=f"Current attempt {attempts_count} reached maximum configured clearing ceiling ({mandate_ceiling})."
                ))
                return PolicyEvaluationResult(
                    status=PolicyResultStatus.STOPPED,
                    allowed_action=InterventionType.STOP,
                    requires_human_approval=False,
                    checks=checks,
                    rejection_reason=f"Configured mandate attempt limit ({mandate_ceiling}) reached. Halting automated debit presentation."
                )
            else:
                checks.append(PolicyCheckItem(
                    rule_name="CONFIGURED_MANDATE_RETRY_CEILING",
                    rule_description=f"Mandate presentation capped at configured limit of {mandate_ceiling} attempts",
                    passed=True,
                    details=f"Attempt {attempts_count} is within allowable mandate presentation bounds ({mandate_ceiling})."
                ))

        # Voice Specific: Configured Operational Contact Window (09:00 - 20:00 IST)
        if recovery_type == RecoveryType.VOICE_RECOVERY:
            if not is_within_contact_hours:
                checks.append(PolicyCheckItem(
                    rule_name="OPERATIONAL_CONTACT_HOURS_GATE",
                    rule_description="Automated voice recovery permitted strictly during configured hours (09:00 - 20:00 IST)",
                    passed=False,
                    details="Current time is outside configured operational contact window. Voice call blocked."
                ))
                return PolicyEvaluationResult(
                    status=PolicyResultStatus.STOPPED,
                    allowed_action=InterventionType.PAYMENT_LINK,
                    requires_human_approval=False,
                    checks=checks,
                    rejection_reason="Outside configured contact window (09:00-20:00 IST). Switched to non-intrusive payment link."
                )
            else:
                checks.append(PolicyCheckItem(
                    rule_name="OPERATIONAL_CONTACT_HOURS_GATE",
                    rule_description="Automated voice recovery permitted strictly during configured hours (09:00 - 20:00 IST)",
                    passed=True,
                    details="Contact time is within legitimate operational window."
                ))

        # Promise-to-Pay Specific: Debtor Reliability and Repeat Breach Guard
        if recovery_type == RecoveryType.PROMISE_TO_PAY:
            if previous_breaches_count >= 2:
                checks.append(PolicyCheckItem(
                    rule_name="REPEAT_BREACH_GUARD",
                    rule_description="Debtors with >= 2 prior broken promises require human collection escalation",
                    passed=False,
                    details=f"Debtor has {previous_breaches_count} previous breached commitments."
                ))
                return PolicyEvaluationResult(
                    status=PolicyResultStatus.OVERRIDDEN_TO_ESCALATE,
                    allowed_action=InterventionType.HUMAN_ESCALATION,
                    requires_human_approval=True,
                    checks=checks,
                    rejection_reason=f"Debtor has {previous_breaches_count} prior broken promises. Automated extension denied; routed to manager."
                )
            else:
                checks.append(PolicyCheckItem(
                    rule_name="REPEAT_BREACH_GUARD",
                    rule_description="Debtor commitment track record verified",
                    passed=True,
                    details=f"Prior breaches ({previous_breaches_count}) within allowable tolerance."
                ))

        # Subscription Cooldown Rule
        if recovery_type == RecoveryType.SUBSCRIPTION and not cooldown_passed:
            checks.append(PolicyCheckItem(
                rule_name="SUBSCRIPTION_COOLDOWN_CHECK",
                rule_description="Minimum 24-hour cooldown enforced between subscription renewal retries",
                passed=False,
                details="Minimum 24h cooldown interval has not elapsed since last renewal attempt."
            ))
            return PolicyEvaluationResult(
                status=PolicyResultStatus.STOPPED,
                allowed_action=InterventionType.NO_ACTION,
                requires_human_approval=False,
                checks=checks,
                rejection_reason="Cooldown active. Retrying immediately violates issuer rate limits."
            )

        # Rule 2: Maximum Retry Limit
        effective_max_retries = max_retries
        if attempts_count > effective_max_retries:
            checks.append(PolicyCheckItem(
                rule_name="MAX_ATTEMPTS_LIMIT",
                rule_description=f"Automated recovery capped at {effective_max_retries} attempts",
                passed=False,
                details=f"Current attempt count ({attempts_count}) exceeds limit of {effective_max_retries}."
            ))
            return PolicyEvaluationResult(
                status=PolicyResultStatus.STOPPED,
                allowed_action=InterventionType.STOP,
                requires_human_approval=False,
                checks=checks,
                rejection_reason=f"Exceeded maximum autonomous retry limit ({effective_max_retries}). Halting workflow."
            )
        else:
            checks.append(PolicyCheckItem(
                rule_name="MAX_ATTEMPTS_LIMIT",
                rule_description=f"Automated recovery capped at {effective_max_retries} attempts",
                passed=True,
                details=f"Attempt {attempts_count} is within allowable limit ({effective_max_retries})."
            ))

        # Rule 3: High Risk / Fraud Containment
        if risk_score >= risk_threshold:
            checks.append(PolicyCheckItem(
                rule_name="RISK_SCORE_THRESHOLD",
                rule_description=f"Cases with risk score >= {risk_threshold:.2f} must not execute automatically",
                passed=False,
                details=f"Risk score ({risk_score:.2f}) exceeds risk threshold ({risk_threshold:.2f})."
            ))
            return PolicyEvaluationResult(
                status=PolicyResultStatus.OVERRIDDEN_TO_ESCALATE,
                allowed_action=InterventionType.HUMAN_ESCALATION,
                requires_human_approval=True,
                checks=checks,
                rejection_reason="High fraud/credit risk profile detected. Automated execution blocked for human ops review."
            )
        else:
            checks.append(PolicyCheckItem(
                rule_name="RISK_SCORE_THRESHOLD",
                rule_description=f"Cases with risk score >= {risk_threshold:.2f} must not execute automatically",
                passed=True,
                details=f"Risk score ({risk_score:.2f}) is safely below threshold ({risk_threshold:.2f})."
            ))

        # Rule 4: Autonomous Amount Ceiling
        effective_ceiling = autonomous_limit
        if recovery_type == RecoveryType.RECEIVABLE:
            effective_ceiling = max(autonomous_limit, 25000.0)  # B2B invoices allow up to 25k or merchant setting

        if amount > effective_ceiling:
            checks.append(PolicyCheckItem(
                rule_name="AUTONOMOUS_AMOUNT_CEILING",
                rule_description=f"Exposure > ₹{effective_ceiling:,.2f} requires human manager approval",
                passed=False,
                details=f"Amount ₹{amount:,.2f} exceeds merchant autonomous ceiling of ₹{effective_ceiling:,.2f}."
            ))
            return PolicyEvaluationResult(
                status=PolicyResultStatus.OVERRIDDEN_TO_ESCALATE,
                allowed_action=InterventionType.HUMAN_ESCALATION,
                requires_human_approval=True,
                checks=checks,
                rejection_reason=f"Amount ₹{amount:,.2f} exceeds autonomous limit ₹{effective_ceiling:,.2f}. Manual approval required."
            )
        else:
            checks.append(PolicyCheckItem(
                rule_name="AUTONOMOUS_AMOUNT_CEILING",
                rule_description=f"Exposure > ₹{effective_ceiling:,.2f} requires human manager approval",
                passed=True,
                details=f"Amount ₹{amount:,.2f} is within autonomous limit ₹{effective_ceiling:,.2f}."
            ))

        # Rule 5: New Customer Policy Bound
        if not is_returning_customer and attempts_count > 1 and recovery_type == RecoveryType.PAYMENT:
            checks.append(PolicyCheckItem(
                rule_name="NEW_CUSTOMER_LIMIT",
                rule_description="First-time customers are limited to 1 autonomous retry",
                passed=False,
                details="First-time customer attempt limit exceeded."
            ))
            return PolicyEvaluationResult(
                status=PolicyResultStatus.OVERRIDDEN_TO_ESCALATE,
                allowed_action=InterventionType.PAYMENT_LINK,
                requires_human_approval=False,
                checks=checks,
                rejection_reason="First-time customer retry limit reached. Switched from retry to smart payment link."
            )
        else:
            checks.append(PolicyCheckItem(
                rule_name="CUSTOMER_LOYALTY_STATUS",
                rule_description="Customer credibility tier verified",
                passed=True,
                details="Customer profile matches automated policy eligibility."
            ))

        # All checks passed
        return PolicyEvaluationResult(
            status=PolicyResultStatus.ALLOWED,
            allowed_action=recommended_action,
            requires_human_approval=False,
            checks=checks,
            rejection_reason=None
        )
