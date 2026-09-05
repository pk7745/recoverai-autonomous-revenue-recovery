import pytest
from app.core.security import verify_razorpay_signature, compute_payload_hash
import hmac
import hashlib

def test_signature_verification():
    secret = "whsec_test_secret"
    payload = b'{"event":"payment.captured"}'
    
    valid_sig = hmac.new(key=secret.encode('utf-8'), msg=payload, digestmod=hashlib.sha256).hexdigest()
    assert verify_razorpay_signature(payload, valid_sig, secret) is True
    assert verify_razorpay_signature(payload, "invalid_sig", secret) is False

def test_payload_hash_deterministic():
    payload_a = {"event": "payment.failed", "amount": 4999, "id": "pay_123"}
    payload_b = {"amount": 4999, "id": "pay_123", "event": "payment.failed"}
    
    # Hashes must match regardless of key order
    assert compute_payload_hash(payload_a) == compute_payload_hash(payload_b)
