from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class ReceivableInvoice(Base):
    __tablename__ = "receivable_invoices"

    id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    invoice_number = Column(String(64), unique=True, index=True, nullable=False)
    invoice_amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    issue_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    due_date = Column(DateTime(timezone=True), nullable=False)
    overdue_days = Column(Integer, default=0)
    chasing_stage = Column(String(64), default="GENTLE_REMINDER")  # GENTLE_REMINDER, FORMAL_FOLLOWUP, EXECUTIVE_ESCALATION
    status = Column(String(32), default="OUTSTANDING", index=True)  # OUTSTANDING, PROMISED, COLLECTED, WRITTEN_OFF
    last_contact_at = Column(DateTime(timezone=True), nullable=True)
    contact_count = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer")
    merchant = relationship("Merchant")
