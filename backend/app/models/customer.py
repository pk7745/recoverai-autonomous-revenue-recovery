from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=False, index=True)
    email = Column(String(128), nullable=False)
    phone = Column(String(32), nullable=True)
    name = Column(String(128), nullable=True)
    total_successful_payments = Column(Integer, default=0)
    total_failed_payments = Column(Integer, default=0)
    is_returning = Column(Boolean, default=False)
    risk_tier = Column(String(32), default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    merchant = relationship("Merchant", back_populates="customers")
    transactions = relationship("Transaction", back_populates="customer")
