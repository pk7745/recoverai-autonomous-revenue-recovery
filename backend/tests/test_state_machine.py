import pytest
from app.recovery.state_machine import RecoveryStateMachine
from app.core.enums import RecoveryState

def test_legal_state_transitions():
    # PAYMENT_FAILED -> RECOVERY_ELIGIBLE
    assert RecoveryStateMachine.can_transition(RecoveryState.PAYMENT_FAILED, RecoveryState.RECOVERY_ELIGIBLE)
    # RECOVERY_ELIGIBLE -> RECOVERY_PLANNED
    assert RecoveryStateMachine.can_transition(RecoveryState.RECOVERY_ELIGIBLE, RecoveryState.RECOVERY_PLANNED)
    # RECOVERY_PLANNED -> POLICY_APPROVED
    assert RecoveryStateMachine.can_transition(RecoveryState.RECOVERY_PLANNED, RecoveryState.POLICY_APPROVED)
    # POLICY_APPROVED -> ACTION_EXECUTING
    assert RecoveryStateMachine.can_transition(RecoveryState.POLICY_APPROVED, RecoveryState.ACTION_EXECUTING)
    # ACTION_EXECUTING -> AWAITING_PAYMENT_EVENT
    assert RecoveryStateMachine.can_transition(RecoveryState.ACTION_EXECUTING, RecoveryState.AWAITING_PAYMENT_EVENT)
    # AWAITING_PAYMENT_EVENT -> RECOVERED
    assert RecoveryStateMachine.can_transition(RecoveryState.AWAITING_PAYMENT_EVENT, RecoveryState.RECOVERED)

def test_illegal_state_transitions():
    # Terminal RECOVERED cannot transition back to executing or failed
    assert not RecoveryStateMachine.can_transition(RecoveryState.RECOVERED, RecoveryState.ACTION_EXECUTING)
    assert not RecoveryStateMachine.can_transition(RecoveryState.RECOVERED, RecoveryState.PAYMENT_FAILED)
    
    with pytest.raises(ValueError):
        RecoveryStateMachine.validate_transition(RecoveryState.RECOVERED, RecoveryState.PAYMENT_FAILED)
