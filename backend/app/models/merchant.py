from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    api_key_id = Column(String(64), nullable=False)
    webhook_secret = Column(String(128), nullable=False)
    autonomous_limit = Column(Float, default=5000.0)  # Max INR for autonomous actions
    max_retries = Column(Integer, default=2)
    min_retry_interval_mins = Column(Integer, default=30)
    risk_threshold = Column(Float, default=0.70)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    transactions = relationship("Transaction", back_populates="merchant", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="merchant", cascade="all, delete-orphan")
