import pytest
import pytest_asyncio
from datetime import timedelta
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from fastapi import HTTPException

from app.core.database import Base
from app.models import Merchant, Customer, Transaction, RecoveryWorkflow, User
from app.core.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    require_role
)
from app.agents.assistant import OperationsAssistant
from app.core.notifications import broadcaster
from app.schemas.policy import UpdateMerchantPolicyRequest
from app.api.v1.policies import update_merchant_policy
from fastapi.security import HTTPAuthorizationCredentials

@pytest.mark.asyncio
async def test_auth_password_hashing_and_jwt():
    raw_pwd = "SecureSecretPassword123!"
    hashed = hash_password(raw_pwd)
    
    assert verify_password(raw_pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

    token = create_access_token({"sub": "usr_123", "role": "MERCHANT_ADMIN"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "usr_123"
    assert payload["role"] == "MERCHANT_ADMIN"

    # Test invalid / malformed token
    assert decode_access_token("invalid.token.string") is None
    assert decode_access_token("garbage_string") is None

    # Test expired token
    expired_token = create_access_token({"sub": "usr_123"}, expires_delta=timedelta(seconds=-3600))
    assert decode_access_token(expired_token) is None

@pytest.mark.asyncio
async def test_rbac_backend_authoritative_enforcement():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSessionLocal() as session:
        # Seed merchant and 2 users
        merch = Merchant(id="m_rbac", name="RBAC Store", api_key_id="k", webhook_secret="s", autonomous_limit=5000.0)
        admin_user = User(
            id="usr_admin_test",
            merchant_id="m_rbac",
            email="admin@test.com",
            name="Admin",
            hashed_password=hash_password("Pass123!"),
            role="MERCHANT_ADMIN"
        )
        ops_user = User(
            id="usr_ops_test",
            merchant_id="m_rbac",
            email="ops@test.com",
            name="Agent",
            hashed_password=hash_password("Pass123!"),
            role="OPERATIONS_AGENT"
        )
        session.add_all([merch, admin_user, ops_user])
        await session.commit()

        # Tokens
        admin_token = create_access_token({"sub": admin_user.id, "role": "MERCHANT_ADMIN"})
        ops_token = create_access_token({"sub": ops_user.id, "role": "OPERATIONS_AGENT"})
        expired_token = create_access_token({"sub": admin_user.id, "role": "MERCHANT_ADMIN"}, expires_delta=timedelta(seconds=-10))

        checker = require_role(["MERCHANT_ADMIN"])

        # 1. Missing token -> 401
        with pytest.raises(HTTPException) as exc_missing:
            await checker(auth=None, db=session)
        assert exc_missing.value.status_code == 401

        # 2. Expired token -> 401
        with pytest.raises(HTTPException) as exc_expired:
            await checker(auth=HTTPAuthorizationCredentials(scheme="Bearer", credentials=expired_token), db=session)
        assert exc_expired.value.status_code == 401

        # 3. Invalid token -> 401
        with pytest.raises(HTTPException) as exc_invalid:
            await checker(auth=HTTPAuthorizationCredentials(scheme="Bearer", credentials="bad.token"), db=session)
        assert exc_invalid.value.status_code == 401

        # 4. Operations Agent token on Admin-only operation -> 403 FORBIDDEN
        with pytest.raises(HTTPException) as exc_forbidden:
            await checker(auth=HTTPAuthorizationCredentials(scheme="Bearer", credentials=ops_token), db=session)
        assert exc_forbidden.value.status_code == 403
        assert "Permission denied" in exc_forbidden.value.detail

        # 5. Merchant Admin token -> 200 OK and resolves user
        resolved_admin = await checker(auth=HTTPAuthorizationCredentials(scheme="Bearer", credentials=admin_token), db=session)
        assert resolved_admin.id == admin_user.id
        assert resolved_admin.role == "MERCHANT_ADMIN"

        # 6. Test actual policy update persistence with Admin
        update_req = UpdateMerchantPolicyRequest(autonomous_limit=7500.0, max_retries=3)
        res = await update_merchant_policy(req=update_req, current_user=resolved_admin, db=session)
        assert res.autonomous_limit == 7500.0
        assert res.max_retries == 3

    await test_engine.dispose()

@pytest.mark.asyncio
async def test_operations_assistant_grounded_queries():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSessionLocal() as session:
        merch = Merchant(id="m_asst", name="Assistant Store", api_key_id="k", webhook_secret="s")
        cust = Customer(id="c_asst", merchant_id="m_asst", name="Rahul", email="r@test.com")
        txn = Transaction(id="txn_asst_1", merchant_id="m_asst", customer_id="c_asst", amount=4999.0, status="RECOVERED", failure_code="TEMPORARY_ISSUER_DECLINE")
        wf = RecoveryWorkflow(id="rec_asst_1", transaction_id="txn_asst_1", state="RECOVERED", recovered_amount=4999.0, ai_confidence=0.88)
        session.add_all([merch, cust, txn, wf])
        await session.commit()

        # Query known transaction
        res1 = await OperationsAssistant.answer_query(session, "What happened to txn_asst_1?")
        assert "txn_asst_1" in res1["observed_data"]
        assert "4,999.00" in res1["final_outcome"]
        assert len(res1["references"]) > 0

        # Query unknown transaction
        res2 = await OperationsAssistant.answer_query(session, "Status of txn_unknown_9999")
        assert "No record found" in res2["summary"]
        assert len(res2["references"]) == 0

    await test_engine.dispose()

@pytest.mark.asyncio
async def test_notification_broadcaster_pubsub():
    history_before = len(broadcaster.get_history())
    await broadcaster.broadcast(
        event_type="PAYMENT_RECOVERED",
        title="Test Recovery",
        message="₹4,999 recovered",
        severity="SUCCESS",
        amount=4999.0
    )
    history_after = broadcaster.get_history()
    assert len(history_after) == history_before + 1
    assert history_after[0]["title"] == "Test Recovery"
    assert history_after[0]["severity"] == "SUCCESS"
