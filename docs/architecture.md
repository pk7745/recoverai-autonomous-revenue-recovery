# RecoverAI Architecture Document

## 1. High-Level Architecture

```
                                    +-----------------------------+
                                    |    Razorpay Gateway / API   |
                                    |  (Test Mode & Webhook Feed) |
                                    +--------------+--------------+
                                                   |
                                                   v
+--------------------------------------------------+--------------------------------------------------+
|                                        RECOVERAI BACKEND (FastAPI)                                 |
|                                                                                                     |
|  +------------------------+      +------------------------+      +-------------------------------+  |
|  | Webhook Ingestion &    | ---> | Payment Event Registry | ---> | Revenue Risk Detection Engine |  |
|  | HMAC Signature Verif.  |      | & Idempotency Store    |      | (Calculates revenue at risk,  |  |
|  +------------------------+      +------------------------+      | failure classification, score)|  |
|                                                                  +---------------+---------------+  |
|                                                                                  |                  |
|                                                                                  v                  |
|  +------------------------+      +------------------------+      +---------------+---------------+  |
|  | Deterministic Policy   | <--- | AI Recovery Decision   | <--- | Context Aggregator            |  |
|  | & Risk Guardrails      |      | Agent (Tool selection, |      | (Customer history, order info,|  |
|  | (Max amount, attempts) |      | reasoning generation)  |      | attempt history, policies)    |  |
|  +-----------+------------+      +------------------------+      +-------------------------------+  |
|              |                                                                                      |
|              | Approved Action (or Escalate/Stop)                                                   |
|              v                                                                                      |
|  +------------------------+      +------------------------+      +-------------------------------+  |
|  | Recovery Execution     | ---> | Razorpay API Client    | ---> | Immutable Audit Trail &       |  |
|  | Orchestrator           |      | (Links, Retries, Sched)|      | Analytics Aggregator          |  |
|  +------------------------+      +------------------------+      +-------------------------------+  |
+--------------------------------------------------+--------------------------------------------------+
                                                   |
                                                   v
+--------------------------------------------------+--------------------------------------------------+
|                                        RECOVERAI FRONTEND (React + Vite)                            |
|                                                                                                     |
|  * Revenue Command Center (KPIs, time-series recovery charts, live event stream)                   |
|  * Recovery Queue & Interactive AI Decision Studio (Explainable factors, manual override)          |
|  * Safety Center (Blocked actions, stopping rules, duplicate protections, escalations)             |
|  * 10,000+ Transaction Experimentation & Statistical Benchmark Suite                               |
|  * Interactive 5-Scenario Demo Simulator                                                           |
+-----------------------------------------------------------------------------------------------------+
```

## 2. Safety & Bounded Autonomy Guarantee
Under NO circumstance can an LLM directly execute financial or gateway operations.
The workflow is strictly:
```
LLM / AI Model
     │  (Proposes structured Recovery Plan)
     ▼
Structured Tool Request
     │
     ▼
Deterministic Policy Engine Check (Hard limits, amount ceiling, customer frequency, cooldown)
     │
     ▼
Risk & Anomaly Engine Check (Fraud signals, velocity checks)
     │
     ├── If Violated / Over Limit ──► HUMAN_ESCALATION or STOP (Reason logged in Audit Trail)
     │
     └── If Approved ───────────────► Razorpay Execution Service (Bounded API Call)
```

## 3. Storage Layer & Modularity
- **Database Engine:** SQLAlchemy 2.0 async engine with SQLite (local development/demo) or PostgreSQL (production deployment).
- **Idempotency Keys:** Unique SHA-256 event hashing and transaction lock state to prevent race conditions and duplicate executions.
- **Audit Log:** Append-only ledger recording all actor states, timestamps, policy decisions, and payload signatures.
