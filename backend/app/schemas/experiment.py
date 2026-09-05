from pydantic import BaseModel
from typing import Dict, Any, List

class StrategyMetrics(BaseModel):
    name: str
    total_transactions: int
    failed_transactions: int
    total_revenue_at_risk: float
    recovered_revenue: float
    recovery_rate: float
    unnecessary_retries: int
    human_escalations: int
    stopped_unsafe_actions: int
    average_attempts_per_recovery: float
    roi_multiple: float

class BenchmarkComparisonResponse(BaseModel):
    dataset_size: int
    baseline_strategy: StrategyMetrics
    recoverai_strategy: StrategyMetrics
    uplift_percentage: float
    additional_revenue_recovered: float
    wasteful_retries_prevented: int
    breakdown_by_category: Dict[str, Dict[str, Any]]
    run_timestamp: str
