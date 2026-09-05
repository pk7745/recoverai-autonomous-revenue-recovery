import httpx
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def run_pre_manual_qa():
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "endpoints": {},
        "scenarios_isolated": {},
        "data_integrity": {},
        "error_handling": {},
        "benchmark_integrity": {}
    }

    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Test Reset Demo
        r_reset = client.post("/api/v1/demo/reset")
        assert r_reset.status_code == 200, f"Reset failed: {r_reset.text}"
        results["reset_endpoint"] = {"status": r_reset.status_code, "msg": r_reset.json().get("message")}

        # 2. Check all GET endpoints
        endpoints = [
            "/health",
            "/api/v1/dashboard/overview",
            "/api/v1/recovery",
            "/api/v1/safety/overview",
            "/api/v1/policies",
            "/api/v1/experiments/benchmark",
            "/api/v1/audit/logs"
        ]
        for ep in endpoints:
            r = client.get(ep)
            results["endpoints"][ep] = {"status": r.status_code, "ok": r.status_code == 200}
            assert r.status_code == 200, f"Endpoint {ep} failed with {r.status_code}"

        # 3. Test Isolated Scenario Execution (Reset -> Scenario -> Verify)
        # Scenario 1: Successful Delayed Retry
        client.post("/api/v1/demo/reset")
        s1 = client.post("/api/v1/demo/scenario/successful_delayed_retry").json()
        wf1 = client.get(f"/api/v1/recovery/{s1['workflow_id']}").json()
        assert wf1["state"] == "RECOVERED"
        assert wf1["recovered_amount"] == 4999.0
        results["scenarios_isolated"]["scenario_1"] = {
            "status": "PASS",
            "state": wf1["state"],
            "amount": wf1["recovered_amount"],
            "policy_status": wf1["policy_evaluation"]["status"]
        }

        # Scenario 2: High Risk Escalation
        client.post("/api/v1/demo/reset")
        s2 = client.post("/api/v1/demo/scenario/high_risk_escalation").json()
        wf2 = client.get(f"/api/v1/recovery/{s2['workflow_id']}").json()
        assert wf2["state"] == "ESCALATED"
        assert wf2["policy_evaluation"]["status"] == "OVERRIDDEN_TO_ESCALATE"
        results["scenarios_isolated"]["scenario_2"] = {
            "status": "PASS",
            "state": wf2["state"],
            "policy_status": wf2["policy_evaluation"]["status"],
            "rejection": wf2["policy_evaluation"]["rejection_reason"]
        }

        # Scenario 3: Maximum Retries Stopped
        client.post("/api/v1/demo/reset")
        s3 = client.post("/api/v1/demo/scenario/max_retries_stopped").json()
        wf3 = client.get(f"/api/v1/recovery/{s3['workflow_id']}").json()
        assert wf3["state"] == "STOPPED"
        assert "maximum" in wf3["stopping_rule_triggered"].lower()
        results["scenarios_isolated"]["scenario_3"] = {
            "status": "PASS",
            "state": wf3["state"],
            "stopping_rule": wf3["stopping_rule_triggered"]
        }

        # Scenario 4: Duplicate Webhook Protection
        client.post("/api/v1/demo/reset")
        s4 = client.post("/api/v1/demo/scenario/duplicate_webhook_protection").json()
        assert s4["duplicate_detected"] is True
        results["scenarios_isolated"]["scenario_4"] = {
            "status": "PASS",
            "event_id": s4["event_id"],
            "duplicate_detected": s4["duplicate_detected"]
        }

        # Scenario 5: Already Recovered (DO NOTHING)
        client.post("/api/v1/demo/reset")
        s5 = client.post("/api/v1/demo/scenario/already_recovered_no_action").json()
        wf5 = client.get(f"/api/v1/recovery/{s5['workflow_id']}").json()
        assert wf5["recommended_action"] == "NO_ACTION"
        results["scenarios_isolated"]["scenario_5"] = {
            "status": "PASS",
            "workflow_id": wf5["id"],
            "recommended_action": wf5["recommended_action"],
            "state": wf5["state"]
        }

        # 4. Error Handling Verification
        r_404 = client.get("/api/v1/recovery/rec_non_existent_id_99999")
        assert r_404.status_code == 404
        results["error_handling"]["invalid_workflow_404"] = {"status": r_404.status_code, "ok": True}

        # 5. Data Integrity Check across Dashboard and DB
        client.post("/api/v1/demo/reset")
        # Run Scenario 1 to produce known state
        client.post("/api/v1/demo/scenario/successful_delayed_retry")
        dash = client.get("/api/v1/dashboard/overview").json()
        wfs = client.get("/api/v1/recovery").json()
        safety = client.get("/api/v1/safety/overview").json()
        
        sum_rec = sum(w["recovered_amount"] for w in wfs)
        dash_rec = dash["metrics"]["recovered_revenue"]
        assert dash_rec == sum_rec, f"Mismatch: dash={dash_rec}, wfs_sum={sum_rec}"
        
        results["data_integrity"] = {
            "dashboard_recovered_revenue": dash_rec,
            "wfs_sum_recovered_amount": sum_rec,
            "match": dash_rec == sum_rec,
            "active_workflows_count": dash["metrics"]["active_recovery_workflows"],
            "human_escalations_count": dash["metrics"]["human_escalations_count"],
            "stopped_actions_count": dash["metrics"]["stopped_actions_count"]
        }

        # 6. Benchmark Data Integrity Check
        bench = client.get("/api/v1/experiments/benchmark").json()
        assert bench["dataset_size"] == 10000
        assert round(bench["uplift_percentage"], 2) == 35.98
        assert round(bench["recoverai_strategy"]["recovery_rate"], 2) == 64.29
        assert round(bench["baseline_strategy"]["recovery_rate"], 2) == 28.31
        results["benchmark_integrity"] = {
            "dataset_size": bench["dataset_size"],
            "baseline_rate": bench["baseline_strategy"]["recovery_rate"],
            "recoverai_rate": bench["recoverai_strategy"]["recovery_rate"],
            "uplift_percentage_points": bench["uplift_percentage"],
            "wasteful_retries_prevented": bench["wasteful_retries_prevented"]
        }

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_pre_manual_qa()
