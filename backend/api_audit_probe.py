import httpx
import json

BASE_URL = "http://127.0.0.1:8000"

def test_endpoints():
    results = {}
    with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
        # 1. Health check
        r = client.get("/health")
        results["/health"] = {"status": r.status_code, "text": r.text}
        
        # 2. Dashboard overview
        r = client.get("/api/v1/dashboard/overview")
        results["/api/v1/dashboard/overview"] = {"status": r.status_code, "text": r.text[:200]}
        
        # 3. Recovery Workflows list
        r = client.get("/api/v1/recovery")
        results["/api/v1/recovery"] = {"status": r.status_code, "text": r.text[:200]}
        
        # 4. Safety Overview
        r = client.get("/api/v1/safety/overview")
        results["/api/v1/safety/overview"] = {"status": r.status_code, "text": r.text[:200]}
        
        # 5. Policies
        r = client.get("/api/v1/policies")
        results["/api/v1/policies"] = {"status": r.status_code, "text": r.text[:200]}
        
        # 6. Experiments Benchmark
        r = client.get("/api/v1/experiments/benchmark")
        results["/api/v1/experiments/benchmark"] = {"status": r.status_code, "text": r.text[:200]}
        
        # 7. Audit Logs
        r = client.get("/api/v1/audit/logs")
        results["/api/v1/audit/logs"] = {"status": r.status_code, "text": r.text[:200]}
        
        # 8. Test Demo Scenario 1
        r = client.post("/api/v1/demo/scenario/successful_delayed_retry")
        results["demo_scenario_1"] = {"status": r.status_code, "data": r.json()}
        
        # 9. Test Demo Scenario 2
        r = client.post("/api/v1/demo/scenario/high_risk_escalation")
        results["demo_scenario_2"] = {"status": r.status_code, "data": r.json()}
        
        # 10. Test Demo Scenario 3
        r = client.post("/api/v1/demo/scenario/max_retries_stopped")
        results["demo_scenario_3"] = {"status": r.status_code, "data": r.json()}
        
        # 11. Test Demo Scenario 4
        r = client.post("/api/v1/demo/scenario/duplicate_webhook_protection")
        results["demo_scenario_4"] = {"status": r.status_code, "data": r.json()}
        
        # 12. Test Demo Scenario 5
        r = client.post("/api/v1/demo/scenario/already_recovered_no_action")
        results["demo_scenario_5"] = {"status": r.status_code, "data": r.json()}

    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    test_endpoints()
