import hmac
import hashlib
import json
from typing import Dict, Any

def verify_razorpay_signature(payload_body: bytes, signature: str, secret: str) -> bool:
    """
    Cryptographically verifies Razorpay webhook HMAC SHA256 signature.
    """
    if not signature or not secret:
        return False
    
    generated_signature = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(generated_signature, signature)

def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """Computes a deterministic SHA256 digest of arbitrary JSON payload for idempotency checking."""
    serialized = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialized.encode('utf-8')).hexdigest()
