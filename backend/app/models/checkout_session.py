from sqlalchemy import Column, String, Float, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class CheckoutSession(Base):
    __tablename__ = "checkout_sessions"

    id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    cart_value = Column(Float, nullable=False)
    currency = Column(String(8), default="INR")
    items_count = Column(Integer, default=1)
    items_summary = Column(Text, nullable=True)
    exit_step = Column(String(64), default="PAYMENT_STEP")  # CART, ADDRESS_STEP, PAYMENT_STEP, OTP_STEP
    detected_friction = Column(String(128), default="CUSTOMER_DROPOFF")
    recovery_status = Column(String(32), default="ABANDONED", index=True)  # ABANDONED, RECOVERY_INITIATED, RECOVERED, EXPIRED
    recovery_link_url = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer")
    merchant = relationship("Merchant")
