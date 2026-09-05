import pytest
from app.policies.policy_engine import PolicyEngine
from app.core.enums import InterventionType, PolicyResultStatus

def test_policy_allows_normal_low_value_transaction():
    result = PolicyEngine.evaluate(
        recommended_action=InterventionType.DELAYED_RETRY,
        amount=4999.0,
        attempts_count=1,
        risk_score=0.20,
        is_returning_customer=True,
        autonomous_limit=5000.0,
        max_retries=2,
        risk_threshold=0.70
    )
    assert result.status == PolicyResultStatus.ALLOWED
    assert result.allowed_action == InterventionType.DELAYED_RETRY
    assert result.requires_human_approval is False

def test_policy_blocks_amount_exceeding_autonomous_limit():
    result = PolicyEngine.evaluate(
        recommended_action=InterventionType.DELAYED_RETRY,
        amount=12500.0,
        attempts_count=1,
        risk_score=0.25,
        is_returning_customer=True,
        autonomous_limit=5000.0
    )
    assert result.status == PolicyResultStatus.OVERRIDDEN_TO_ESCALATE
    assert result.allowed_action == InterventionType.HUMAN_ESCALATION
    assert result.requires_human_approval is True
    assert "exceeds autonomous limit" in result.rejection_reason

def test_policy_blocks_high_risk_transaction():
    result = PolicyEngine.evaluate(
        recommended_action=InterventionType.PAYMENT_LINK,
        amount=2500.0,
        attempts_count=1,
        risk_score=0.85,
        is_returning_customer=False,
        risk_threshold=0.70
    )
    assert result.status == PolicyResultStatus.OVERRIDDEN_TO_ESCALATE
    assert result.allowed_action == InterventionType.HUMAN_ESCALATION
    assert result.requires_human_approval is True

def test_policy_stops_on_max_attempts():
    result = PolicyEngine.evaluate(
        recommended_action=InterventionType.DELAYED_RETRY,
        amount=3000.0,
        attempts_count=3,
        risk_score=0.30,
        is_returning_customer=True,
        max_retries=2
    )
    assert result.status == PolicyResultStatus.STOPPED
    assert result.allowed_action == InterventionType.STOP

def test_policy_stops_if_already_recovered():
    result = PolicyEngine.evaluate(
        recommended_action=InterventionType.DELAYED_RETRY,
        amount=4999.0,
        attempts_count=1,
        risk_score=0.10,
        is_returning_customer=True,
        is_already_recovered=True
    )
    assert result.status == PolicyResultStatus.STOPPED
    assert result.allowed_action == InterventionType.NO_ACTION
