from typing import Dict, Any, Tuple
from app.core.enums import RiskTier, FailureCategory

class RiskEngine:
    """
    Evaluates multi-factor transaction risk based on failure patterns, customer credibility,
    amount velocity, and anomaly indicators.
    """
    
    @staticmethod
    def evaluate_risk(
        amount: float,
        failure_category: FailureCategory,
        customer_successful_payments: int,
        customer_failed_payments: int,
        attempts_count: int,
        is_returning: bool
    ) -> Tuple[float, RiskTier, Dict[str, Any]]:
        base_score = 0.10
        risk_flags = []
        
        # 1. Failure category inherent risk
        if failure_category == FailureCategory.SUSPICIOUS_FRAUD:
            base_score += 0.65
            risk_flags.append("Suspected fraud / stolen credential trigger")
        elif failure_category == FailureCategory.AUTHENTICATION_FAILURE:
            base_score += 0.15
            risk_flags.append("3DS OTP / Customer authentication failure")
        elif failure_category == FailureCategory.TEMPORARY_ISSUER_DECLINE:
            base_score += 0.05
            risk_flags.append("Temporary issuer gateway decline (Low risk)")
        elif failure_category == FailureCategory.INSUFFICIENT_FUNDS:
            base_score += 0.10
            risk_flags.append("Insufficient account funds")
            
        # 2. Transaction Amount exposure
        if amount >= 25000.0:
            base_score += 0.25
            risk_flags.append("High value transaction (>= ₹25,000)")
        elif amount >= 10000.0:
            base_score += 0.15
            risk_flags.append("Elevated value transaction (>= ₹10,000)")
            
        # 3. Customer payment credibility
        if not is_returning or customer_successful_payments == 0:
            base_score += 0.15
            risk_flags.append("First-time customer (No successful history)")
        else:
            success_ratio = customer_successful_payments / max(1, (customer_successful_payments + customer_failed_payments))
            if success_ratio > 0.8:
                base_score -= 0.15
                risk_flags.append(f"Highly reputable customer ({customer_successful_payments} prior successes)")
            elif success_ratio < 0.3:
                base_score += 0.20
                risk_flags.append("Poor historical payment success ratio (<30%)")
                
        # 4. Attempt velocity
        if attempts_count >= 3:
            base_score += 0.25
            risk_flags.append(f"High attempt count ({attempts_count} prior attempts)")
            
        # Clamp score between 0.01 and 0.99
        risk_score = round(max(0.01, min(0.99, base_score)), 3)
        
        # Determine risk tier
        if risk_score >= 0.75:
            risk_tier = RiskTier.CRITICAL
        elif risk_score >= 0.50:
            risk_tier = RiskTier.HIGH
        elif risk_score >= 0.25:
            risk_tier = RiskTier.MEDIUM
        else:
            risk_tier = RiskTier.LOW
            
        return risk_score, risk_tier, {
            "score": risk_score,
            "tier": risk_tier,
            "flags": risk_flags
        }
