from sqlalchemy import Column, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class RecoveryWorkflow(Base):
    __tablename__ = "recovery_workflows"

    id = Column(String(64), primary_key=True, index=True)
    recovery_type = Column(String(32), default="PAYMENT", index=True)  # PAYMENT, CHECKOUT, SUBSCRIPTION, RECEIVABLE, MANDATE, PROMISE_TO_PAY, VOICE_RECOVERY
    reference_id = Column(String(64), nullable=True, index=True)  # Links to CheckoutSession, Subscription, Invoice, Mandate, PTP, Voice
    transaction_id = Column(String(64), ForeignKey("transactions.id"), nullable=True, unique=True, index=True)
    state = Column(String(32), default="PAYMENT_FAILED", index=True)
    risk_score = Column(Float, default=0.0)
    failure_category = Column(String(64), default="UNKNOWN")
    recommended_action = Column(String(64), default="NO_ACTION")
    execution_mode = Column(String(32), default="SIMULATED")  # SIMULATED, LIVE_TEST_MODE, EXECUTED, BLOCKED, ESCALATED
    ai_confidence = Column(Float, default=0.0)
    ai_reasoning = Column(JSON, nullable=True)  # List of factors, structured reasoning
    policy_evaluation = Column(JSON, nullable=True)  # Policy check results & status
    execution_payload = Column(JSON, nullable=True)  # Gateway response or payment link details
    recovered_amount = Column(Float, default=0.0)
    stopping_rule_triggered = Column(String(128), nullable=True)
    escalation_reason = Column(String(256), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    transaction = relationship("Transaction", back_populates="workflow")
    audit_logs = relationship("AuditLog", back_populates="workflow", cascade="all, delete-orphan")
