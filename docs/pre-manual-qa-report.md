# RecoverAI — Pre-Manual QA & Demo Readiness Report

**Report Date:** August 31, 2026  
**Audience:** Lead Product Engineer & Buildathon Evaluator  
**Status:** **FREEZE COMPLETE — READY FOR MANUAL EVALUATION**  
**Backend:** `http://127.0.0.1:8000` (FastAPI 0.111+)  
**Frontend:** `http://localhost:5173` (React 18 + Vite 5.4)

---

## 1. Startup Verification

The platform was verified to start cleanly from documented terminal commands with zero working-directory or manual `PYTHONPATH` friction:

### Backend Startup:
```bash
cd backend
.venv\Scripts\python -m uvicorn app.main:app --port 8000
```
- **Verification:** Automatically sets up `sys.path` via `app.core.path_setup` and initializes SQLite database schema tables on startup.
- **Port:** `8000`
- **Interactive OpenAPI Documentation:** `http://127.0.0.1:8000/docs`

### Frontend Startup:
```bash
cd frontend
npm run dev
```
- **Verification:** Vite starts in $< 900\text{ms}$ and serves the console on `http://localhost:5173`.

---

## 2. Frontend / API Verification

All 17 REST endpoints utilized by the frontend were probed and verified:

| Feature / UI Flow | HTTP Method & Path | Backend Router / Function | Status Code | Verified Payload |
|---|---|---|---|---|
| Health Check | `GET /health` | `app.main:health_check` | `200 OK` | `{"status": "healthy", "mode": "Razorpay Test Mode"}` |
| Dashboard Overview | `GET /api/v1/dashboard/overview` | `MetricsService.get_dashboard_overview` | `200 OK` | Live KPI metrics + 7-day trend series |
| Recovery Queue | `GET /api/v1/recovery` | `RecoveryOrchestrator.list_workflows` | `200 OK` | Normalized workflows array |
| Workflow Detail | `GET /api/v1/recovery/{id}` | `RecoveryOrchestrator.get_workflow` | `200 OK` | Structured decision factors & policy items |
| AI Diagnostic Plan | `POST /api/v1/recovery/{id}/plan` | `RecoveryOrchestrator.plan_workflow` | `200 OK` | AI diagnosis + Policy Gate evaluation |
| Action Execution | `POST /api/v1/recovery/{id}/execute` | `RecoveryOrchestrator.execute_workflow` | `200 OK` | Bounded Razorpay dispatch payload |
| Manager Signoff | `POST /api/v1/recovery/{id}/approve` | `RecoveryOrchestrator.approve_escalation` | `200 OK` | State $\rightarrow$ `POLICY_APPROVED` |
| Manual Stop | `POST /api/v1/recovery/{id}/stop` | `RecoveryOrchestrator.stop_workflow` | `200 OK` | State $\rightarrow$ `STOPPED` |
| Safety Overview | `GET /api/v1/safety/overview` | `MetricsService.get_safety_overview` | `200 OK` | Safety score (99.9%) + stopped retries |
| Merchant Policies | `GET /api/v1/policies` | `app.api.v1.policies:get_policies` | `200 OK` | Autonomous ceiling, retries, risk threshold |
| Update Policies | `PUT /api/v1/policies` | `app.api.v1.policies:update_policies` | `200 OK` | Immediate persistence in PolicyEngine |
| 10k Benchmark | `GET /api/v1/experiments/benchmark` | `app.api.v1.experiments:get_benchmark` | `200 OK` | 10k transaction empirical dataset |
| Run Simulation | `POST /api/v1/experiments/run` | `app.api.v1.experiments:run_benchmark` | `200 OK` | On-demand cohort simulator |
| Audit Trail | `GET /api/v1/audit/logs` | `AuditService.get_audit_logs` | `200 OK` | Append-only event ledger |
| Cryptographic Webhook | `POST /api/v1/webhooks/razorpay` | `WebhookHandler.process_webhook` | `200 OK` / `401` | HMAC-SHA256 verified ingestion |
| Run Demo Scenario | `POST /api/v1/demo/scenario/{id}` | `app.api.v1.demo:run_demo_scenario` | `200 OK` | Deterministic scenario execution |
| Demo Reset | `POST /api/v1/demo/reset` | `app.api.v1.demo:reset_demo_database` | `200 OK` | Clean database re-seeding |

---

## 3. Five Scenario Verification

Each scenario was executed in complete isolation (Reset $\rightarrow$ Run Scenario $\rightarrow$ Verify DB):

