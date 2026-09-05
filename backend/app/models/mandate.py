from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Mandate(Base):
    __tablename__ = "mandates"

    id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    mandate_token = Column(String(128), unique=True, index=True, nullable=False)
    mandate_type = Column(String(32), default="UPI_AUTOPAY")  # UPI_AUTOPAY, E_MANDATE, NACH
    max_amount = Column(Float, nullable=False)
    scheduled_amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    frequency = Column(String(32), default="MONTHLY")  # AS_PRESENTED, MONTHLY, QUARTERLY
    status = Column(String(32), default="SEQUENCED", index=True)  # ACTIVE, PAUSED, SEQUENCED, STOPPED, CAPTURED
    attempt_number = Column(Integer, default=1)
    max_attempts = Column(Integer, default=3)  # Configurable retry limit
    failure_code = Column(String(64), default="ISSUER_CLEARING_UNAVAILABLE")
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer")
    merchant = relationship("Merchant")
