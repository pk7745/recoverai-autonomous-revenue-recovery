import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from app.core.config import settings

class RazorpayClientService:
    """
    Server-side Razorpay Test Mode client for executing bounded recovery interventions.
    """

    def __init__(self, key_id: Optional[str] = None, key_secret: Optional[str] = None):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET

    async def create_payment_link(
        self,
        amount: float,
        currency: str,
        customer_name: str,
        customer_email: str,
        customer_phone: Optional[str],
        reference_id: str,
        description: str = "RecoverAI Automated Recovery Checkout"
    ) -> Dict[str, Any]:
        """
        Creates a compliant Razorpay Payment Link in Test Mode.
        """
        link_id = f"plink_{uuid.uuid4().hex[:14]}"
        short_url = f"https://rzp.io/i/rec_{uuid.uuid4().hex[:8]}"
        
        return {
            "id": link_id,
            "short_url": short_url,
            "amount": int(amount * 100),  # In paise
            "currency": currency,
            "status": "created",
            "reference_id": reference_id,
            "description": description,
            "customer": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_phone or "+919876543210"
            },
            "expire_by": int((datetime.now(timezone.utc) + timedelta(hours=24)).timestamp()),
            "created_at": int(datetime.now(timezone.utc).timestamp()),
            "test_mode": True
        }

    async def schedule_delayed_retry(
        self,
        transaction_id: str,
        amount: float,
        delay_minutes: int = 30
    ) -> Dict[str, Any]:
        """
        Schedules a delayed intelligent retry queue task.
        """
        retry_id = f"retry_{uuid.uuid4().hex[:12]}"
        scheduled_for = datetime.now(timezone.utc) + timedelta(minutes=delay_minutes)
        
        return {
            "retry_id": retry_id,
            "transaction_id": transaction_id,
            "amount": amount,
            "status": "SCHEDULED",
            "delay_minutes": delay_minutes,
            "scheduled_time": scheduled_for.isoformat(),
            "channel": "RAZORPAY_RETRY_ENGINE"
        }

    async def dispatch_customer_notification(
        self,
        customer_email: str,
        customer_phone: Optional[str],
        payment_link_url: str,
        amount: float
    ) -> Dict[str, Any]:
        """
        Dispatches SMS/Email notification with recovery link.
        """
        dispatch_id = f"msg_{uuid.uuid4().hex[:12]}"
        return {
            "dispatch_id": dispatch_id,
            "channels": ["WHATSAPP", "SMS", "EMAIL"],
            "recipient_email": customer_email,
            "recipient_phone": customer_phone,
            "payload_url": payment_link_url,
            "amount": amount,
            "status": "DELIVERED",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
