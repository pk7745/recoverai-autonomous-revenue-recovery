from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=False, index=True)
    email = Column(String(128), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    hashed_password = Column(String(256), nullable=False)
    role = Column(String(32), default="OPERATIONS_AGENT", nullable=False)  # MERCHANT_ADMIN, OPERATIONS_AGENT
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    merchant = relationship("Merchant")
