# RecoverAI — Autonomous AI Revenue Recovery Platform

> **"AI Recommends. Policy Decides. Risk Constrains. Execution is Bounded. Audit Records Everything."**  
> Built for the **Razorpay AI Builder Buildathon 2026 — Track 03: AI Revenue Recovery**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![asyncpg](https://img.shields.io/badge/Driver-asyncpg-2C3E50?logo=python&logoColor=white)](https://magicstack.github.io/asyncpg/)
[![Razorpay Test Mode](https://img.shields.io/badge/Razorpay-Test%20Mode-0C2340?logo=razorpay&logoColor=white)](https://razorpay.com/docs/)
[![Pytest](https://img.shields.io/badge/Tests-24%20Passing%20(100%25)-4E9A06?logo=pytest&logoColor=white)](https://pytest.org)

---

## 1. Executive Summary & Problem Statement

When merchant payments fail on payment gateways, Indian online merchants lose **15% to 25% of top-line GMV**. Existing recovery approaches suffer from two fatal extremes:

1. **Passive Inaction:** The failure is treated as terminal; the cart is abandoned, and the customer churns.
2. **Blind Retry Scripts ("Spam Bots"):** Naive cron scripts retry every failed payment immediately and identically, triggering bank card flags, payment gateway rate limits, chargeback spikes, customer harassment, and double charges.

**RecoverAI** replaces naive retry scripts with an **autonomous, policy-bounded revenue recovery engine**. It detects failures in real-time, diagnoses root causes via factor synthesis, recommends intelligent interventions, subjects every action to deterministic merchant policy gates, executes bounded operations, and records tamper-evident audit trails.

```
EVENT ──► EVIDENCE ──► DIAGNOSIS ──► RECOMMENDATION ──► RISK CHECK ──► POLICY GATE ──► BOUNDED EXECUTION ──► AUDIT LEDGER
```

---

## 2. Core Architecture & Bounded Autonomy

Under **no circumstance** is an AI agent permitted to execute financial mutations directly. The system enforces strict architectural layers:

```
                            [ Merchant Operator / Admin ]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 │       React 18 + TypeScript Console           │
                 │  • Real-Time SSE Notification Center          │
                 │  • Grounded 4-Layer Operations Assistant      │
                 │  • RBAC Guardrail Policy Control Plane        │
                 └───────────────────────┬───────────────────────┘
                                         │ HTTP / Bearer JWT
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │             FastAPI Ingress Layer             │
                 │  • Backend RBAC Authorization (Admin vs Agent)│
                 │  • HMAC-SHA256 Webhook Verification           │
                 │  • SHA-256 Idempotency Ingress Gate           │
                 └───────────────────────┬───────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
┌─────────────────┐            ┌───────────────────┐            ┌───────────────────┐
│ AI Diagnostic   │            │ Deterministic     │            │ Risk Engine       │
│ Agent           │ ─────────► │ Policy Engine     │ ─────────► │ Factor Scoring    │
│ (Root Cause)    │            │ (Hard Boundaries) │            │ (Fraud Velocity)  │
└─────────────────┘            └───────────────────┘            └───────────────────┘
                                         │
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │        9-State Recovery State Machine         │
                 │        Scoped Razorpay Client Executor        │
                 │        Tamper-Evident Audit Ledger            │
                 └───────────────────────┬───────────────────────┘
                                         │ SQLAlchemy 2.0 Async
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │        Persistent Database Storage            │
                 │   Dev: SQLite 3 (aiosqlite)                   │
                 │   Prod: PostgreSQL 16 (asyncpg)               │
                 └───────────────────────────────────────────────┘
```

---

## 3. Subsystems & Key Capabilities

### 1. 9-State Recovery State Machine
Enforces strict legal state transitions:
`PAYMENT_FAILED` $\rightarrow$ `RECOVERY_ELIGIBLE` $\rightarrow$ `RECOVERY_PLANNED` $\rightarrow$ `POLICY_APPROVED` $\rightarrow$ `ACTION_EXECUTING` $\rightarrow$ `AWAITING_PAYMENT_EVENT` $\rightarrow$ `RECOVERED` / `ESCALATED` / `STOPPED`.

### 2. Deterministic Merchant Policy Engine
Server-side authoritative rules that cannot be overridden by AI reasoning:
- **Autonomous Ceiling:** Automated interventions capped at ₹5,000.00 (higher amounts routed to Human Review).
- **Max Retry Limit:** Hard cap of 2 retry attempts per transaction (attempt 3 triggers `STOPPED`).
- **Fraud Anomaly Threshold:** Risk score $\ge 0.70$ immediately halts autonomous actions.
- **Cooldown Interval:** Enforces minimum 30-minute delays for issuer declines.

### 3. Gateway Security & Idempotency Gate
- **HMAC-SHA256 Verification:** Constant-time `hmac.compare_digest` validation of gateway webhook signatures.
- **SHA-256 Payload Deduplication:** Hashes webhook bodies and indexes event IDs to drop duplicate network replays with zero financial mutation.

### 4. Real-Time SSE Notification Center
Streams live gateway and recovery events directly to the browser over Server-Sent Events (`/api/v1/events/stream`), eliminating polling while displaying severity badges, timestamps, and transaction links.

### 5. Grounded Operations Assistant
Context-aware conversational assistant grounded in SQL records (`Transaction`, `RecoveryWorkflow`, `Customer`, `AuditLog`, `MetricsService`). Strictly outputs 4 distinct layers:
- **Observed Data:** Raw gateway facts, amount, and customer profile.
- **AI Recommendation:** Suggested recovery strategy and confidence score.
- **Policy Decision:** Deterministic rules evaluated and whether execution was authorized or blocked.
- **Final Outcome:** Settled financial amount or human escalation status (honest *"No record found"* on unknown IDs).

### 6. Backend-Authoritative RBAC
- **`MERCHANT_ADMIN`:** Full control; can modify guardrail policies via `PUT /api/v1/policies` (HTTP 200).
- **`OPERATIONS_AGENT`:** Operations monitoring and case review; policy modifications are blocked on the backend with **HTTP 403 Forbidden**.

### 7. Tamper-Evident Audit Ledger
Chronological, append-only log capturing actor, action, timestamp, and structured payload for every transition.

---

## 4. Empirical 10,000-Transaction Benchmark

RecoverAI includes a statistical benchmark evaluated against **10,000 synthetic Indian merchant payment failures** (deterministic seed 42) across authentic failure distributions:

| Metric | Static Single Retry (Baseline) | RecoverAI (Bounded Agentic) | Measured Impact |
|---|:---:|:---:|:---:|
| **Recovery Rate** | **28.31%** | **64.29%** | **+35.98 pp (Net Lift)** |
| **Total Recovered Revenue** | ₹1,62,75,056.05 | ₹3,69,60,073.06 | **+₹2,06,85,017.01 Incremental GMV** |
| **Wasteful / Failed Retries** | 6,550 | 332 | **6,218 Retries Prevented** |
| **Human Escalations Routed** | 0 (Unchecked) | 2,500 | **100% High-Risk Protected** |
| **Unsafe Actions Blocked** | 0 | 1,689 | **100% Contained (Fraud & Max-Retry)** |

---

## 5. The 5 Deterministic Demo Lab Scenarios

Evaluators can execute all 5 scenarios with 1-click reproducibility in the **Demo Lab**:

```
┌────────────┬───────────────────────────────────────┬──────────────┬──────────────────────────────────────────────────────┐
│ Scenario   │ Trigger & Condition                   │ Final State  │ Financial Outcome                                    │
├────────────┼───────────────────────────────────────┼──────────────┼──────────────────────────────────────────────────────┤
│ Scenario 1 │ ₹4,999 Temporary Bank Decline         │ RECOVERED    │ ₹4,999.00 Settled (Delayed retry executed & captured)│
│ Scenario 2 │ ₹27,000 High Risk / Suspicious Fraud  │ ESCALATED    │ ₹0 Recovered • ₹27,000 Held for Human Review         │
│ Scenario 3 │ ₹3,200 Max Retry Breached (Attempt 3) │ STOPPED      │ ₹0 Recovered • Stopped (Max Attempts Limit Enforced) │
│ Scenario 4 │ Replayed Webhook Event                │ IDEMPOTENT   │ Zero Financial Mutation (Duplicate Dropped)          │
│ Scenario 5 │ Already Settled via Parallel Window   │ RECOVERED    │ Zero Duplicate Execution (Evaluated NO_ACTION)       │
└────────────┴───────────────────────────────────────┴──────────────┴──────────────────────────────────────────────────────┘
```

---

## 6. Seeded Demo Accounts

| Role | Email | Password | Permissions |
|---|---|---|---|
| **Lead Merchant Admin** | `admin@acrobatics.com` | `RecoverAI2026!` | **Full Control:** Policy management, dual signoffs, execution |
| **Operations Agent** | `ops@acrobatics.com` | `RecoverAI2026!` | **Read-Only:** Operations review (**Policy editing blocked with 403**) |

*(1-Click quick-fill buttons are provided on the login page at `http://localhost:5173`.)*

---

## 7. Local Quickstart

### Prerequisites
- Python 3.10+
- Node.js v18+ & npm

### 1. Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000 --reload
```
- API Base: `http://127.0.0.1:8000`
- Interactive Swagger Docs: `http://127.0.0.1:8000/docs`
- Health Endpoint: `http://127.0.0.1:8000/health`

### 2. Run Automated Regression Suite
```bash
cd backend
pytest -v
```
*(All 24 unit, security, RBAC, benchmark, and integration tests pass in ~1.5s)*

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
- Console UI: `http://localhost:5173`

---

## 8. Production Render Deployment

RecoverAI is configured for 1-click infrastructure provisioning on [Render](https://render.com) using [`render.yaml`](file:///C:/Users/pky45/.gemini/antigravity/scratch/recoverai/render.yaml).

### Architecture
- **Web Service (Backend):** Python 3.11 + FastAPI (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`)
- **Managed Database:** PostgreSQL 16 with `asyncpg` async connection pooling
- **Static Site (Frontend):** React 18 + Vite (`npm run build` $\rightarrow$ `./frontend/dist`)

### Required Environment Variables

#### Backend Web Service:
```env
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://user:password@host:5432/recoverai?ssl=require
JWT_SECRET_KEY=<your-secure-random-64-char-string>
FRONTEND_URL=https://recoverai-frontend.onrender.com
RAZORPAY_KEY_ID=rzp_test_recoverai2026
RAZORPAY_KEY_SECRET=sec_recoverai_test_secret_key_2026
RAZORPAY_WEBHOOK_SECRET=whsec_recoverai_super_secret_webhook_2026
```

#### Frontend Static Site:
```env
VITE_API_BASE_URL=https://recoverai-backend.onrender.com
```

---

## 9. Technology Stack

| Layer | Technologies |
|---|---|
| **Backend Core** | Python 3.10+, FastAPI, Pydantic v2, Uvicorn (ASGI) |
| **Database & ORM** | SQLAlchemy 2.0 Async, aiosqlite (Dev), asyncpg (Prod PostgreSQL) |
| **Frontend Console** | React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons |
| **Security & Auth** | Salted PBKDF2 (100k rounds), HMAC-SHA256 JWT, Constant-Time Digest Verification |
| **Gateway Integration**| Razorpay Test Mode API, HMAC-SHA256 Webhook Verification, SHA-256 Idempotency |
| **Testing** | Pytest, Pytest-Asyncio, HTTPX |

---

## 10. License

MIT License. Developed for the **Razorpay AI Builder Buildathon 2026**.
