from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class MetricSummary(BaseModel):
    total_revenue_processed: float
    revenue_at_risk: float
    recovered_revenue: float
    recovery_rate: float
    total_transactions: int
    failed_transactions: int
    active_recovery_workflows: int
    automatic_recovery_count: int
    human_escalations_count: int
    stopped_actions_count: int
    average_recovery_time_seconds: float
    ai_automation_rate: float
    safety_health_score: float = 99.9
    prevented_loss_amount: float = 0.0

class TimeSeriesPoint(BaseModel):
    timestamp: str
    date_label: str
    failed_amount: float
    recovered_amount: float
    recovery_rate: float

class ActivityFeedItem(BaseModel):
    id: str
    workflow_id: str
    transaction_id: str
    amount: float
    action_type: str
    state: str
    reason: str
    timestamp: datetime
    customer_name: Optional[str] = None
    payment_method: Optional[str] = None

class DashboardOverviewResponse(BaseModel):
    metrics: MetricSummary
    timeseries: List[TimeSeriesPoint]
    activity_feed: List[ActivityFeedItem]
    recovery_by_intervention: Dict[str, Dict[str, Any]]
    recovery_by_failure_category: Dict[str, Dict[str, Any]]