| Scenario | Input Context | Expected Behavior | Actual Outcome | Status |
|---|---|---|---|---|
| **01 — Successful Delayed Retry** | ₹4,999 card failure, Temporary Decline, Attempt 1 | AI recommends retry $\rightarrow$ Policy allows ($\le\text{₹}5,000$) $\rightarrow$ Retry scheduled $\rightarrow$ Webhook settles | State: `RECOVERED`, Recovered: `₹4,999.00`, Policy: `ALLOWED` | **PASS** |
| **02 — High-Risk Policy Block** | ₹27,000 card failure, Fraud risk score 0.85, Attempt 1 | AI diagnoses $\rightarrow$ Policy intercepts ($>\text{₹}5,000$ & risk $\ge 0.70$) $\rightarrow$ Blocks auto-retry $\rightarrow$ Escalates | State: `ESCALATED`, Policy: `OVERRIDDEN_TO_ESCALATE`, Rejection: `High fraud risk profile detected.` | **PASS** |
| **03 — Max Attempts Stop** | Payment failure at Attempt 3 (Max limit 2) | Attempt velocity rule triggers Stopping Rule $\rightarrow$ Halts retries | State: `STOPPED`, Stopping Rule: `Exceeded maximum autonomous retry limit (2)` | **PASS** |
| **04 — Duplicate Webhook** | Replayed signed webhook `evt_demo_dup_webhook_12345` | HMAC verified $\rightarrow$ SHA-256 hash matches existing event $\rightarrow$ Second event dropped | `duplicate: True`, 0 redundant mutations, `DUPLICATE_WEBHOOK_IGNORED` in audit | **PASS** |
| **05 — Already Recovered** | Payment already captured in parallel tab | Policy checks settled state $\rightarrow$ Evaluates `NO_ACTION` $\rightarrow$ Aborts retry | State: `RECOVERED`, Action: `NO_ACTION`, 0 double charges | **PASS** |

---

## 4. Reset Verification

The demo state reset was tested across repeated cycles:
$$\text{Reset} \longrightarrow \text{Scenario 1} \longrightarrow \text{Reset} \longrightarrow \text{Scenario 2} \longrightarrow \text{Reset} \longrightarrow \text{Scenario 3} \longrightarrow \text{Reset}$$
- **Execution Command:** `POST http://127.0.0.1:8000/api/v1/demo/reset` (or "Reset Demo Dataset" button in UI).
- **Result:** Successfully re-seeds fresh merchants, customers, failed transactions, and baseline workflows without database lockups.

---

## 5. Decision Studio Verification (Layer Separation)

The signature **Recovery Decision Studio** modal was inspected for strict subsystem attribution:
- **AI / Expert Recommendation Panel (Blue):** Shows Root Cause Diagnosis, Confidence (88%), Expected Recovery Amount, and Factor Tags. Displays notice: *"Recommendation only. AI cannot execute financial operations without passing deterministic policy validation."*
- **Deterministic Policy Gate (Emerald/Amber):** Shows rule checklist ($\checkmark$/$\times$) verifying Amount Ceiling, Max Retries, Risk Threshold, and Already Recovered state.
- **Dominant Authorization Badges:** Explicitly renders `AUTHORIZED BY POLICY`, `HUMAN REVIEW REQUIRED`, `BLOCKED & STOPPED`, or `AUTHORIZED & RECOVERED`.
- **Causal Decision Trace Timeline:** Visual 8-step pipeline showing which subsystem made each decision (`EVENT` $\rightarrow$ `DETECT` $\rightarrow$ `DIAGNOSE` $\rightarrow$ `RECOMMEND` $\rightarrow$ `POLICY` $\rightarrow$ `RISK` $\rightarrow$ `EXECUTE` $\rightarrow$ `VERIFY` $\rightarrow$ `AUDIT`).

---

## 6. Error-State Verification

The application handles edge cases and failure states gracefully:
- **Invalid Workflow ID:** Querying `GET /api/v1/recovery/rec_invalid_9999` returns `404 Not Found` with structured JSON error details instead of crashing.
- **Missing / Invalid Webhook Signature:** Webhooks without `X-Razorpay-Signature` or with tampered payloads return `401 Unauthorized` (`Missing required X-Razorpay-Signature header`).
- **Empty Filter Search:** Recovery Queue and Audit Trail display empty state notices with search guidance rather than blank screens or console errors.

---

## 7. Data Integrity Verification

The numerical metrics across all screens were verified against database records:

| Metric | Command Center | Recovery Queue | Safety Center | Audit Ledger | Match Verified |
|---|---|---|---|---|---|
| **Recovered Revenue** | `₹4,999.00` | $\sum = \text{₹}4,999.00$ | N/A | Recorded in settlement event | **100% MATCH** |
| **Active Workflows** | `3 Active` | `3 Active Records` | N/A | N/A | **100% MATCH** |
| **Escalations Count** | `0 Escalated` | `0 Escalated Records` | `0 Pending` | Recorded in policy audits | **100% MATCH** |
| **Stopped Workflows** | `0 Stopped` | `0 Stopped Records` | `0 Stopped` | Recorded in policy audits | **100% MATCH** |

---

## 8. Benchmark Integrity Verification

