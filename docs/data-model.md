# Data Model & Schema Specification

## 1. Entities & Relationships

### `merchants`
- `id` (VARCHAR PK): Unique merchant identifier (e.g. `merch_razorpay_demo`)
- `name` (VARCHAR): Business / merchant trade name
- `api_key_id` (VARCHAR): Razorpay Test Mode Key ID
- `webhook_secret` (VARCHAR): Secret for HMAC-SHA256 signature verification
- `autonomous_limit` (FLOAT): Maximum INR amount permitted for autonomous intervention (default: ₹5,000)
- `max_retries` (INT): Maximum automated recovery attempts per invoice (default: 2)
- `created_at` (TIMESTAMP)

### `customers`
- `id` (VARCHAR PK): Customer ID (`cust_...`)
- `merchant_id` (VARCHAR FK -> merchants.id)
- `email` (VARCHAR)
- `phone` (VARCHAR)
- `total_successful_payments` (INT): Lifetime successful orders
- `total_failed_payments` (INT): Lifetime failed attempts
- `is_returning` (BOOLEAN): Flag if >= 1 historical settled payment
- `risk_tier` (VARCHAR): `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `created_at` (TIMESTAMP)

### `transactions`
- `id` (VARCHAR PK): Internal transaction ID (`txn_...`)
- `merchant_id` (VARCHAR FK)
- `customer_id` (VARCHAR FK)
- `razorpay_payment_id` (VARCHAR): Gateway payment ID (`pay_...`)
- `razorpay_order_id` (VARCHAR): Gateway order ID (`order_...`)
- `amount` (FLOAT): Transaction amount in INR
- `currency` (VARCHAR): Currency code (e.g. `INR`)
- `status` (VARCHAR): `PAYMENT_PENDING`, `PAYMENT_FAILED`, `PAYMENT_AUTHORIZED`, `PAYMENT_CAPTURED`, `RECOVERED`
- `failure_code` (VARCHAR): e.g. `BAD_REQUEST_ERROR`, `GATEWAY_ERROR`, `AUTH_FAILED`, `INSUFFICIENT_FUNDS`
- `failure_reason` (TEXT): Diagnostic description of failure
- `payment_method` (VARCHAR): `card`, `upi`, `netbanking`, `wallet`
- `attempts_count` (INT): Number of attempts made for this payment
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### `recovery_workflows`
- `id` (VARCHAR PK): Recovery workflow ID (`rec_...`)
- `transaction_id` (VARCHAR FK -> transactions.id)
- `state` (VARCHAR): State machine state (`PAYMENT_FAILED`, `RECOVERY_ELIGIBLE`, `RECOVERY_PLANNED`, `POLICY_APPROVED`, `ACTION_EXECUTING`, `AWAITING_PAYMENT_EVENT`, `RECOVERED`, `STOPPED`, `ESCALATED`)
- `risk_score` (FLOAT): 0.0 to 1.0 risk indicator
- `failure_category` (VARCHAR): `TEMPORARY_ISSUER_DECLINE`, `AUTHENTICATION_FAILURE`, `INSUFFICIENT_FUNDS`, `NETWORK_TIMEOUT`, `SUSPICIOUS_FRAUD`, `UNSUPPORTED_METHOD`
- `recommended_action` (VARCHAR): `DELAYED_RETRY`, `ALTERNATIVE_PAYMENT`, `PAYMENT_LINK`, `CUSTOMER_NOTIFICATION`, `HUMAN_ESCALATION`, `STOP`, `NO_ACTION`
- `ai_confidence` (FLOAT): 0.0 to 1.0 confidence rating
- `ai_reasoning` (JSON): Structured decision factors, diagnostic signals, explainability summary
- `policy_evaluation` (JSON): Outcome of merchant policy evaluation (status: `ALLOWED`, `OVERRIDDEN_TO_ESCALATE`, `BLOCKED`, `STOPPED`)
- `execution_payload` (JSON): Details of executed action (payment link URL, retry schedule, dispatch ID)
- `recovered_amount` (FLOAT): Amount recovered (0 if unrecovered)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### `audit_logs`
- `id` (VARCHAR PK): Audit ID (`aud_...`)
- `workflow_id` (VARCHAR FK -> recovery_workflows.id, nullable)
- `transaction_id` (VARCHAR FK -> transactions.id, nullable)
- `actor` (VARCHAR): `SYSTEM_AGENT`, `POLICY_ENGINE`, `RISK_ENGINE`, `MERCHANT_ADMIN`, `RAZORPAY_WEBHOOK`
- `action` (VARCHAR): Action verb (e.g. `FAILURE_DIAGNOSED`, `POLICY_EVALUATED`, `PAYMENT_LINK_CREATED`, `WEBHOOK_VERIFIED`, `RECOVERY_COMPLETED`)
- `details` (JSON): Detailed key-value context, timestamps, metadata
- `created_at` (TIMESTAMP)

### `webhook_events`
- `id` (VARCHAR PK): Webhook event record ID (`whe_...`)
- `razorpay_event_id` (VARCHAR UNIQUE): Gateway event ID (`event_...`)
- `event_type` (VARCHAR): e.g. `payment.failed`, `payment.authorized`, `payment.captured`
- `payload` (JSON): Raw payload for audit & replay protection
- `signature` (VARCHAR): HMAC SHA256 signature header
- `is_duplicate` (BOOLEAN): Flag if duplicate event detected
- `processed_at` (TIMESTAMP)
