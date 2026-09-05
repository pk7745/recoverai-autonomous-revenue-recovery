from sqlalchemy import Column, String, Float, Integer, Boolean, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.core.database import Base

class VoiceRecoverySession(Base):
    __tablename__ = "voice_recovery_sessions"

    id = Column(String(64), primary_key=True, index=True)
    workflow_id = Column(String(64), nullable=True, index=True)
    merchant_id = Column(String(64), ForeignKey("merchants.id"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    phone_number = Column(String(32), nullable=False)
    language = Column(String(32), default="HINGLISH")  # HINGLISH, ENGLISH
    generated_script = Column(Text, nullable=False)
    audio_simulation_state = Column(JSON, nullable=True)  # Transcript, audio player events
    call_status = Column(String(32), default="SIMULATED_READY", index=True)  # SIMULATED_READY, CALL_INITIATED, CONNECTED, COMPLETED, FAILED
    detected_intent = Column(String(64), default="AGREED_TO_RETRY")  # AGREED_TO_RETRY, REQUESTED_LINK, DISPUTED_AMOUNT, CALLBACK_LATER
    payment_link_sent = Column(Boolean, default=False)
    duration_seconds = Column(Integer, default=45)
    execution_mode = Column(String(32), default="SIMULATED")  # SIMULATED, LIVE_VOICE_API
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer")
    merchant = relationship("Merchant")
