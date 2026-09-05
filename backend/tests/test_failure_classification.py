import pytest
from app.agents.tools import RecoveryToolRegistry
from app.core.enums import FailureCategory, RecoveryState, InterventionType
from app.schemas.recovery import RecoveryWorkflowResponse
from datetime import datetime, timezone

def test_auth_failed_normalization():
    result = RecoveryToolRegistry.normalize_failure_category("AUTH_FAILED")
    assert result == FailureCategory.AUTHENTICATION_FAILURE

def test_fraud_risk_block_normalization():
    result = RecoveryToolRegistry.normalize_failure_category("FRAUD_RISK_BLOCK")
    assert result == FailureCategory.SUSPICIOUS_FRAUD

def test_known_category_normalization():
    result = RecoveryToolRegistry.normalize_failure_category("TEMPORARY_ISSUER_DECLINE")
    assert result == FailureCategory.TEMPORARY_ISSUER_DECLINE
    
    result_enum = RecoveryToolRegistry.normalize_failure_category(FailureCategory.NETWORK_TIMEOUT)
    assert result_enum == FailureCategory.NETWORK_TIMEOUT

def test_unknown_category_graceful_fallback():
    result = RecoveryToolRegistry.normalize_failure_category("COMPLETELY_UNKNOWN_CUSTOM_ERROR_999")
    assert result == FailureCategory.UNKNOWN
    
    result_none = RecoveryToolRegistry.normalize_failure_category(None)
    assert result_none == FailureCategory.UNKNOWN

def test_pydantic_workflow_response_handles_raw_codes_resiliently():
    # Simulate DB records containing un-normalized strings
    raw_data = {
        "id": "rec_test_norm_1",
        "transaction_id": "txn_test_norm_1",
        "state": RecoveryState.PAYMENT_FAILED,
        "risk_score": 0.15,
        "failure_category": "AUTH_FAILED",  # Raw gateway code
        "recommended_action": InterventionType.PAYMENT_LINK,
        "ai_confidence": 0.85,
        "recovered_amount": 0.0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    resp = RecoveryWorkflowResponse.model_validate(raw_data)
    assert resp.failure_category == FailureCategory.AUTHENTICATION_FAILURE

    raw_data_unknown = {
        "id": "rec_test_norm_2",
        "transaction_id": "txn_test_norm_2",
        "state": RecoveryState.PAYMENT_FAILED,
        "risk_score": 0.50,
        "failure_category": "RANDOM_UNDEFINED_BANK_CODE",  # Unknown string
        "recommended_action": InterventionType.NO_ACTION,
        "ai_confidence": 0.0,
        "recovered_amount": 0.0,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)
    }
    resp_unknown = RecoveryWorkflowResponse.model_validate(raw_data_unknown)
    assert resp_unknown.failure_category == FailureCategory.UNKNOWN
