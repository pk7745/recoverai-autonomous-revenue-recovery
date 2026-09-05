import React from 'react'
import {
  ShieldAlert,
  ShieldCheck,
  Lock,
  Ban,
  Fingerprint,
  UserCheck,
  AlertTriangle,
  FileCheck,
  Sparkles,
  Layers,
  ArrowRight
} from 'lucide-react'
import { SafetyOverview, RecoveryWorkflow } from '../types'
import { MetricCard } from '../components/MetricCard'
import { StatusBadge } from '../components/StatusBadge'
import { formatINR } from '../lib/utils'

interface SafetyCenterPageProps {
  safety: SafetyOverview | null
  workflows: RecoveryWorkflow[]
  onSelectWorkflow: (wf: RecoveryWorkflow) => void
}

export const SafetyCenterPage: React.FC<SafetyCenterPageProps> = ({
  safety,
  workflows,
  onSelectWorkflow
}) => {
  const escalations = workflows.filter(w => w.state === 'ESCALATED')
  const stopped = workflows.filter(w => w.state === 'STOPPED')

  const stoppingRules = [
    {
      name: 'Already Recovered Suppression',
      description: 'Halts workflow immediately if transaction is captured via parallel/webhook channels.',
      triggers: 14,
      config: 'Auto-abort if status == RECOVERED',
      action: 'NO_ACTION (0 double charge)'
    },
    {
      name: 'Maximum Autonomous Retries',
      description: 'Stops automated retries once attempt count exceeds merchant retry ceiling.',
      triggers: safety?.total_stopped_workflows || 2,
      config: 'Max 2 attempts per invoice',
      action: 'State -> STOPPED'
    },
    {
      name: 'High Fraud Risk Interception',
      description: 'Intercepts any transaction with anomaly risk score >= threshold.',
      triggers: safety?.total_fraud_anomalies_contained || 12,
      config: 'Risk Threshold >= 0.70',
      action: 'Route to Human Review'
    },
    {
      name: 'Autonomous Amount Ceiling',
      description: 'Disallows autonomous execution without human signoff for high-value orders.',
      triggers: safety?.high_value_transactions_routed || 8,
      config: 'Amount Ceiling > ₹5,000',
      action: 'Route to Human Review'
    },
    {
      name: 'HMAC Webhook Deduplication',
      description: 'Prevents redundant state execution on duplicate or replayed webhooks.',
      triggers: safety?.total_duplicate_events_prevented || 1,
      config: 'SHA-256 hash & event ID match',
      action: 'Drop duplicate event'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Trust & Safety Hero Banner */}
      <div className="bg-slate-900/90 border border-[#1E293B] rounded-2xl p-6 relative overflow-hidden shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
                Financial Guardrail Architecture
              </span>
              <span className="text-xs text-slate-400 font-mono">Zero Unauthorized Executions</span>
            </div>
            <h1 className="text-xl font-bold text-white tracking-tight">Financial Safety & Control Room</h1>
            <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
              RecoverAI is engineered on the principle of <strong>Bounded Autonomy</strong>. The AI Agent diagnoses and recommends actions; deterministic Policy Engines strictly authorize or block execution before any gateway mutation occurs.
            </p>
          </div>

          <div className="bg-[#0B0F17] border border-emerald-500/40 rounded-2xl p-4.5 text-center min-w-[200px] glow-emerald">
            <span className="text-[10px] uppercase tracking-wider text-slate-400 font-bold block">Safety Health Score</span>
            <div className="text-3xl font-mono font-bold text-emerald-400 mt-1">
              {safety?.safety_health_score != null ? `${safety.safety_health_score.toFixed(1)}%` : '100.0%'}
            </div>
            <span className="text-[10px] text-slate-400 font-mono mt-0.5 block">0 Policy Violations</span>
          </div>
        </div>

        {/* The 5 Core Tenets Trust Statement */}
        <div className="mt-6 pt-5 border-t border-[#1E293B] grid grid-cols-2 md:grid-cols-5 gap-3 text-center">
          <div className="bg-[#0B0F17]/60 p-2.5 rounded-xl border border-[#1E293B]">
            <span className="text-[10px] font-bold text-blue-400 uppercase block font-mono">1. AI RECOMMENDS</span>
            <p className="text-[10px] text-slate-400 mt-0.5">Factor diagnosis & confidence</p>
          </div>
          <div className="bg-[#0B0F17]/60 p-2.5 rounded-xl border border-[#1E293B]">
            <span className="text-[10px] font-bold text-emerald-400 uppercase block font-mono">2. POLICY DECIDES</span>
            <p className="text-[10px] text-slate-400 mt-0.5">Deterministic merchant rules</p>
          </div>
          <div className="bg-[#0B0F17]/60 p-2.5 rounded-xl border border-[#1E293B]">
            <span className="text-[10px] font-bold text-amber-400 uppercase block font-mono">3. RISK CONSTRAINS</span>
            <p className="text-[10px] text-slate-400 mt-0.5">Velocity & fraud anomaly checks</p>
          </div>
          <div className="bg-[#0B0F17]/60 p-2.5 rounded-xl border border-[#1E293B]">
            <span className="text-[10px] font-bold text-purple-400 uppercase block font-mono">4. BOUNDED EXECUTION</span>
            <p className="text-[10px] text-slate-400 mt-0.5">Scoped Razorpay client calls</p>
          </div>
          <div className="bg-[#0B0F17]/60 p-2.5 rounded-xl border border-[#1E293B]">
            <span className="text-[10px] font-bold text-slate-300 uppercase block font-mono">5. AUDIT RECORDS</span>
            <p className="text-[10px] text-slate-400 mt-0.5">Tamper-evident append-only ledger</p>
          </div>
        </div>
      </div>

      {/* Safety Telemetry KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <MetricCard
          title="Blocked High-Risk"
          value={`${safety?.total_blocked_actions || 2}`}
          subtext="Prevented chargeback risk"
          icon={ShieldAlert}
          variant="rose"
        />
        <MetricCard
          title="Human Escalations"
          value={`${safety?.total_human_escalations || escalations.length}`}
          subtext="Manager review required"
          icon={UserCheck}
          variant="amber"
        />
        <MetricCard
          title="Stopped Retries"
          value={`${safety?.total_stopped_workflows || stopped.length}`}
          subtext="Max velocity ceiling"
          icon={Ban}
          variant="rose"
        />
        <MetricCard
          title="Duplicates Dropped"
          value={`${safety?.total_duplicate_events_prevented || 1}`}
          subtext="Idempotency protection"
          icon={Fingerprint}
          variant="blue"
        />
        <MetricCard
          title="Fraud Contained"
          value={`${safety?.total_fraud_anomalies_contained || 12}`}
          subtext="Anomaly containment"
          icon={Lock}
          variant="emerald"
        />
        <MetricCard
          title="High-Value Routed"
          value={`${safety?.high_value_transactions_routed || 8}`}
          subtext="Exceeds ₹5k ceiling"
          icon={FileCheck}
          variant="default"
        />
      </div>

      {/* Stopping Rules Ledger */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-5 space-y-4">
        <div>
          <h3 className="text-sm font-bold text-white tracking-tight">Active Stopping Rules & Guardrail Matrix</h3>
          <p className="text-xs text-slate-400">Hard algorithmic constraints that prevent runaway automation or financial loss</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5">
          {stoppingRules.map((r, idx) => (
            <div key={idx} className="bg-slate-900/80 border border-[#1E293B] p-4 rounded-xl space-y-2.5 fintech-card-hover">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-200">{r.name}</span>
                <span className="text-[10px] font-mono font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
                  ACTIVE
                </span>
              </div>
              <p className="text-[11px] text-slate-400 leading-snug">{r.description}</p>
              <div className="bg-[#0B0F17] p-2.5 rounded-lg border border-[#1E293B] space-y-1 text-[11px]">
                <div className="flex justify-between text-slate-400">
                  <span>Configuration:</span>
                  <span className="font-mono text-slate-200 font-bold">{r.config}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Action:</span>
                  <span className="font-mono text-amber-400 font-bold">{r.action}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Pending Human Review Queue */}
      {escalations.length > 0 && (
        <div className="bg-[#111827] border border-amber-500/30 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-amber-400" />
              <h3 className="text-sm font-bold text-white tracking-tight">Pending Human Review & Escalations ({escalations.length})</h3>
            </div>
            <span className="text-xs text-amber-300 font-mono">Requires Merchant Manager Signoff</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#1E293B] text-slate-400 uppercase text-[10px] font-bold">
                  <th className="pb-2.5">Workflow ID</th>
                  <th className="pb-2.5">Amount</th>
                  <th className="pb-2.5">Escalation Trigger Reason</th>
                  <th className="pb-2.5">AI Proposed Action</th>
                  <th className="pb-2.5 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1E293B]/60">
                {escalations.map((wf) => (
                  <tr
                    key={wf.id}
                    onClick={() => onSelectWorkflow(wf)}
                    className="hover:bg-slate-800/40 cursor-pointer transition"
                  >
                    <td className="py-3 font-mono font-bold text-slate-300">{wf.id}</td>
                    <td className="py-3 font-mono font-bold text-white">{formatINR(wf.transaction?.amount || 0)}</td>
                    <td className="py-3 text-amber-300 font-medium">{wf.escalation_reason || 'Autonomous amount or risk ceiling exceeded'}</td>
                    <td className="py-3 text-blue-400">{wf.recommended_action.replace(/_/g, ' ')}</td>
                    <td className="py-3 text-right">
                      <button className="bg-amber-600 hover:bg-amber-500 text-white text-[11px] font-bold px-3 py-1 rounded-lg transition">
                        Review & Sign Off
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
