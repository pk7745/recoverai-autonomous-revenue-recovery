from typing import Dict, Any, List, Optional
from app.core.enums import FailureCategory, InterventionType, RiskTier
from app.risk.risk_engine import RiskEngine

class RecoveryToolRegistry:
    """
    Formal registry of bounded tools accessible to the AI Recovery Agent.
    """

    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        return [
            {
                "name": "classify_failure",
                "description": "Analyzes raw gateway error code, sub-error message, and status to categorize the failure root cause.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "failure_code": {"type": "string"},
                        "failure_reason": {"type": "string"},
                        "payment_method": {"type": "string"}
                    },
                    "required": ["failure_code"]
                }
            },
            {
                "name": "evaluate_customer_health",
                "description": "Fetches customer historical payment success ratios, loyalty tier, and lifetime volume.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "customer_id": {"type": "string"}
                    },
                    "required": ["customer_id"]
                }
            },
            {
                "name": "calculate_risk_score",
                "description": "Evaluates risk factors including amount, velocity, failure category, and historical fraud flags.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "amount": {"type": "number"},
                        "failure_category": {"type": "string"},
                        "attempts_count": {"type": "integer"}
                    },
                    "required": ["amount", "failure_category", "attempts_count"]
                }
            },
            {
                "name": "determine_intervention",
                "description": "Selects optimal recovery strategy (DELAYED_RETRY, PAYMENT_LINK, ALTERNATIVE_PAYMENT, HUMAN_ESCALATION, STOP).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "failure_category": {"type": "string"},
                        "risk_tier": {"type": "string"},
                        "is_returning": {"type": "boolean"},
                        "attempts_count": {"type": "integer"}
                    },
                    "required": ["failure_category", "risk_tier"]
                }
            }
        ]

    @classmethod
    def normalize_failure_category(cls, val: Any) -> FailureCategory:
        """
        Canonical normalizer that safely converts any string, enum, or raw code
        into a valid FailureCategory member, defaulting to UNKNOWN for unrecognized values.
        """
        if isinstance(val, FailureCategory):
            return val
        if not val or not isinstance(val, str):
            return FailureCategory.UNKNOWN

        cleaned = val.strip().upper()
        # Direct enum value match
        for member in FailureCategory:
            if cleaned == member.value or cleaned == member.name:
                return member

        # Gateway code canonical mapping
        if any(w in cleaned for w in ["AUTH_FAILED", "OTP", "3DS", "AUTHENTICATION", "ABANDONED"]):
            return FailureCategory.AUTHENTICATION_FAILURE
        elif any(w in cleaned for w in ["FRAUD", "STOLEN", "RESTRICTED", "RISK_DECLINE", "SUSPICIOUS"]):
            return FailureCategory.SUSPICIOUS_FRAUD
        elif any(w in cleaned for w in ["GATEWAY_TIMEOUT", "TIMEOUT", "NETWORK_ERROR", "TIMEOUT_ERROR"]):
            return FailureCategory.NETWORK_TIMEOUT
        elif any(w in cleaned for w in ["INSUFFICIENT_FUNDS", "LOW_BALANCE", "FUNDS"]):
            return FailureCategory.INSUFFICIENT_FUNDS
        elif any(w in cleaned for w in ["EXPIRED", "CARD_EXPIRED"]):
            return FailureCategory.EXPIRED_CARD
        elif any(w in cleaned for w in ["UNSUPPORTED_METHOD", "METHOD_NOT_ALLOWED", "INVALID_METHOD"]):
            return FailureCategory.UNSUPPORTED_METHOD
        elif any(w in cleaned for w in ["ISSUER_DOWN", "BANK_DOWNTIME", "TEMPORARY", "TRY_AGAIN", "SYSTEM_ERROR", "GATEWAY_ERROR"]):
            return FailureCategory.TEMPORARY_ISSUER_DECLINE
        else:
            return FailureCategory.UNKNOWN

    @classmethod
    def classify_failure(cls, failure_code: str, failure_reason: str, payment_method: str = "card") -> FailureCategory:
        code_upper = (failure_code or "").upper()
        reason_upper = (failure_reason or "").upper()

        combined = f"{code_upper} {reason_upper}"
        normalized = cls.normalize_failure_category(combined)
        if normalized != FailureCategory.UNKNOWN:
            return normalized
        elif code_upper:
            norm_code = cls.normalize_failure_category(code_upper)
            if norm_code != FailureCategory.UNKNOWN:
                return norm_code

        return FailureCategory.TEMPORARY_ISSUER_DECLINE
