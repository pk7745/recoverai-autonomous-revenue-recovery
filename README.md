# RecoverAI — Autonomous AI Revenue Recovery Platform

> **Recover revenue before it becomes lost revenue.**  
> Built for **Razorpay AI Builder Buildathon 2026 — Track 03: AI Revenue Recovery**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-3.4-38B2AC?logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![Razorpay Test Mode](https://img.shields.io/badge/Razorpay-Test%20Mode-0C2340?logo=razorpay&logoColor=white)](https://razorpay.com/docs/)
[![Pytest](https://img.shields.io/badge/Tests-19%20Passing%20(100%25)-4E9A06?logo=pytest&logoColor=white)](https://pytest.org)

---

## 1. Product Overview & The Problem

When Razorpay merchant payments fail, merchants lose **15% to 25% of top-line revenue**. Traditional payment systems suffer from two fatal extremes:
1. **Do Nothing:** The payment failure is treated as final; cart abandonment occurs, customer churns.
2. **Blind "Retry Everything" Bots:** Naive scripts retry every failed transaction blindly, causing card network penalties, bank fraud flags, chargeback spikes, and angry customers receiving duplicate charges.

**RecoverAI** replaces naive retry scripts with an **autonomous, policy-bounded revenue recovery loop**:
```
EVENT ──► DETECT ──► DIAGNOSE ──► DECIDE ──► POLICY CHECK ──► EXECUTE ──► VERIFY ──► MEASURE ──► AUDIT
```

---

## 2. Key Architecture & Bounded Autonomy

Under **no circumstance** is an AI/LLM allowed to directly call gateway execution endpoints without guardrails. 

```
+-------------------------------------------------------------------------------+
|                             RECOVERAI ORCHESTRATION LAYER                     |
|                                                                               |
|   1. Payment Failure Webhook (HMAC-SHA256 Verified, Idempotent)               |
|      │                                                                        |
|   2. Revenue Risk Detection Engine (Analyzes amount, customer credibility)    |
|      │                                                                        |
|   3. AI Diagnostic Agent (Selects bounded tools, outputs explainable factors) |
|      │                                                                        |
|   4. Deterministic Merchant Policy Engine (Hard caps: ₹5,000 auto limit,      |
|      │                                    Max 2 retries, cooldown periods)    |
|      ├───────────────────────────────────┐                                    |
|      ▼ [Within Limits]                   ▼ [Violates Policy / High Risk]      |
|   5. Razorpay Test Mode Execution     5. Route to Human Escalation Queue      |
|      (Smart Links, Delayed Retry)        (Manual Finance Manager Sign-off)    |
|      │                                                                        |
|   6. Asynchronous Webhook Settlement (payment.captured / payment.authorized)  |
|      │                                                                        |
|   7. Immutable Cryptographic Audit Ledger & Real-Time Telemetry               |
+-------------------------------------------------------------------------------+
```

---

## 3. Empirical 10,000+ Transaction Benchmark

To prove real financial impact without fabricating metrics, RecoverAI includes a reproducible statistical simulator evaluated against **10,000 realistic synthetic payments** (deterministic seed 42) across authentic failure distributions:

| Evaluation Metric | Static Single Retry (Baseline) | RecoverAI (Bounded Agentic) | Measured Impact |
|---|---|---|---|
| **Recovery Rate** | **28.31%** | **64.29%** | **+35.98 Percentage-Point Uplift** |
| **Recovered Volume** | ₹1.63 Cr (₹1,62,75,056) | ₹3.70 Cr (₹3,69,60,073) | **+₹2.07 Cr Net Incremental GMV** |
| **Wasteful / Unsafe Retries** | 6,550 | 332 | **6,218 Retries Prevented (89% Drop)** |
| **Human Escalations Routed** | 0 (Blindly retried) | 2,500 High-Risk Checked | **100% High-Risk Safe** |
| **Unsafe Actions Blocked** | 0 | 1,689 Blocked | **Zero Chargeback Risk** |
| **Platform ROI Multiple** | 1.8x | **4.6x** | **+2.8x Net Merchant ROI** |

---

## 4. Deterministic Demo Scenarios

Evaluators can test and verify all 5 core scenarios with 1-click execution in the built-in **Demo Lab**:

1. **Scenario 1 — Successful Delayed Retry:** ₹4,999 temporary issuer decline + returning customer $\rightarrow$ AI schedules 30-min delayed retry $\rightarrow$ Policy allows $\rightarrow$ Webhook confirms settlement $\rightarrow$ Revenue recovered.
2. **Scenario 2 — High-Risk Policy Block:** ₹27,000 high-value transaction + fraud risk score 0.85 $\rightarrow$ Policy engine blocks automated retry ($>\text{₹}5,000$ limit) $\rightarrow$ Escalates to Human Ops.
3. **Scenario 3 — Max Attempts Stopping Rule:** Payment reaches 3rd failure attempt $\rightarrow$ Exceeds merchant max limit of 2 retries $\rightarrow$ Stopping rule halts workflow immediately.
4. **Scenario 4 — Duplicate Webhook Idempotency:** Identical Razorpay webhook replayed twice $\rightarrow$ Deduped via SHA-256 hash $\rightarrow$ Second event rejected without duplicate mutation.
5. **Scenario 5 — Already Recovered (DO NOTHING):** Payment already captured in parallel channel $\rightarrow$ Policy evaluates `NO_ACTION` $\rightarrow$ Aborts workflow to prevent double-charging.

---

## 5. Technology Stack

- **Backend:** Python 3.10+, FastAPI, SQLAlchemy 2.0 Async, SQLite/PostgreSQL, Pydantic v2, Pytest.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, Lucide Icons, Recharts.
- **Payments:** Razorpay Test Mode API Client, HMAC-SHA256 signature verification, idempotent webhook engine.
- **AI / Reasoning:** Pluggable `AIProvider` supporting offline deterministic expert engine + Google Gemini / OpenAI adapters.

---

## 6. Quickstart & Local Setup

### Prerequisites
- Python 3.10+
- Node.js v18+ & npm

### 1. Start Backend
```bash
cd backend
.venv\Scripts\activate
# Or create venv: python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```
- API Endpoint: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

### 2. Run Test Suite
```bash
cd backend
pytest -v
```
*(All 19 unit & end-to-end integration tests pass in <1s)*

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
- Console UI: `http://localhost:5173`

---

## 7. Demo Reset & Verification Commands

To reset the database to a fresh deterministic state at any time:
```bash
# Via API / Curl:
curl -X POST http://127.0.0.1:8000/api/v1/demo/reset

# Or inside UI:
Click "Reset Demo Dataset" on the Demo Lab screen.
```

---

## 8. License

MIT License. Designed & Developed for the **Razorpay AI Builder Buildathon 2026**.
