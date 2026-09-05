from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.core.enums import (
    PaymentStatus,
    FailureCategory,
    RecoveryState,
    InterventionType,
    PolicyResultStatus,
    RiskTier
)
from app.agents.tools import RecoveryToolRegistry

class DecisionFactor(BaseModel):
    title: str
    description: str
    impact: str  # POSITIVE, NEGATIVE, NEUTRAL
    icon: Optional[str] = None

class AIReasoning(BaseModel):
    summary: str
    confidence: float
    factors: List[DecisionFactor]
    root_cause_diagnosis: str
    expected_recovery_amount: float
    recommended_intervention: InterventionType

class PolicyCheckItem(BaseModel):
    rule_name: str
    rule_description: str
    passed: bool
    details: str

class PolicyEvaluationResult(BaseModel):
    status: PolicyResultStatus
    allowed_action: InterventionType
    requires_human_approval: bool
    checks: List[PolicyCheckItem]
    rejection_reason: Optional[str] = None

class CustomerSummary(BaseModel):
    id: str
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    total_successful_payments: int
    total_failed_payments: int
    is_returning: bool
    risk_tier: RiskTier

class TransactionSummary(BaseModel):
    id: str
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    amount: float
    currency: str
    status: PaymentStatus
    failure_code: Optional[str] = None
    failure_reason: Optional[str] = None
    payment_method: Optional[str] = None
    attempts_count: int
    created_at: datetime
    customer: Optional[CustomerSummary] = None

class RecoveryWorkflowResponse(BaseModel):
    id: str
    recovery_type: Optional[str] = "PAYMENT"
    reference_id: Optional[str] = None
    transaction_id: Optional[str] = None
    state: RecoveryState
    risk_score: float
    failure_category: FailureCategory
    recommended_action: InterventionType
    execution_mode: Optional[str] = "SIMULATED"
    ai_confidence: float
    ai_reasoning: Optional[Dict[str, Any]] = None
    policy_evaluation: Optional[Dict[str, Any]] = None
    execution_payload: Optional[Dict[str, Any]] = None
    recovered_amount: float
    stopping_rule_triggered: Optional[str] = None
    escalation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    transaction: Optional[TransactionSummary] = None

    @field_validator('failure_category', mode='before')
    @classmethod
    def validate_failure_category(cls, v: Any) -> FailureCategory:
        return RecoveryToolRegistry.normalize_failure_category(v)

class RecoveryPlanRequest(BaseModel):
    force_recalculate: bool = False

class ManualApprovalRequest(BaseModel):
    notes: Optional[str] = None
    action_override: Optional[InterventionType] = None
