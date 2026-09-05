import httpx
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def run_phase4_validation():
    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoints": {},
        "core_journey": {},
        "scenarios": {},
        "metrics_consistency": {},
        "audit_verification": {}
    }

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # Step 0: Reset & seed fresh state
        r = client.post("/api/v1/demo/reset")
        assert r.status_code == 200, f"Reset failed: {r.text}"
        
        # 1. Verify Core API endpoints
        endpoints = [
            ("GET", "/health"),
            ("GET", "/api/v1/dashboard/overview"),
            ("GET", "/api/v1/recovery"),
            ("GET", "/api/v1/safety/overview"),
            ("GET", "/api/v1/policies"),
            ("GET", "/api/v1/experiments/benchmark"),
            ("GET", "/api/v1/audit/logs")
        ]
        for method, path in endpoints:
            res = client.request(method, path)
            report["endpoints"][f"{method} {path}"] = {
                "status": res.status_code,
                "ok": res.status_code == 200
            }

        # 2. Core Recovery Journey Validation (Step A -> Step B -> Step C -> Step D)
        # Select transaction txn_demo_4999 (Workflow rec_txn_demo_4999)
        wf_id = "rec_txn_demo_4999"
        
        # Step A: Get Initial Failed State
        wf_res = client.get(f"/api/v1/recovery/{wf_id}")
        assert wf_res.status_code == 200
        wf_initial = wf_res.json()
        
        # Step B: AI Diagnostic Planning
        plan_res = client.post(f"/api/v1/recovery/{wf_id}/plan")
        assert plan_res.status_code == 200
        wf_planned = plan_res.json()
        
        # Step C: Execute Bounded Recovery Action
        exec_res = client.post(f"/api/v1/recovery/{wf_id}/execute")
        assert exec_res.status_code == 200
        wf_executed = exec_res.json()
        
        # Step D: Webhook Settlement
        # Send payment.captured webhook
        # Signature calculation for test
        import hmac, hashlib
        secret = "whsec_recoverai_super_secret_webhook_2026"
        webhook_payload = {
            "event_id": "evt_phase4_settle_001",
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_N89a7df92",
                        "amount": 499900,
                        "currency": "INR",
                        "status": "captured"
                    }
                }
            }
        }
        raw_body = json.dumps(webhook_payload).encode("utf-8")
        sig = hmac.new(key=secret.encode("utf-8"), msg=raw_body, digestmod=hashlib.sha256).hexdigest()
        
        wh_res = client.post(
            "/api/v1/webhooks/razorpay",
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig}
        )
        assert wh_res.status_code == 200
        
        # Step E: Verify Settled State
        wf_settled_res = client.get(f"/api/v1/recovery/{wf_id}")
        wf_settled = wf_settled_res.json()

        report["core_journey"] = {
            "workflow_id": wf_id,
            "initial_state": wf_initial["state"],
            "planned_state": wf_planned["state"],
            "ai_recommendation": wf_planned["recommended_action"],
            "ai_confidence": wf_planned["ai_confidence"],
            "policy_status": wf_planned["policy_evaluation"]["status"],
            "executed_state": wf_executed["state"],
            "execution_payload_channel": wf_executed["execution_payload"].get("channel"),
            "final_state": wf_settled["state"],
            "recovered_amount": wf_settled["recovered_amount"]
        }

        # 3. Test All 5 Demo Scenarios
        # Scenario 1
        s1 = client.post("/api/v1/demo/scenario/successful_delayed_retry").json()
        report["scenarios"]["scenario_1"] = s1
        
        # Scenario 2
        s2 = client.post("/api/v1/demo/scenario/high_risk_escalation").json()
        report["scenarios"]["scenario_2"] = s2

        # Scenario 3
        s3 = client.post("/api/v1/demo/scenario/max_retries_stopped").json()
        report["scenarios"]["scenario_3"] = s3

        # Scenario 4
        s4 = client.post("/api/v1/demo/scenario/duplicate_webhook_protection").json()
        report["scenarios"]["scenario_4"] = s4

        # Scenario 5
        s5 = client.post("/api/v1/demo/scenario/already_recovered_no_action").json()
        report["scenarios"]["scenario_5"] = s5

        # 4. Metrics Consistency Check across Dashboard, Safety, and DB
        dash = client.get("/api/v1/dashboard/overview").json()
        safety = client.get("/api/v1/safety/overview").json()
        wfs = client.get("/api/v1/recovery").json()
        
        total_in_queue = len(wfs)
        active_count = len([w for w in wfs if w["state"] in ["PAYMENT_FAILED", "RECOVERY_ELIGIBLE", "RECOVERY_PLANNED", "POLICY_APPROVED", "ACTION_EXECUTING", "AWAITING_PAYMENT_EVENT"]])
        escalated_count = len([w for w in wfs if w["state"] == "ESCALATED"])
        stopped_count = len([w for w in wfs if w["state"] == "STOPPED"])
        recovered_count = len([w for w in wfs if w["state"] == "RECOVERED"])
        recovered_amount = sum(w["recovered_amount"] for w in wfs)

        report["metrics_consistency"] = {
            "dashboard_recovered_revenue": dash["metrics"]["recovered_revenue"],
            "sum_recovered_amount_in_wfs": recovered_amount,
            "recovered_revenue_match": dash["metrics"]["recovered_revenue"] == recovered_amount,
            "dashboard_active_workflows": dash["metrics"]["active_recovery_workflows"],
            "queue_active_count": active_count,
            "dashboard_escalations_count": dash["metrics"]["human_escalations_count"],
            "queue_escalations_count": escalated_count,
            "dashboard_stopped_count": dash["metrics"]["stopped_actions_count"],
            "queue_stopped_count": stopped_count,
            "safety_total_stopped": safety["total_stopped_workflows"],
            "safety_stopped_match": safety["total_stopped_workflows"] == stopped_count
        }

        # 5. Audit Trail Verification
        audit_logs = client.get("/api/v1/audit/logs?limit=50").json()
        report["audit_verification"] = {
            "total_audit_records": len(audit_logs),
            "actors_present": list(set(l["actor"] for l in audit_logs)),
            "actions_present": list(set(l["action"] for l in audit_logs)),
            "contains_policy_actions": any("POLICY" in l["action"] for l in audit_logs),
            "contains_system_actions": any("AI" in l["action"] or "RECOVERY" in l["action"] for l in audit_logs),
            "contains_webhook_actions": any("WEBHOOK" in l["action"] for l in audit_logs)
        }

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    run_phase4_validation()
