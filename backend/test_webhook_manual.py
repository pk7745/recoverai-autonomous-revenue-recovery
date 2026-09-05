import httpx
import hmac
import hashlib
import json
import uuid

BASE_URL = "http://127.0.0.1:8000"
SECRET = "whsec_recoverai_super_secret_webhook_2026"

def test_webhook_manual():
    evt_id = f"evt_manual_test_{uuid.uuid4().hex[:8]}"
    payload = {
        "event_id": evt_id,
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_manual_{uuid.uuid4().hex[:8]}",
                    "amount": 499900,
                    "currency": "INR",
                    "status": "captured"
                }
            }
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    valid_sig = hmac.new(key=SECRET.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256).hexdigest()
    
    with httpx.Client(base_url=BASE_URL, timeout=5.0) as client:
        # 1. Missing signature
        r1 = client.post("/api/v1/webhooks/razorpay", content=raw_body, headers={"Content-Type": "application/json"})
        print(f"1. Missing Signature: Status {r1.status_code}, Response: {r1.text}")
        assert r1.status_code == 401
        
        # 2. Invalid signature
        r2 = client.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": "invalid_sig"}
        )
        print(f"2. Invalid Signature: Status {r2.status_code}, Response: {r2.text}")
        assert r2.status_code == 401

        # 3. Valid signature
        r3 = client.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": valid_sig}
        )
        print(f"3. Valid Signature: Status {r3.status_code}, Response: {r3.text}")
        assert r3.status_code == 200
        assert r3.json()["duplicate"] is False

        # 4. Duplicate valid event
        r4 = client.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": valid_sig}
        )
        print(f"4. Duplicate Event: Status {r4.status_code}, Response: {r4.text}")
        assert r4.status_code == 200
        assert r4.json()["duplicate"] is True

    print("\nALL MANUAL WEBHOOK TESTS PASSED!")

if __name__ == "__main__":
    test_webhook_manual()
