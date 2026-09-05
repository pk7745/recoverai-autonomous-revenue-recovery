import pytest
import pytest_asyncio
import hmac
import hashlib
import json
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

from app.core.database import Base
from app.models import Merchant, Customer, Transaction, RecoveryWorkflow
from app.core.enums import PaymentStatus, RecoveryState, InterventionType
from app.recovery.orchestrator import RecoveryOrchestrator
from app.webhooks.webhook_handler import WebhookHandler
from app.analytics.metrics_service import MetricsService

@pytest.mark.asyncio
async def test_full_end_to_end_recovery_lifecycle():
    # 1. Setup in-memory test SQLite DB
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    
    async with TestSessionLocal() as session:
        # Seed Merchant & Customer
        merch = Merchant(
            id="merch_test_e2e",
            name="Test Store",
            api_key_id="rzp_test_e2e",
            webhook_secret="whsec_test_e2e",
            autonomous_limit=5000.0,
            max_retries=2
        )
        cust = Customer(
            id="cust_test_e2e",
            merchant_id=merch.id,
            name="Test User",
            email="test@example.com",
            total_successful_payments=5,
            total_failed_payments=1,
            is_returning=True
        )
        txn = Transaction(
            id="txn_test_e2e_1",
            merchant_id=merch.id,
            customer_id=cust.id,
            razorpay_payment_id="pay_test_e2e_1",
            amount=4999.0,
            status="FAILED",
            failure_code="TEMPORARY_ISSUER_DECLINE",
            failure_reason="Issuer bank busy"
        )
        wf = RecoveryWorkflow(
            id="rec_test_e2e_1",
            transaction_id=txn.id,
            state="PAYMENT_FAILED"
        )
        session.add_all([merch, cust, txn, wf])
        await session.commit()
        
        # 2. Plan Recovery Workflow
        orchestrator = RecoveryOrchestrator()
        wf = await orchestrator.plan_workflow(session, wf.id)
        assert wf.state == RecoveryState.POLICY_APPROVED.value
        assert wf.recommended_action == InterventionType.DELAYED_RETRY.value
        assert wf.ai_confidence > 0.70
        await session.commit()
        
        # 3. Execute Recovery Action
        wf = await orchestrator.execute_workflow(session, wf.id)
        assert wf.state == RecoveryState.AWAITING_PAYMENT_EVENT.value
        assert wf.execution_payload is not None
        assert wf.execution_payload["channel"] == "RAZORPAY_RETRY_ENGINE"
        await session.commit()
        
        # 4. Ingest Razorpay Webhook Confirmation (payment.captured)
        webhook_payload = {
            "event_id": "evt_test_e2e_webhook_999",
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_test_e2e_1",
                        "amount": 499900,
                        "currency": "INR",
                        "status": "captured"
                    }
                }
            }
        }
        raw_body = json.dumps(webhook_payload).encode("utf-8")
        valid_sig = hmac.new(
            key=settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            msg=raw_body,
            digestmod=hashlib.sha256
        ).hexdigest()
        success, msg, details = await WebhookHandler.process_webhook(
            db=session,
            raw_body=raw_body,
            signature=valid_sig,
            payload_data=webhook_payload
        )
        assert success is True
        assert details["is_duplicate"] is False
        await session.commit()
        
        # 5. Verify Final Settled State
        refreshed_wf = await orchestrator.plan_workflow(session, wf.id)
        assert refreshed_wf.transaction.status == PaymentStatus.RECOVERED.value
        assert refreshed_wf.recovered_amount == 4999.0
        
        # 6. Verify Dashboard Metrics Updated
        overview = await MetricsService.get_dashboard_overview(session)
        assert overview.metrics.recovered_revenue >= 4999.0
        assert overview.metrics.recovery_rate > 0.0

    await test_engine.dispose()

@pytest.mark.asyncio
async def test_manual_stop_workflow_api_lifecycle():
    from app.api.v1.recovery import stop_recovery_workflow
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with TestSessionLocal() as session:
        merch = Merchant(id="m_stop", name="Stop Store", api_key_id="k", webhook_secret="s")
        cust = Customer(id="c_stop", merchant_id="m_stop", name="Stop User", email="u@test.com")
        txn = Transaction(id="t_stop", merchant_id="m_stop", customer_id="c_stop", amount=2500.0, status="FAILED", failure_code="AUTH_FAILED", failure_reason="fail")
        wf = RecoveryWorkflow(id="rec_t_stop", transaction_id="t_stop", state="PAYMENT_FAILED")
        session.add_all([merch, cust, txn, wf])
        await session.commit()

        stopped = await stop_recovery_workflow(workflow_id=wf.id, db=session)
        assert stopped.state == RecoveryState.STOPPED.value
        assert stopped.stopping_rule_triggered == "Manually stopped by Merchant Operator"
        assert stopped.transaction.amount == 2500.0

    await test_engine.dispose()
