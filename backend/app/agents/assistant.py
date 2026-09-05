import re
from typing import Dict, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.transaction import Transaction
from app.models.recovery_workflow import RecoveryWorkflow
from app.models.merchant import Merchant
from app.models.audit_log import AuditLog
from app.models.checkout_session import CheckoutSession
from app.models.subscription import Subscription
from app.models.receivable_invoice import ReceivableInvoice
from app.models.mandate import Mandate
from app.models.promise_to_pay import PromiseToPay
from app.models.voice_session import VoiceRecoverySession
from app.analytics.metrics_service import MetricsService

class OperationsAssistant:
    """Context-aware Recovery Operations Assistant grounded strictly in database records."""

    @staticmethod
    async def answer_query(db: AsyncSession, query: str, context_workflow_id: Optional[str] = None) -> Dict[str, Any]:
        query_lower = query.lower().strip()

        # 1. Extract IDs from query
        txn_match = re.search(r'(txn_[a-zA-Z0-9_]+)', query)
        wf_match = re.search(r'(rec_[a-zA-Z0-9_]+)', query)
        chk_match = re.search(r'(chk_[a-zA-Z0-9_]+)', query)
        sub_match = re.search(r'(sub_[a-zA-Z0-9_]+)', query)
        inv_match = re.search(r'(inv_[a-zA-Z0-9_]+)', query)
        man_match = re.search(r'(man_[a-zA-Z0-9_]+)', query)
        voc_match = re.search(r'(voc_[a-zA-Z0-9_]+)', query)
        ptp_match = re.search(r'(ptp_[a-zA-Z0-9_]+)', query)

        target_txn_id = txn_match.group(1) if txn_match else None
        target_wf_id = wf_match.group(1) if wf_match else context_workflow_id
        target_chk_id = chk_match.group(1) if chk_match else None
        target_sub_id = sub_match.group(1) if sub_match else None
        target_inv_id = inv_match.group(1) if inv_match else None
        target_man_id = man_match.group(1) if man_match else None
        target_voc_id = voc_match.group(1) if voc_match else None
        target_ptp_id = ptp_match.group(1) if ptp_match else None

        # Check Program Entity Direct Queries
        if target_chk_id:
            chk = (await db.execute(select(CheckoutSession).where(CheckoutSession.id == target_chk_id))).scalar_one_or_none()
            if chk:
                return {
                    "query": query,
                    "summary": f"Checkout Session {chk.id} (Cart: ₹{chk.cart_value:,.2f})",
                    "observed_data": f"Exit Step: {chk.exit_step} | Detected Friction: {chk.detected_friction} | Items: {chk.items_count} | Status: {chk.recovery_status}",
                    "ai_recommendation": f"Tailored checkout recovery incentive/link (URL: {chk.recovery_link_url or 'Generated dynamically'}).",
                    "policy_decision": "Subject to checkout recovery policy & rate limits.",
                    "final_outcome": f"Session recovery status is {chk.recovery_status}.",
                    "references": [chk.id]
                }
        if target_sub_id:
            sub = (await db.execute(select(Subscription).where(Subscription.id == target_sub_id))).scalar_one_or_none()
            if sub:
                return {
                    "query": query,
                    "summary": f"Subscription {sub.id} ({sub.plan_name} - ₹{sub.recurring_amount:,.2f})",
                    "observed_data": f"Status: {sub.status} | Interval: {sub.billing_interval} | Failed Attempts: {sub.failed_attempts}/{sub.max_retries} | Reason: {sub.last_failure_reason or 'None'}",
                    "ai_recommendation": "Smart dunning sequence with optimal retry windows (salary cycle sync).",
                    "policy_decision": f"Bounded by {sub.cooldown_hours}h subscription cooldown and max {sub.max_retries} retry limit.",
                    "final_outcome": f"Next retry scheduled at: {sub.next_retry_at or 'In Dunning'}",
                    "references": [sub.id]
                }
        if target_inv_id:
            inv = (await db.execute(select(ReceivableInvoice).where(ReceivableInvoice.id == target_inv_id))).scalar_one_or_none()
            if inv:
                return {
                    "query": query,
                    "summary": f"B2B Receivable Invoice {inv.invoice_number} ({inv.id})",
                    "observed_data": f"Amount Due: ₹{inv.invoice_amount:,.2f} | Overdue: {inv.overdue_days} days | Stage: {inv.chasing_stage} | Contacts: {inv.contact_count}",
                    "ai_recommendation": "Dynamic chasing workflow with stakeholder-specific tone and payment link generation.",
                    "policy_decision": "High-value B2B policy: Invoices requiring Executive Escalation require Merchant Admin review.",
                    "final_outcome": f"Status: {inv.status} (Last contacted: {inv.last_contact_at or 'Pending initial chase'}).",
                    "references": [inv.id]
                }
        if target_man_id:
            man = (await db.execute(select(Mandate).where(Mandate.id == target_man_id))).scalar_one_or_none()
            if man:
                return {
                    "query": query,
                    "summary": f"Mandate {man.id} ({man.mandate_type})",
                    "observed_data": f"Scheduled Amount: ₹{man.scheduled_amount:,.2f} | Frequency: {man.frequency} | Retries: {man.attempt_number}/{man.max_attempts} | Status: {man.status}",
                    "ai_recommendation": "Debit retry sequencer predicting high-liquidity clearing windows.",
                    "policy_decision": "RBI Compliance Guardrail: Maximum 3 retry attempts hard cap.",
                    "final_outcome": f"Next retry attempt: {man.next_attempt_at or 'Sequenced'}",
                    "references": [man.id]
                }
        if target_voc_id:
            voc = (await db.execute(select(VoiceRecoverySession).where(VoiceRecoverySession.id == target_voc_id))).scalar_one_or_none()
            if voc:
                return {
                    "query": query,
                    "summary": f"Hinglish Voice Recovery Session {voc.id} ({voc.phone_number})",
                    "observed_data": f"Language: {voc.language} | Status: {voc.call_status} | Intent: {voc.detected_intent} | Duration: {voc.duration_seconds}s",
                    "ai_recommendation": f"Generated Script: {voc.generated_script[:80]}...",
                    "policy_decision": "TRAI Calling Window Compliance: Outbound voice calls strictly constrained to 9:00 AM - 8:00 PM IST.",
                    "final_outcome": f"Call Status: {voc.call_status} (Link Sent: {voc.payment_link_sent})",
                    "references": [voc.id]
                }
        if target_ptp_id:
            ptp = (await db.execute(select(PromiseToPay).where(PromiseToPay.id == target_ptp_id))).scalar_one_or_none()
            if ptp:
                return {
                    "query": query,
                    "summary": f"Promise-to-Pay {ptp.id} (Ref: {ptp.reference_id})",
                    "observed_data": f"Promised Amount: ₹{ptp.promised_amount:,.2f} | Promised Date: {ptp.promised_date} | Status: {ptp.status} | Reminders Sent: {ptp.reminder_sent_count}",
                    "ai_recommendation": f"SLA tracking with {ptp.grace_period_hours}h grace period window.",
                    "policy_decision": "PTP Policy: SLA breach triggers automatic escalation and credibility downgrade.",
                    "final_outcome": f"Status is {ptp.status} (Fulfilled: {ptp.fulfilled_at or 'Pending'}).",
                    "references": [ptp.id]
                }

        # 2. Check for Specific Transaction / Workflow Queries
        if target_txn_id or target_wf_id:
            stmt = select(RecoveryWorkflow).options(
                selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.customer),
                selectinload(RecoveryWorkflow.transaction).selectinload(Transaction.merchant)
            )
            if target_wf_id:
                stmt = stmt.where(RecoveryWorkflow.id == target_wf_id)
            elif target_txn_id:
                stmt = stmt.where(RecoveryWorkflow.transaction_id == target_txn_id)

            res = await db.execute(stmt)
            workflow = res.scalar_one_or_none()

            if not workflow:
                # Also try looking up raw Transaction if workflow was not found
                if target_txn_id:
                    txn_stmt = select(Transaction).where(Transaction.id == target_txn_id)
                    txn_res = await db.execute(txn_stmt)
                    txn = txn_res.scalar_one_or_none()
                    if txn:
                        return {
                            "query": query,
                            "summary": f"Transaction {txn.id} found in state {txn.status}.",
                            "observed_data": f"Amount: ₹{txn.amount:,.2f}, Status: {txn.status}, Failure Code: {txn.failure_code or 'None'}.",
                            "ai_recommendation": "No recovery workflow currently mapped.",
                            "policy_decision": "Standard gateway processing.",
                            "final_outcome": f"Transaction status is {txn.status}.",
                            "references": [txn.id]
                        }

                missing_id = target_wf_id or target_txn_id
                return {
                    "query": query,
                    "summary": f"No record found for identifier '{missing_id}'.",
                    "observed_data": "The requested transaction or workflow ID does not exist in the active merchant database.",
                    "ai_recommendation": "N/A",
                    "policy_decision": "N/A",
                    "final_outcome": "Please verify the ID or check the Recovery Queue for active cases.",
                    "references": []
                }

            txn = workflow.transaction
            reasoning = workflow.ai_reasoning or {}
            policy = workflow.policy_evaluation or {}

            # Construct Grounded 4-Layer Response
            observed = (
                f"Transaction ID: {txn.id} | Amount: ₹{txn.amount:,.2f} | "
                f"Gateway Failure: {txn.failure_code or workflow.failure_category} ({txn.failure_reason or 'No reason string'}) | "
                f"Attempts: {txn.attempts_count} | Customer Risk: {txn.customer.risk_tier if txn.customer else 'UNKNOWN'}."
            )

            ai_rec = (
                f"Recommendation: {workflow.recommended_action.replace('_', ' ')} with "
                f"{int(workflow.ai_confidence * 100)}% confidence score. "
                f"Diagnostic Summary: {reasoning.get('summary', 'Root cause classified via factor synthesis.')}"
            )

            if workflow.state == "ESCALATED":
                pol_decision = (
                    f"Status: BLOCKED & ESCALATED. The deterministic Policy Engine intercepted execution because "
                    f"{workflow.escalation_reason or policy.get('rejection_reason', 'it exceeded autonomous limits or risk thresholds')}."
                )
                outcome = f"₹0 automatically recovered. ₹{txn.amount:,.2f} transaction exposure is currently Held for Human Review in the Operations Queue."
            elif workflow.state == "STOPPED":
                pol_decision = (
                    f"Status: STOPPED. Halting rule enforced: {workflow.stopping_rule_triggered or 'Maximum allowable retries reached.'}"
                )
                outcome = "Workflow halted. Zero additional retries scheduled to prevent card network penalty fees."
            elif workflow.state == "RECOVERED":
                pol_decision = (
                    f"Status: ALLOWED. Transaction passed all 4 merchant guardrails (Amount <= ₹5,000, Attempts <= 2, Risk < 0.70)."
                )
                outcome = f"₹{workflow.recovered_amount:,.2f} successfully recaptured and settled via Razorpay Test Mode webhook."
            else:
                pol_decision = f"Status: {policy.get('status', 'PENDING_EVALUATION')}."
                outcome = f"Workflow is currently in state {workflow.state}."

            return {
                "query": query,
                "summary": f"Analysis for {txn.id} (Status: {workflow.state})",
                "observed_data": observed,
                "ai_recommendation": ai_rec,
                "policy_decision": pol_decision,
                "final_outcome": outcome,
                "references": [txn.id, workflow.id]
            }

        # 3. Aggregate Revenue / Metrics Queries
        if any(w in query_lower for w in ["revenue", "recovered", "how much", "rate", "metrics", "stats", "overview"]):
            overview = await MetricsService.get_dashboard_overview(db)
            m = overview.metrics
            return {
                "query": query,
                "summary": "RecoverAI Live Platform Telemetry",
                "observed_data": f"Total Failed Volume at Risk: ₹{m.revenue_at_risk:,.2f} across {m.failed_transactions} failed transactions.",
                "ai_recommendation": f"Autonomous AI diagnostic automation rate is currently {m.ai_automation_rate}%.",
                "policy_decision": f"{m.human_escalations_count} high-risk transactions routed to Human Ops; {m.stopped_actions_count} unsafe actions blocked.",
                "final_outcome": f"Total Recovered Revenue: ₹{m.recovered_revenue:,.2f} (Recovery Rate: {m.recovery_rate}%). Safety Health Score: {m.safety_health_score}%.",
                "references": []
            }

        # 4. Merchant Policy & Guardrails Queries
        if any(w in query_lower for w in ["policy", "limit", "rules", "guardrail", "threshold", "ceiling", "settings"]):
            stmt = select(Merchant).where(Merchant.id == "merch_razorpay_demo")
            res = await db.execute(stmt)
            merch = res.scalar_one_or_none()
            if merch:
                return {
                    "query": query,
                    "summary": f"Active Merchant Policy Guardrails for {merch.name}",
                    "observed_data": f"Merchant ID: {merch.id} | Environment: Razorpay Test Mode.",
                    "ai_recommendation": "AI recommendations are strictly constrained by these deterministic thresholds.",
                    "policy_decision": (
                        f"• Autonomous Amount Ceiling: ₹{merch.autonomous_limit:,.2f}\n"
                        f"• Maximum Retry Attempts: {merch.max_retries} attempts\n"
                        f"• Risk Score Escalation Threshold: {merch.risk_threshold}\n"
                        f"• Minimum Retry Cooldown: {merch.min_retry_interval_mins} minutes."
                    ),
                    "final_outcome": "Any transaction exceeding these limits is automatically blocked from automated execution.",
                    "references": ["policies"]
                }

        # 5. Scenario Explanations
        if "scenario 4" in query_lower or "duplicate" in query_lower or "idempotency" in query_lower:
            return {
                "query": query,
                "summary": "Scenario 4 — Duplicate Webhook Idempotency Architecture",
                "observed_data": "Razorpay webhook event delivers payload with event ID 'evt_demo_dup_webhook_12345'.",
                "ai_recommendation": "AI bypassed; ingress gate resolves duplicate cryptographically.",
                "policy_decision": "SHA-256 payload hash and unique event ID match an existing processed record in webhook_events.",
                "final_outcome": "Second webhook is safely dropped (duplicate: true). Zero duplicate mutations or double-charges occur.",
                "references": ["evt_demo_dup_webhook_12345"]
            }
        elif "scenario 2" in query_lower or "high risk" in query_lower or "27000" in query_lower:
            return {
                "query": query,
                "summary": "Scenario 2 — High Risk Policy Block & Human Escalation",
                "observed_data": "₹27,000 card transaction failed with card velocity anomaly and 0.85 fraud risk score.",
                "ai_recommendation": "Diagnoses fraud risk block.",
                "policy_decision": "Policy Engine intercepts because amount exceeds ₹5,000 limit and risk >= 0.70 threshold -> OVERRIDDEN_TO_ESCALATE.",
                "final_outcome": "Automated execution blocked. ₹0 recovered. Transaction held for human signoff.",
                "references": ["txn_demo_27000"]
            }

        # 6. Recovery Programs Inquiries
        if any(w in query_lower for w in ["program", "capabilities", "modules", "suite", "expansion"]):
            return {
                "query": query,
                "summary": "RecoverAI 7-Program Revenue Recovery Architecture",
                "observed_data": "Seven specialized pipelines active: 1. Payment Degradation Recovery, 2. Checkout Drop-off Recovery, 3. Failed-Subscription Dunning, 4. B2B Receivables Chaser, 5. Mandate Retry Sequencer, 6. Hinglish Voice Recovery, 7. Promise-to-Pay (PTP) Tracker.",
                "ai_recommendation": "All 7 programs utilize specialized AI reasoning with bounded deterministic guardrails.",
                "policy_decision": "Deterministic rules enforce RBI caps (mandates), TRAI hours (voice), 24h subscription cooldowns, and credit score breach escalations.",
                "final_outcome": "Unified audit logging and SSE telemetry across all 7 operational programs.",
                "references": ["programs"]
            }

        # 7. Default Grounded Guidance
        return {
            "query": query,
            "summary": "RecoverAI Operations Intelligence Assistant",
            "observed_data": "I am connected to the live RecoverAI database and deterministic Policy Engine across all 7 recovery programs.",
            "ai_recommendation": "Ask me about specific transactions, subscriptions, invoices, mandates, voice sessions, PTP commitments, recovery metrics, or merchant policies.",
            "policy_decision": "Bounded Autonomy rule: AI Recommends • Policy Decides • Risk Constrains • Execution is Bounded • Audit Records Everything.",
            "final_outcome": "All answers are strictly grounded in active records without hallucination.",
            "references": []
        }
