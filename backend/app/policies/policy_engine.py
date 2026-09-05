from typing import List, Dict, Any
from app.core.enums import InterventionType, PolicyResultStatus, RiskTier
from app.schemas.recovery import PolicyCheckItem, PolicyEvaluationResult

class PolicyEngine:
    """
    Deterministic Merchant Policy Enforcement Engine.
    Guarantees that AI recommendations never bypass hard business and risk guardrails.
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
        is_already_recovered: bool = False
    ) -> PolicyEvaluationResult:
        checks: List[PolicyCheckItem] = []
        
        # Rule 1: Stopping rule - Already Recovered
        if is_already_recovered:
            checks.append(PolicyCheckItem(
                rule_name="ALREADY_RECOVERED_CHECK",
                rule_description="Prevent duplicate recovery workflows on settled transactions",
                passed=False,
                details="Transaction is already in RECOVERED/CAPTURED state."
            ))
            return PolicyEvaluationResult(
                status=PolicyResultStatus.STOPPED,
                allowed_action=InterventionType.NO_ACTION,
                requires_human_approval=False,
                checks=checks,
                rejection_reason="Payment is already settled. Zero action permitted to avoid double charges."
            )
        else:
            checks.append(PolicyCheckItem(
                rule_name="ALREADY_RECOVERED_CHECK",
                rule_description="Prevent duplicate recovery workflows on settled transactions",
                passed=True,
                details="Transaction is unsettled and eligible for evaluation."
            ))

        # Rule 2: Maximum Retry Limit
        if attempts_count > max_retries:
            checks.append(PolicyCheckItem(
                rule_name="MAX_ATTEMPTS_LIMIT",
                rule_description=f"Automated recovery capped at {max_retries} attempts",
                passed=False,
                details=f"Current attempt count ({attempts_count}) exceeds limit of {max_retries}."
            ))
            return PolicyEvaluationResult(
                status=PolicyResultStatus.STOPPED,
                allowed_action=InterventionType.STOP,
                requires_human_approval=False,
                checks=checks,
                rejection_reason=f"Exceeded maximum autonomous retry limit ({max_retries}). Halting workflow."
            )
        else:
            checks.append(PolicyCheckItem(
                rule_name="MAX_ATTEMPTS_LIMIT",
                rule_description=f"Automated recovery capped at {max_retries} attempts",
                passed=True,
                details=f"Attempt {attempts_count} is within allowable limit ({max_retries})."
            ))

        # Rule 3: High Risk / Fraud Containment
        if risk_score >= risk_threshold:
            checks.append(PolicyCheckItem(
                rule_name="RISK_SCORE_THRESHOLD",
                rule_description=f"Transactions with risk score >= {risk_threshold:.2f} must not execute automatically",
                passed=False,
                details=f"Risk score ({risk_score:.2f}) exceeds risk threshold ({risk_threshold:.2f})."
            ))
            return PolicyEvaluationResult(
                status=PolicyResultStatus.OVERRIDDEN_TO_ESCALATE,
                allowed_action=InterventionType.HUMAN_ESCALATION,
                requires_human_approval=True,
                checks=checks,
                rejection_reason="High fraud risk profile detected. Automated execution blocked for human ops review."
            )
        else:
            checks.append(PolicyCheckItem(
                rule_name="RISK_SCORE_THRESHOLD",
                rule_description=f"Transactions with risk score >= {risk_threshold:.2f} must not execute automatically",
                passed=True,
                details=f"Risk score ({risk_score:.2f}) is safely below threshold ({risk_threshold:.2f})."
            ))

        # Rule 4: Autonomous Amount Ceiling
        if amount > autonomous_limit:
            checks.append(PolicyCheckItem(
                rule_name="AUTONOMOUS_AMOUNT_CEILING",
                rule_description=f"Transactions > ₹{autonomous_limit:,.2f} require human manager approval",
                passed=False,
                details=f"Amount ₹{amount:,.2f} exceeds merchant autonomous ceiling of ₹{autonomous_limit:,.2f}."
            ))
            return PolicyEvaluationResult(
                status=PolicyResultStatus.OVERRIDDEN_TO_ESCALATE,
                allowed_action=InterventionType.HUMAN_ESCALATION,
                requires_human_approval=True,
                checks=checks,
                rejection_reason=f"Amount ₹{amount:,.2f} exceeds autonomous limit ₹{autonomous_limit:,.2f}. Manual approval required."
            )
        else:
            checks.append(PolicyCheckItem(
                rule_name="AUTONOMOUS_AMOUNT_CEILING",
                rule_description=f"Transactions > ₹{autonomous_limit:,.2f} require human manager approval",
                passed=True,
                details=f"Amount ₹{amount:,.2f} is within autonomous limit ₹{autonomous_limit:,.2f}."
            ))

        # Rule 5: New Customer Policy Bound
        if not is_returning_customer and attempts_count > 1:
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
