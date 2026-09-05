from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    razorpay_payment_id = Column(String(64), nullable=True, index=True)
    razorpay_order_id = Column(String(64), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    status = Column(String(32), default="PAYMENT_PENDING", index=True)
    failure_code = Column(String(64), nullable=True)
    failure_reason = Column(Text, nullable=True)
    payment_method = Column(String(32), nullable=True)  # card, upi, netbanking, wallet
    attempts_count = Column(Integer, default=1)
    metadata_info = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    merchant = relationship("Merchant", back_populates="transactions")
    customer = relationship("Customer", back_populates="transactions")
    workflow = relationship("RecoveryWorkflow", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="transaction", cascade="all, delete-orphan")
