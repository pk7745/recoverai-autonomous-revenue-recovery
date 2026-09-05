from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    plan_id = Column(String(64), nullable=False)
    plan_name = Column(String(128), nullable=False)
    recurring_amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    billing_interval = Column(String(32), default="monthly")  # weekly, monthly, quarterly, yearly
    status = Column(String(32), default="PAST_DUE", index=True)  # ACTIVE, PAST_DUE, RECOVERED, HALTED, CANCELLED
    failed_attempts = Column(Integer, default=1)
    max_retries = Column(Integer, default=3)
    last_failure_reason = Column(Text, nullable=True)
    cooldown_hours = Column(Integer, default=24)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer")
    merchant = relationship("Merchant")
