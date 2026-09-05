from sqlalchemy import Column, String, Boolean, DateTime, JSON
from datetime import datetime, timezone
from app.core.database import Base

class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String(64), primary_key=True, index=True)
    razorpay_event_id = Column(String(64), unique=True, index=True, nullable=False)
    event_type = Column(String(64), nullable=False)
    payload_hash = Column(String(64), index=True, nullable=False)
    payload = Column(JSON, nullable=False)
    signature = Column(String(128), nullable=True)
    is_duplicate = Column(Boolean, default=False)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
