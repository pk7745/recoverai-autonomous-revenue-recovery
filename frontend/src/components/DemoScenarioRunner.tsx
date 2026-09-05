import React, { useState } from 'react'
import {
  Play,
  RotateCcw,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  Fingerprint,
  Ban,
  Clock
} from 'lucide-react'
import { apiService } from '../services/api'
import { formatINR } from '../lib/utils'

interface DemoScenarioRunnerProps {
  onScenarioComplete?: () => void
}

interface ScenarioCard {
  id: string
  num: string
  title: string
  subtitle: string
  amount: string
  tag: string
  whatWeTest: string
  input: string
  aiExpectation: string
  policyExpectation: string
  executionExpectation: string
  icon: any
  variant: 'emerald' | 'amber' | 'rose' | 'blue' | 'purple'
}

export const DemoScenarioRunner: React.FC<DemoScenarioRunnerProps> = ({ onScenarioComplete }) => {
  const [runningId, setRunningId] = useState<string | null>(null)
  const [isResetting, setIsResetting] = useState(false)
  const [activeResult, setActiveResult] = useState<{ id: string; data: any } | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  const scenarios: ScenarioCard[] = [
    {
      id: 'successful_delayed_retry',
      num: '01',
      title: 'Successful Delayed Retry',
      subtitle: 'Transient Issuer Downtime Resolution',
      amount: '₹4,999.00',
      tag: 'Bounded Recovery',
      whatWeTest: 'Temporary bank gateway connectivity drop with returning customer credibility.',
      input: '₹4,999 card payment failed with TEMPORARY_ISSUER_DECLINE on Attempt 1.',
      aiExpectation: 'Recommends DELAYED_RETRY with 88% confidence (Outage cooldown factor).',
      policyExpectation: 'Within ₹5k limit & Attempt 1 <= 2 -> ALLOWED.',
      executionExpectation: 'Razorpay Client schedules 30-min retry -> Webhook confirms settlement -> ₹4,999 RECOVERED.',
      icon: Clock,
      variant: 'emerald'
    },
    {
      id: 'high_risk_escalation',
      num: '02',
      title: 'High-Risk Policy Block',
      subtitle: 'Autonomous Ceiling & Anomaly Containment',
      amount: '₹27,000.00',
      tag: 'Policy Safety',
      whatWeTest: 'High-value transaction and fraud risk score triggering deterministic Policy Engine block.',
      input: '₹27,000 card payment with FRAUD_RISK_BLOCK and 0.85 risk score on Attempt 3.',
      aiExpectation: 'May attempt recovery or flag anomaly.',
      policyExpectation: 'Deterministic policy intercepts: Amount > ₹5,000 & Risk >= 0.70 -> OVERRIDDEN_TO_ESCALATE.',
      executionExpectation: 'Autonomous retry BLOCKED. Workflow routed to Human Escalation Queue.',
      icon: ShieldAlert,
      variant: 'amber'
    },
    {
      id: 'max_retries_stopped',
      num: '03',
      title: 'Maximum Attempts Stop',
      subtitle: 'Anti-Spam & Network Penalty Protection',
      amount: '₹12,500.00',
      tag: 'Stopping Rule',
      whatWeTest: 'Stopping Rule enforcement when transaction exceeds allowable retry ceiling.',
      input: 'Payment with Attempt Count = 3 (Exceeds merchant max retry limit of 2).',
      aiExpectation: 'Assesses repeated failure velocity.',
      policyExpectation: 'Attempts 3 > Max 2 -> STOPPED immediately.',
      executionExpectation: 'Hard stop triggered. Zero further retries. Avoids card network penalty fees.',
      icon: Ban,
      variant: 'rose'
    },
    {
      id: 'duplicate_webhook_protection',
      num: '04',
      title: 'Duplicate Webhook Protection',
      subtitle: 'Cryptographic HMAC & Idempotency Guarantee',
      amount: '₹4,999.00',
      tag: 'Idempotency',
      whatWeTest: 'Replay of identical signed payment.captured webhook event.',
      input: 'Duplicate webhook event evt_demo_dup_webhook_12345 delivered twice.',
      aiExpectation: 'N/A (Handled at Webhook Ingress Gate).',
      policyExpectation: 'SHA-256 payload hash & event ID deduplication matches existing record.',
      executionExpectation: 'Second event marked duplicate: true. Dropped idempotently with 0 double-charging.',
      icon: Fingerprint,
      variant: 'blue'
    },
    {
      id: 'already_recovered_no_action',
      num: '05',
      title: 'Already Recovered Safety Gate',
      subtitle: 'Non-Action on Parallel Channel Settlement',
      amount: '₹1,999.00',
      tag: 'Non-Action Safety',
      whatWeTest: 'Payment captured in alternate channel (e.g. offline UPI QR) before recovery executes.',
      input: 'Failed payment where transaction status in database is already RECOVERED.',
      aiExpectation: 'Identifies settled status.',
      policyExpectation: 'Already Recovered Check fails -> Evaluates NO_ACTION / STOP.',
      executionExpectation: 'Aborts workflow immediately. Zero redundant notifications or duplicate charges.',
      icon: ShieldCheck,
      variant: 'purple'
    }
  ]

  const handleRun = async (id: string) => {
    setRunningId(id)
    setErrorMsg(null)
    try {
      const res = await apiService.runDemoScenario(id)
      setActiveResult({ id, data: res })
      if (onScenarioComplete) onScenarioComplete()
    } catch (err: any) {
      setErrorMsg(err?.response?.data?.detail || 'Failed to execute scenario')
    } finally {
      setRunningId(null)
    }
  }

  const handleReset = async () => {
    setIsResetting(true)
    setErrorMsg(null)
    try {
      await apiService.resetDemoData()
      setActiveResult(null)
      if (onScenarioComplete) onScenarioComplete()
    } catch (err: any) {
      setErrorMsg('Failed to reset demo dataset')
    } finally {
      setIsResetting(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex items-center justify-between bg-slate-900/80 border border-[#1E293B] p-5 rounded-2xl">
        <div>
          <div className="flex items-center space-x-2">
            <span className="bg-amber-500/10 text-amber-300 border border-amber-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
              Official Evaluation Suite
            </span>
            <h2 className="text-lg font-bold text-white tracking-tight">Demo Lab — 5 Deterministic Pitch Scenarios</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Execute the 5 core RecoverAI architectural proofs with single-click deterministic repeatability.
          </p>
        </div>

        <button
          onClick={handleReset}
          disabled={isResetting}
          className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 px-3.5 py-2 rounded-xl text-xs font-semibold transition disabled:opacity-50"
        >
          <RotateCcw className={`h-3.5 w-3.5 ${isResetting ? 'animate-spin' : ''}`} />
          <span>Reset Demo Dataset</span>
        </button>
      </div>

      {errorMsg && (
        <div className="bg-rose-500/10 border border-rose-500/30 p-3.5 rounded-xl text-xs text-rose-300">
          {errorMsg}
        </div>
      )}

      {/* Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {scenarios.map((sc) => {
          const Icon = sc.icon
          const isRunning = runningId === sc.id
          const isSelected = activeResult?.id === sc.id

          return (
            <div
              key={sc.id}
              className={`bg-[#111827] border rounded-2xl p-5 flex flex-col justify-between transition-all fintech-card-hover ${
                isSelected
                  ? 'border-blue-500/60 shadow-lg shadow-blue-500/5 bg-slate-900/90'
                  : 'border-[#1E293B]'
              }`}
            >
              <div className="space-y-3.5">
                {/* Header */}
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-bold text-slate-500">{sc.num}</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full border uppercase font-mono bg-slate-800 text-slate-300 border-slate-700">
                    {sc.tag}
                  </span>
                </div>

                <div>
                  <h3 className="text-sm font-bold text-white">{sc.title}</h3>
                  <p className="text-[11px] text-slate-400 mt-0.5">{sc.subtitle}</p>
                </div>

                <div className="bg-[#0B0F17] border border-[#1E293B] p-2.5 rounded-xl flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-400 text-[11px]">Exposure:</span>
                  <strong className="text-white font-bold">{sc.amount}</strong>
                </div>

                {/* Structured Flow Breakdown */}
                <div className="space-y-2 text-[11px] text-slate-300">
                  <div className="bg-slate-950/60 border border-[#1E293B] p-2.5 rounded-lg space-y-1">
                    <span className="text-[10px] font-bold uppercase text-slate-500 block">Input Context</span>
                    <p className="text-slate-300 leading-tight">{sc.input}</p>
                  </div>

                  <div className="bg-slate-950/60 border border-[#1E293B] p-2.5 rounded-lg space-y-1">
                    <span className="text-[10px] font-bold uppercase text-blue-400 block">AI Recommendation</span>
                    <p className="text-slate-300 leading-tight">{sc.aiExpectation}</p>
                  </div>

                  <div className="bg-slate-950/60 border border-[#1E293B] p-2.5 rounded-lg space-y-1">
                    <span className="text-[10px] font-bold uppercase text-emerald-400 block">Policy Gate & Result</span>
                    <p className="text-slate-300 leading-tight">{sc.policyExpectation}</p>
                  </div>
                </div>
              </div>

              {/* Action Trigger */}
              <div className="mt-4 pt-3.5 border-t border-[#1E293B]">
                <button
                  onClick={() => handleRun(sc.id)}
                  disabled={isRunning || runningId !== null}
                  className={`w-full py-2 px-3 rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1.5 ${
                    isSelected
                      ? 'bg-blue-600 text-white hover:bg-blue-500'
                      : 'bg-slate-800 hover:bg-slate-700 text-slate-100 border border-slate-700'
                  } disabled:opacity-50`}
                >
                  <Play className={`h-3.5 w-3.5 ${isRunning ? 'animate-spin' : ''}`} />
                  <span>{isRunning ? 'Executing...' : 'Run Scenario'}</span>
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {/* Live Execution Result Banner */}
      {activeResult && (
        <div className="bg-slate-900 border border-blue-500/40 rounded-2xl p-5 shadow-xl animate-fade-in space-y-3">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300">Live Scenario Execution Telemetry</span>
            </div>
            <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded-full border ${
              activeResult.data.status === 'RECOVERED'
                ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
                : activeResult.data.status === 'ESCALATED'
                ? 'text-amber-300 bg-amber-500/10 border-amber-500/30'
                : activeResult.data.status === 'STOPPED'
                ? 'text-rose-400 bg-rose-500/10 border-rose-500/30'
                : 'text-blue-300 bg-blue-500/10 border-blue-500/30'
            }`}>
              STATUS: {activeResult.data.status || (activeResult.data.duplicate_detected ? 'IDEMPOTENT_IGNORED' : 'COMPLETED')}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="bg-slate-950/70 p-3 rounded-xl border border-[#1E293B]">
              <span className="text-[10px] text-slate-500 uppercase block font-bold">Scenario Triggered</span>
              <strong className="text-white text-xs mt-0.5 block">{activeResult.data.scenario}</strong>
            </div>

            <div className="bg-slate-950/70 p-3 rounded-xl border border-[#1E293B]">
              <span className="text-[10px] text-slate-500 uppercase block font-bold">Financial Outcome</span>
              <strong className={`text-xs font-mono mt-0.5 block ${
                activeResult.data.status === 'RECOVERED' && activeResult.data.recovered_amount > 0
                  ? 'text-emerald-400'
                  : activeResult.data.status === 'ESCALATED'
                  ? 'text-amber-300'
                  : activeResult.data.status === 'STOPPED'
                  ? 'text-rose-400'
                  : 'text-slate-300'
              }`}>
                {activeResult.data.financial_outcome || (
                  activeResult.data.status === 'RECOVERED' && activeResult.data.recovered_amount > 0
                    ? `${formatINR(activeResult.data.recovered_amount)} Settled`
                    : activeResult.data.status === 'ESCALATED'
                    ? `₹0 Recovered • ${formatINR(activeResult.data.exposure_amount || 27000)} Held for Review`
                    : activeResult.data.status === 'STOPPED'
                    ? '₹0 Recovered • Stopped by Policy Guardrail'
                    : 'Zero Financial Mutation'
                )}
              </strong>
            </div>

            <div className="bg-slate-950/70 p-3 rounded-xl border border-[#1E293B]">
              <span className="text-[10px] text-slate-500 uppercase block font-bold">Subsystem Explanation</span>
              <p className="text-slate-300 text-[11px] leading-tight mt-0.5">{activeResult.data.explanation}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