The statistical benchmark was evaluated against $N = 10,000$ synthetic transactions (deterministic seed 42):
- **Recovery Rate Lift:** **+35.98 Percentage-Point Uplift** (**64.29%** RecoverAI vs **28.31%** Baseline).
- **Recovered Volume:** **₹3,69,60,073** (~₹3.70 Cr) vs **₹1,62,75,056** (~₹1.63 Cr) on ₹5.75 Cr at risk.
- **Wasteful Retries Prevented:** **6,218 retries prevented** (89% drop in gateway requests).
- **Platform ROI:** **4.6x** merchant ROI multiple vs 1.8x static baseline.
- **Honest Labeling:** The UI explicitly displays: *"Synthetic benchmark — deterministic seed 42 ($N = 10,000$)* and *+35.98 percentage-point recovery rate uplift"*.

---

## 9. Security Check

- **Zero Hard-Coded Credentials:** All secrets loaded via Pydantic `Settings(BaseSettings)` from `.env`.
- **Git Ignore Protection:** `.gitignore` excludes `.env`, `*.db`, `node_modules/`, `dist/`, `.venv/`.
- **Constant-Time Verification:** Webhooks verify signatures via `hmac.compare_digest`.
- **Safe Audit Logging:** Secrets and sensitive customer card data are never logged in audit trails.

---

## 10. Browser Console Quality Gate

- **JavaScript Errors:** 0 uncaught errors.
- **Network Failures:** 0 failed requests on initial load or navigation.
- **React Hydration / Key Warnings:** 0 key warnings across tables and lists.

---

## 11. Responsive Smoke Test

Verified across standard viewport resolutions:
- **1440px (Desktop):** Full 6-column KPI grid, 2-column charts, master-detail audit inspector.
- **1366px (Laptop):** Proportional layout scaling, clean table headers, zero horizontal scrollbar.
- **1024px (Tablet Landscape):** 3-column KPI grid, stacked chart sections, scrollable filter pills.
- **768px (Tablet Portrait):** 2-column KPI grid, full-width modal drawer with internal scrolling.

---

## 12. Build & Test Results

### Pytest Backend Suite (19/19 Passing):
```bash
test_webhook_manual.py::test_webhook_manual PASSED                       [  5%]
tests/test_benchmark.py::test_synthetic_dataset_generation PASSED        [ 10%]
tests/test_benchmark.py::test_benchmark_simulation_metrics PASSED        [ 15%]
tests/test_e2e_recovery.py::test_full_end_to_end_recovery_lifecycle PASSED [ 21%]
tests/test_failure_classification.py::test_auth_failed_normalization PASSED [ 26%]
tests/test_failure_classification.py::test_fraud_risk_block_normalization PASSED [ 31%]
tests/test_failure_classification.py::test_known_category_normalization PASSED [ 36%]
tests/test_failure_classification.py::test_unknown_category_graceful_fallback PASSED [ 42%]
tests/test_failure_classification.py::test_pydantic_workflow_response_handles_raw_codes_resiliently PASSED [ 47%]
tests/test_idempotency.py::test_signature_verification PASSED            [ 52%]
tests/test_idempotency.py::test_payload_hash_deterministic PASSED        [ 57%]
tests/test_policies.py::test_policy_allows_normal_low_value_transaction PASSED [ 63%]
tests/test_policies.py::test_policy_blocks_amount_exceeding_autonomous_limit PASSED [ 68%]
tests/test_policies.py::test_policy_blocks_high_risk_transaction PASSED  [ 73%]
tests/test_policies.py::test_policy_stops_on_max_attempts PASSED         [ 78%]
tests/test_policies.py::test_policy_stops_if_already_recovered PASSED    [ 84%]
tests/test_state_machine.py::test_legal_state_transitions PASSED         [ 89%]
tests/test_state_machine.py::test_illegal_state_transitions PASSED       [ 94%]
tests/test_webhook_security.py::test_webhook_security_matrix PASSED      [100%]
============================= 19 passed in 0.92s ==============================
```

### Vite Frontend Production Build:
```bash
✓ 2313 modules transformed.
dist/index.html                   1.09 kB │ gzip:   0.63 kB
dist/assets/index-CzqbO4p4.css   30.54 kB │ gzip:   5.71 kB
dist/assets/index-B2Ix7t-6.js   627.58 kB │ gzip: 173.49 kB
✓ built in 6.54s
```

---

## 13. Issues Fixed During QA Pass

1. **Scenario 2 Attempt Count Alignment:** `txn_demo_27000` was initialized with `attempts: 1` instead of `attempts: 3`, ensuring Scenario 2 strictly tests the high-risk / high-amount human escalation gate rather than premature attempt count stoppage.
2. **Demo Repeatability Reset:** Automated reset before scenario execution guarantees deterministic repeatability for evaluators.
3. **Sidebar Type Safety:** Fixed TypeScript interface types in `Sidebar.tsx` and property references in `ExperimentsPage.tsx`.

---

## 14. Remaining Known Limitations (Intentional Scope)

1. **Razorpay Live Gateway Dispatch:** Server-side payment links and retries generate authentic Razorpay Test Mode schemas and cryptographic IDs in local simulation mode rather than making live outbound HTTP requests to `api.razorpay.com`.
2. **Merchant Authentication Middleware:** API routes operate without Bearer JWT login requirements for frictionless buildathon demo evaluation.
