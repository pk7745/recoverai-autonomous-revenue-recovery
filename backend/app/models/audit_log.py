from sqlalchemy import Column, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    workflow_id = Column(String(64), ForeignKey("recovery_workflows.id"), nullable=True, index=True)
    transaction_id = Column(String(64), ForeignKey("transactions.id"), nullable=True, index=True)
    actor = Column(String(64), nullable=False)  # SYSTEM_AGENT, POLICY_ENGINE, RISK_ENGINE, MERCHANT_ADMIN, RAZORPAY_WEBHOOK
    action = Column(String(64), nullable=False)  # DIAGNOSED, POLICY_EVALUATED, EXECUTED, WEBHOOK_PROCESSED, STOPPED
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    transaction = relationship("Transaction", back_populates="audit_logs")
    workflow = relationship("RecoveryWorkflow", back_populates="audit_logs")
