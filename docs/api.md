# API Contract Specification

All endpoints are versioned under `/api/v1`.

### 1. Dashboard & Core Overview
- `GET /api/v1/dashboard/metrics`
  - Returns total volume, revenue at risk, recovered revenue, recovery rate, active workflows, stopped count, escalation count, average recovery latency.
- `GET /api/v1/dashboard/timeseries`
  - Returns daily/hourly time-series of total failed volume vs recovered volume.
- `GET /api/v1/dashboard/activity-feed`
  - Returns real-time chronological stream of recovery state events.

### 2. Recovery Workflows & Decisions
- `GET /api/v1/recovery`
  - Paginated list of recovery workflows with filtering (`state`, `risk_tier`, `failure_category`, `search`).
- `GET /api/v1/recovery/{workflow_id}`
  - Full details of a recovery workflow: transaction, customer context, AI diagnosis, decision factors, policy evaluation, execution log, timeline.
- `POST /api/v1/recovery/{workflow_id}/plan`
  - Triggers AI agent diagnostic & intervention planning.
- `POST /api/v1/recovery/{workflow_id}/execute`
  - Evaluates policy guardrails and executes approved bounded intervention.
- `POST /api/v1/recovery/{workflow_id}/approve`
  - Human manager approval for escalated workflows.
- `POST /api/v1/recovery/{workflow_id}/stop`
  - Merchant override to manually halt workflow.

### 3. Safety Center & Policies
- `GET /api/v1/safety/overview`
  - Metrics on blocked actions, stopped workflows, duplicate events prevented, policy violations.
- `GET /api/v1/policies`
  - Current merchant active policies & risk boundaries.
- `PUT /api/v1/policies`
  - Update merchant autonomous limits, max retry counts, cooldown periods.

### 4. Razorpay Webhooks
- `POST /api/v1/webhooks/razorpay`
  - Receives Razorpay webhook with `X-Razorpay-Signature` validation.
  - Idempotently processes `payment.failed`, `payment.authorized`, `payment.captured`.

### 5. Benchmark Experiments & Analytics
- `GET /api/v1/experiments/benchmark`
  - Returns comprehensive comparison of 10,000+ transaction dataset: Baseline (static retry) vs RecoverAI (context-aware policy-bounded recovery).
- `POST /api/v1/experiments/run`
  - Re-executes the synthetic benchmark on demand.

### 6. Interactive Demo Scenarios
- `POST /api/v1/demo/scenario/{scenario_id}`
  - Executes one of 5 deterministic demo scenarios:
    1. `successful_delayed_retry`
    2. `high_risk_escalation`
    3. `max_retries_stopped`
    4. `duplicate_webhook_protection`
    5. `already_recovered_no_action`
- `POST /api/v1/demo/reset`
  - Resets state and seeds sample transactions for live testing.
