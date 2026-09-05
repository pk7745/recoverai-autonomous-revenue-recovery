from pydantic import BaseModel, Field
from typing import Optional

class MerchantPolicyResponse(BaseModel):
    merchant_id: str
    merchant_name: str
    autonomous_limit: float
    max_retries: int
    min_retry_interval_mins: int
    risk_threshold: float

class UpdateMerchantPolicyRequest(BaseModel):
    autonomous_limit: Optional[float] = Field(None, ge=100.0, le=100000.0)
    max_retries: Optional[int] = Field(None, ge=1, le=5)
    min_retry_interval_mins: Optional[int] = Field(None, ge=5, le=1440)
    risk_threshold: Optional[float] = Field(None, ge=0.1, le=1.0)
