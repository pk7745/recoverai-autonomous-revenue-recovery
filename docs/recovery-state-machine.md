# Recovery State Machine & Stopping Rules

## 1. Primary Lifecycle State Diagram

```mermaid
stateDiagram-v2
    [*] --> PAYMENT_FAILED: Webhook / Event Ingested
    PAYMENT_FAILED --> RECOVERY_ELIGIBLE: Check not settled & within timeout
    PAYMENT_FAILED --> STOPPED: Already settled / Expired window

    RECOVERY_ELIGIBLE --> RECOVERY_PLANNED: AI Diagnostic & Intervention Plan
    RECOVERY_ELIGIBLE --> ESCALATED: Anomaly / Critical Risk detected

    RECOVERY_PLANNED --> POLICY_APPROVED: Policy Engine check PASSED
    RECOVERY_PLANNED --> ESCALATED: Policy: High Value / High Risk / Exceeded Auto Limit
    RECOVERY_PLANNED --> STOPPED: Policy: Max Retries Exceeded / Blocked Method

    POLICY_APPROVED --> ACTION_EXECUTING: Execute Bounded Tool (Retry / Link / Alert)
    ACTION_EXECUTING --> AWAITING_PAYMENT_EVENT: Action dispatches, waiting for Webhook

    AWAITING_PAYMENT_EVENT --> RECOVERED: payment.captured / payment.authorized received
    AWAITING_PAYMENT_EVENT --> PAYMENT_FAILED: Subsequent retry failed (re-evaluates with attempts_count + 1)
    AWAITING_PAYMENT_EVENT --> STOPPED: Customer explicit cancellation / Timeout reached

    ESCALATED --> ACTION_EXECUTING: Merchant Manual Override / Approval
    ESCALATED --> STOPPED: Merchant rejects recovery

    RECOVERED --> [*]
    STOPPED --> [*]
```

## 2. Stopping Rules Matrix

| Trigger Condition | Target State | Execution Safety Action | Explainability Reason |
|---|---|---|---|
| Payment already settled / captured | `STOPPED` / `NO_ACTION` | Immediate abort | Transaction is already paid in full. Retrying would cause duplicate charge. |
| Attempts >= Max Retries (e.g. 2) | `STOPPED` | Halt all retries | Reached merchant safety limit for automated interventions. Prevents card issuer penalties. |
| Risk Score >= 0.75 | `ESCALATED` | Block auto-action, alert fraud ops | Suspected velocity abuse or stolen credential pattern. |
| Transaction Amount > Autonomous Limit | `ESCALATED` | Route to finance manager approval | Exceeds merchant auto-approval threshold of ₹5,000. |
| Duplicate Webhook Event ID | `IDEMPOTENT_IGNORED` | Drop execution, record duplicate | Event already processed. State machine remains unchanged. |
| Incompatible Failure (Invalid Card Number) | `STOPPED` | Do not retry | Hard decline / invalid credentials cannot be solved by retrying. |
