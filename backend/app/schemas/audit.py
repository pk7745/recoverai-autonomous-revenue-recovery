from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class AuditLogItem(BaseModel):
    id: str
    workflow_id: Optional[str] = None
    transaction_id: Optional[str] = None
    actor: str
    action: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

class SafetyOverviewResponse(BaseModel):
    total_blocked_actions: int
    total_stopped_workflows: int
    total_human_escalations: int
    total_duplicate_events_prevented: int
    total_fraud_anomalies_contained: int
    high_value_transactions_routed: int
    policy_violations_prevented: int
    safety_health_score: float  # e.g., 99.9%
