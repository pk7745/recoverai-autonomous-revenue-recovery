from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class PromiseToPay(Base):
    __tablename__ = "promises_to_pay"

    id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    reference_type = Column(String(32), default="INVOICE")  # INVOICE, SUBSCRIPTION, TRANSACTION, CHECKOUT
    reference_id = Column(String(64), nullable=False, index=True)
    promised_amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    promised_date = Column(DateTime(timezone=True), nullable=False)
    grace_period_hours = Column(Integer, default=24)
    status = Column(String(32), default="ACTIVE", index=True)  # ACTIVE, FULFILLED, BREACHED, ESCALATED
    reminder_sent_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    fulfilled_at = Column(DateTime(timezone=True), nullable=True)
    breached_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer")
    merchant = relationship("Merchant")
