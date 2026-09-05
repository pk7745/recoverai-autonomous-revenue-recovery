import pytest
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.models import (
    Merchant, Customer, Transaction, RecoveryWorkflow,
    CheckoutSession, Subscription, ReceivableInvoice,
    Mandate, PromiseToPay, VoiceRecoverySession
)
from app.recovery.orchestrator import RecoveryOrchestrator
from app.agents.assistant import OperationsAssistant

async def setup_test_db():
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    session = TestSessionLocal()
    
    # Base Merchant & Customer
    merch = Merchant(
        id="merch_razorpay_demo",
        name="Test Store",
        api_key_id="rzp_test_key",
        webhook_secret="whsec_test_secret",
        autonomous_limit=50000.0,
        max_retries=3
    )
    cust = Customer(
        id="cust_test_01",
        merchant_id=merch.id,
        name="Rahul Roy",
        email="rahul@example.com",
        phone="+919876543210",
        total_successful_payments=4,
        total_failed_payments=1,
        is_returning=True
    )
    session.add_all([merch, cust])
    await session.commit()
    return session


@pytest.mark.asyncio
async def test_checkout_dropoff_lifecycle():
    db_session = await setup_test_db()
    orchestrator = RecoveryOrchestrator()
    
    # 1. Create Checkout Session
    chk = CheckoutSession(
        id="chk_test_101",
        merchant_id="merch_razorpay_demo",
        customer_id="cust_test_01",
        cart_value=4500.0,
        exit_step="PAYMENT_STEP",
        detected_friction="GATEWAY_LATENCY",
        items_count=2
    )
    db_session.add(chk)
    await db_session.commit()

    # 2. Plan Checkout Recovery
    chk_obj, wf = await orchestrator.plan_checkout_recovery(db_session, chk.id)
    await db_session.commit()

    assert wf.recovery_type == "CHECKOUT"
    assert wf.reference_id == chk.id
    assert wf.state == "POLICY_APPROVED"
    assert wf.ai_confidence > 0.5
    assert wf.ai_reasoning is not None

    # 3. Execute Checkout Recovery
    chk_exec, wf_exec = await orchestrator.execute_checkout_recovery(db_session, chk.id)
    await db_session.commit()

    assert wf_exec.state in ["AWAITING_PAYMENT_EVENT", "RECOVERED"]
    assert wf_exec.execution_mode == "SIMULATED"
    assert chk_exec.recovery_status == "RECOVERY_INITIATED"
    await db_session.close()


@pytest.mark.asyncio
async def test_subscription_recovery_lifecycle():
    db_session = await setup_test_db()
    orchestrator = RecoveryOrchestrator()

    # 1. Create Failed Subscription
    sub = Subscription(
        id="sub_test_201",
        merchant_id="merch_razorpay_demo",
        customer_id="cust_test_01",
        plan_id="plan_growth",
        plan_name="Growth Cloud Monthly",
        recurring_amount=2999.0,
        billing_interval="monthly",
        status="PAST_DUE",
        failed_attempts=1,
        last_failure_reason="Card expired or issuer busy",
        cooldown_hours=24
    )
    db_session.add(sub)
    await db_session.commit()

    # 2. Plan Subscription Dunning
    sub_obj, wf = await orchestrator.plan_subscription_recovery(db_session, sub.id)
    await db_session.commit()

    assert wf.recovery_type == "SUBSCRIPTION"
    assert wf.reference_id == sub.id
    assert wf.state == "POLICY_APPROVED"

    # 3. Execute Dunning
    sub_exec, wf_exec = await orchestrator.execute_subscription_recovery(db_session, sub.id)
    await db_session.commit()

    assert wf_exec.state in ["AWAITING_PAYMENT_EVENT", "RECOVERED"]
    assert wf_exec.execution_mode == "SIMULATED"
    await db_session.close()


@pytest.mark.asyncio
async def test_b2b_receivables_chasing_lifecycle():
    db_session = await setup_test_db()
    orchestrator = RecoveryOrchestrator()

    # 1. Create Receivable Invoice (within autonomous limit)
    inv = ReceivableInvoice(
        id="inv_test_301",
        merchant_id="merch_razorpay_demo",
        customer_id="cust_test_01",
        invoice_number="INV-2026-301",
        invoice_amount=35000.0,
        due_date=datetime.now(timezone.utc),
        overdue_days=10,
        chasing_stage="GENTLE_REMINDER",
        status="OUTSTANDING"
    )
    db_session.add(inv)
    await db_session.commit()

    # 2. Plan Receivables Chasing
    inv_obj, wf = await orchestrator.plan_receivable_chasing(db_session, inv.id)
    await db_session.commit()

    assert wf.recovery_type == "RECEIVABLE"
    assert wf.reference_id == inv.id
    assert wf.state == "POLICY_APPROVED"

    # 3. Execute Receivables Chasing
    inv_exec, wf_exec = await orchestrator.execute_receivable_chasing(db_session, inv.id)
    await db_session.commit()

    assert wf_exec.state in ["AWAITING_PAYMENT_EVENT", "RECOVERED"]
    assert wf_exec.execution_mode == "SIMULATED"
    assert inv_exec.contact_count == 1
    await db_session.close()


