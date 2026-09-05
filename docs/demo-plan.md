# RecoverAI 5-Minute Buildathon Demo Plan

## Timeline & Narrative

### 0:00 – 0:45: The Problem & The Solution
- **Hook:** "Merchants don't just lose revenue when payments fail — they lose it when systems fail to decide what to do next. Traditional systems either do nothing or blindly retry everything, triggering fraud filters and cardholder frustration."
- **Present:** RecoverAI Revenue Command Center showing real-time **₹38.45 Lakhs Revenue at Risk**, **₹28.10 Lakhs Recovered (73.1% Recovery Rate)**, and live AI activity feed.

### 0:45 – 1:45: The Core AI Loop (Detect -> Diagnose -> Decide -> Policy Check -> Execute)
- Select a failed transaction (`₹4,999` temporary issuer decline, returning customer).
- Trigger AI diagnosis: Show structured factors (Confidence 88%, Low Risk, Allowed by Policy).
- Execute delayed retry -> receive Razorpay `payment.captured` webhook -> state transitions to `RECOVERED` -> Live counters increment.

### 1:45 – 2:45: Bounded Autonomy & Deterministic Policy Safety
- Select high-risk transaction (`₹27,000` velocity anomaly).
- AI suggests intervention, but **Policy Engine Intercepts & Blocks it** because amount > autonomous limit and risk > 0.75.
- Demonstrates Human Escalation queue with manual finance officer review & approval drawer.

### 2:45 – 3:30: Idempotency & Stopping Rules (Do Nothing as a Feature)
- Trigger Duplicate Webhook scenario -> verify SHA-256 event deduping and zero duplicate charges.
- Show Stopping Rule triggered on payment already settled in another window -> system outputs `NO_ACTION`.
- Open **Safety Center** displaying blocked actions, stopped workflows, and zero double-charge guarantee.

### 3:30 – 4:30: Measured 10,000+ Transaction Experimentation Benchmark
- Switch to **Experiments** tab.
- Present statistical benchmark over 10,000 realistic payments:
  - **Baseline (Static Single Retry):** 38.2% recovery rate, ₹14.8L recovered, 3,120 unnecessary retries.
  - **RecoverAI (Policy-Bounded Agentic):** 73.1% recovery rate, ₹28.1L recovered, 89% reduction in wasteful retries.
  - Proven ROI and net merchant profit increase.

### 4:30 – 5:00: Production Architecture & Immutable Audit Ledger
- Walk through **Audit Trail** showing every cryptographic signature, decision factor, and execution timestamp.
- Conclude: "RecoverAI doesn't just predict revenue loss. It closes the loop from detection to safe recovery and measures what it actually recovered."
