from pydantic import BaseModel
from typing import Dict, Any, Optional

class RazorpayWebhookPayload(BaseModel):
    event: str
    account_id: Optional[str] = None
    event_id: Optional[str] = None
    contains: Optional[list] = None
    payload: Dict[str, Any]
    created_at: Optional[int] = None

class WebhookResponse(BaseModel):
    status: str
    message: str
    event_id: str
    duplicate: bool
    action_taken: Optional[str] = None
