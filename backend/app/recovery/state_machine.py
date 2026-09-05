from typing import Dict, Set
from app.core.enums import RecoveryState

class RecoveryStateMachine:
    """
    Strict state transition rules for payment recovery lifecycle.
    """
    
    ALLOWED_TRANSITIONS: Dict[RecoveryState, Set[RecoveryState]] = {
        RecoveryState.PAYMENT_FAILED: {
            RecoveryState.RECOVERY_ELIGIBLE,
            RecoveryState.STOPPED,
            RecoveryState.ESCALATED
        },
        RecoveryState.RECOVERY_ELIGIBLE: {
            RecoveryState.RECOVERY_PLANNED,
            RecoveryState.ESCALATED,
            RecoveryState.STOPPED
        },
        RecoveryState.RECOVERY_PLANNED: {
            RecoveryState.POLICY_APPROVED,
            RecoveryState.ESCALATED,
            RecoveryState.STOPPED
        },
        RecoveryState.POLICY_APPROVED: {
            RecoveryState.ACTION_EXECUTING,
            RecoveryState.STOPPED
        },
        RecoveryState.ACTION_EXECUTING: {
            RecoveryState.AWAITING_PAYMENT_EVENT,
            RecoveryState.STOPPED,
            RecoveryState.RECOVERED
        },
        RecoveryState.AWAITING_PAYMENT_EVENT: {
            RecoveryState.RECOVERED,
            RecoveryState.PAYMENT_FAILED,
            RecoveryState.STOPPED
        },
        RecoveryState.ESCALATED: {
            RecoveryState.POLICY_APPROVED,
            RecoveryState.ACTION_EXECUTING,
            RecoveryState.STOPPED
        },
        RecoveryState.RECOVERED: set(),  # Terminal state
        RecoveryState.STOPPED: set()     # Terminal state
    }

    @classmethod
    def can_transition(cls, from_state: RecoveryState, to_state: RecoveryState) -> bool:
        if from_state == to_state:
            return True
        return to_state in cls.ALLOWED_TRANSITIONS.get(from_state, set())

    @classmethod
    def validate_transition(cls, from_state: RecoveryState, to_state: RecoveryState):
        if not cls.can_transition(from_state, to_state):
            raise ValueError(f"Illegal recovery state transition from {from_state.value} to {to_state.value}")