@pytest.mark.asyncio
async def test_mandate_sequencer_lifecycle():
    db_session = await setup_test_db()
    orchestrator = RecoveryOrchestrator()

    # 1. Create Mandate
    man = Mandate(
        id="man_test_401",
        merchant_id="merch_razorpay_demo",
        customer_id="cust_test_01",
        mandate_token="tok_man_401",
        mandate_type="UPI_AUTOPAY",
        max_amount=10000.0,
        scheduled_amount=4500.0,
        frequency="MONTHLY",
        status="SEQUENCED",
        attempt_number=1,
        max_attempts=3
    )
    db_session.add(man)
    await db_session.commit()

    # 2. Plan Mandate Sequence
    man_obj, wf = await orchestrator.plan_mandate_sequence(db_session, man.id)
    await db_session.commit()

    assert wf.recovery_type == "MANDATE"
    assert wf.reference_id == man.id
    assert wf.state == "POLICY_APPROVED"

    # 3. Execute Mandate Sequence
    man_exec, wf_exec = await orchestrator.execute_mandate_sequence(db_session, man.id)
    await db_session.commit()

    assert wf_exec.state in ["AWAITING_PAYMENT_EVENT", "RECOVERED"]
    assert wf_exec.execution_mode == "SIMULATED"
    await db_session.close()


@pytest.mark.asyncio
async def test_hinglish_voice_recovery_lifecycle():
    db_session = await setup_test_db()
    orchestrator = RecoveryOrchestrator()

    # 1. Create Voice Recovery Session
    voc = VoiceRecoverySession(
        id="voc_test_501",
        merchant_id="merch_razorpay_demo",
        customer_id="cust_test_01",
        phone_number="+919876543210",
        language="HINGLISH",
        generated_script="Namaste Rahul ji, RecoverAI finance desk se call hai.",
        call_status="SIMULATED_READY",
        detected_intent="AGREED_TO_RETRY",
        duration_seconds=45,
        execution_mode="SIMULATED"
    )
    db_session.add(voc)
    await db_session.commit()

    # 2. Plan Voice Recovery
    voc_obj, wf = await orchestrator.plan_voice_recovery(db_session, voc.id)
    await db_session.commit()

    assert wf.recovery_type == "VOICE_RECOVERY"
    assert wf.reference_id == voc.id

    # 3. Execute Voice Recovery Call
    voc_exec, wf_exec = await orchestrator.execute_voice_recovery(db_session, voc.id)
    await db_session.commit()

    assert wf_exec.execution_mode == "SIMULATED"
    assert voc_exec.call_status == "CONNECTED"
    await db_session.close()


@pytest.mark.asyncio
async def test_promise_to_pay_lifecycle():
    db_session = await setup_test_db()
    orchestrator = RecoveryOrchestrator()

    # 1. Create Promise-to-Pay
    ptp = PromiseToPay(
        id="ptp_test_601",
        merchant_id="merch_razorpay_demo",
        customer_id="cust_test_01",
        reference_type="INVOICE",
        reference_id="inv_test_301",
        promised_amount=50000.0,
        promised_date=datetime.now(timezone.utc),
        grace_period_hours=24,
        status="ACTIVE"
    )
    db_session.add(ptp)
    await db_session.commit()

    # 2. Plan PTP Tracking
    ptp_obj, wf = await orchestrator.plan_promise_to_pay(db_session, ptp.id)
    await db_session.commit()

    assert wf.recovery_type == "PROMISE_TO_PAY"
    assert wf.reference_id == ptp.id

    # 3. Fulfill PTP
    ptp_ful, wf_fulfill = await orchestrator.fulfill_promise_to_pay(db_session, ptp.id)
    await db_session.commit()

    assert wf_fulfill.state == "RECOVERED"
    assert wf_fulfill.recovered_amount == 50000.0
    assert ptp_ful.status == "FULFILLED"
    await db_session.close()


@pytest.mark.asyncio
async def test_operations_assistant_program_queries():
    db_session = await setup_test_db()

    # Test natural language answering for programs
    ans_prog = await OperationsAssistant.answer_query(db_session, "Tell me about the recovery programs")
    assert "7-Program" in ans_prog["summary"]

    # Test query for specific checkout session
    chk = CheckoutSession(
        id="chk_test_777",
        merchant_id="merch_razorpay_demo",
        customer_id="cust_test_01",
        cart_value=7200.0,
        exit_step="PAYMENT_STEP",
        detected_friction="GATEWAY_LATENCY",
        items_count=3
    )
    db_session.add(chk)
    await db_session.commit()

    ans_chk = await OperationsAssistant.answer_query(db_session, "What happened to chk_test_777?")
    assert "chk_test_777" in ans_chk["summary"]
    assert "7,200" in ans_chk["summary"]
    await db_session.close()
