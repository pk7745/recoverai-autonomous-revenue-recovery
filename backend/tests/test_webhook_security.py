import pytest
import hmac
import hashlib
import json
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base, get_db
from app.core.config import settings
from app.main import app

@pytest.mark.asyncio
async def test_webhook_security_matrix():
    # 1. Setup in-memory test DB and dependency override
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with TestSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    secret = settings.RAZORPAY_WEBHOOK_SECRET
    payload = {
        "event_id": "evt_sec_test_001",
        "event": "payment.authorized",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_sec_test_001",
                    "amount": 499900,
                    "currency": "INR",
                    "status": "authorized"
                }
            }
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    valid_signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test 1: Valid signature -> Accepted (HTTP 200)
        res_valid = await ac.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": valid_signature
            }
        )
        assert res_valid.status_code == 200
        assert res_valid.json()["status"] == "success"
        assert res_valid.json()["duplicate"] is False

        # Test 2: Invalid signature -> Rejected (HTTP 401)
        res_invalid = await ac.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": "invalid_tampered_signature_12345"
            }
        )
        assert res_invalid.status_code == 401
        assert "signature" in res_invalid.json()["detail"].lower()

        # Test 3: Missing signature -> Rejected (HTTP 401)
        res_missing = await ac.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={
                "Content-Type": "application/json"
            }
        )
        assert res_missing.status_code == 401
        assert "missing" in res_missing.json()["detail"].lower()

        # Test 4: Modified payload with original valid signature -> Rejected (HTTP 401)
        tampered_payload = dict(payload)
        tampered_payload["event_id"] = "evt_sec_test_tampered"
        tampered_body = json.dumps(tampered_payload).encode("utf-8")
        res_tampered = await ac.post(
            "/api/v1/webhooks/razorpay",
            content=tampered_body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": valid_signature  # Signature for original payload
            }
        )
        assert res_tampered.status_code == 401

        # Test 5: Duplicate valid event -> Accepted with duplicate=True, no redundant state execution
        res_dup = await ac.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "X-Razorpay-Signature": valid_signature
            }
        )
        assert res_dup.status_code == 200
        assert res_dup.json()["duplicate"] is True
        assert "duplicate" in res_dup.json()["message"].lower()

    app.dependency_overrides.clear()
    await test_engine.dispose()
