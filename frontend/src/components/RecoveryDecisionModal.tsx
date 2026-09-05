import React from 'react'
import {
  X,
  BrainCircuit,
  ShieldCheck,
  Zap,
  Clock,
  Smartphone,
  CreditCard,
  ShieldAlert,
  UserCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  Check,
  Ban,
  Lock,
  ArrowRight,
  Sparkles,
  Layers,
  HelpCircle
} from 'lucide-react'
import { RecoveryWorkflow } from '../types'
import { StatusBadge } from './StatusBadge'
import { formatINR, formatRelativeTime } from '../lib/utils'

interface RecoveryDecisionModalProps {
  workflow: RecoveryWorkflow | null
  onClose: () => void
  onPlan: (id: string) => Promise<void>
  onExecute: (id: string) => Promise<void>
  onApprove: (id: string) => Promise<void>
  onStop: (id: string) => Promise<void>
  isProcessing: boolean
}

export const RecoveryDecisionModal: React.FC<RecoveryDecisionModalProps> = ({
  workflow,
  onClose,
  onPlan,
  onExecute,
  onApprove,
  onStop,
  isProcessing
}) => {
  if (!workflow) return null

  const txn = workflow.transaction
  const cust = txn?.customer
  const reasoning = workflow.ai_reasoning
  const policy = workflow.policy_evaluation

  const getFactorIcon = (icon?: string) => {
    switch (icon) {
      case 'clock': return <Clock className="h-3.5 w-3.5 text-blue-400" />
      case 'smartphone': return <Smartphone className="h-3.5 w-3.5 text-purple-400" />
      case 'credit-card': return <CreditCard className="h-3.5 w-3.5 text-amber-400" />
      case 'shield-alert': return <ShieldAlert className="h-3.5 w-3.5 text-rose-400" />
      case 'user-check': return <UserCheck className="h-3.5 w-3.5 text-emerald-400" />
      default: return <Zap className="h-3.5 w-3.5 text-blue-400" />
    }
  }

  // Decision trace steps showing 9 explicit subsystem layers
  const traceSteps = [
    { name: '1. EVENT', layer: 'Gateway Feed', state: txn?.failure_code || 'Payment Failed' },
    { name: '2. EVIDENCE', layer: 'Context Engine', state: `Attempt ${txn?.attempts_count || 1} • ${cust?.risk_tier || 'LOW'} Risk` },
    { name: '3. DIAGNOSIS', layer: 'AI Agent', state: workflow.failure_category },
    { name: '4. RECOMMEND', layer: 'AI Agent', state: workflow.recommended_action !== 'NO_ACTION' ? workflow.recommended_action.replace(/_/g, ' ') : 'Evaluate' },
    { name: '5. RISK SCORE', layer: 'Risk Engine', state: `Risk: ${(workflow.risk_score || 0).toFixed(2)}` },
    { name: '6. POLICY GATE', layer: 'Policy Engine', state: policy?.status || (workflow.state === 'ESCALATED' ? 'Ceiling/Risk Triggered' : 'Evaluated') },
    { name: '7. DECISION', layer: 'Policy Engine', state: workflow.state === 'ESCALATED' ? 'BLOCKED -> ESCALATE' : (workflow.state === 'STOPPED' ? 'BLOCKED -> STOP' : (workflow.state === 'RECOVERED' || workflow.state === 'POLICY_APPROVED' ? 'AUTHORIZED' : 'Pending')) },
    { name: '8. EXECUTION', layer: 'Razorpay Client', state: workflow.state === 'RECOVERED' ? 'Settled (₹' + (workflow.recovered_amount || txn?.amount || 0).toLocaleString() + ')' : (workflow.state === 'ESCALATED' ? 'Held for Human Signoff' : (workflow.state === 'STOPPED' ? 'Suppressed (₹0 Mutated)' : 'Bounded Dispatch')) },
    { name: '9. AUDIT', layer: 'Ledger Engine', state: 'Tamper-Evident Record' }
  ]

  const getFinalDecisionBadge = () => {
    if (workflow.state === 'RECOVERED') return <span className="bg-emerald-500/15 text-emerald-400 border border-emerald-500/40 text-xs px-3 py-1 rounded-full font-bold uppercase font-mono">AUTHORIZED & RECOVERED</span>
    if (workflow.state === 'ESCALATED') return <span className="bg-amber-500/15 text-amber-400 border border-amber-500/40 text-xs px-3 py-1 rounded-full font-bold uppercase font-mono">HUMAN REVIEW REQUIRED</span>
    if (workflow.state === 'STOPPED') return <span className="bg-rose-500/15 text-rose-400 border border-rose-500/40 text-xs px-3 py-1 rounded-full font-bold uppercase font-mono">BLOCKED & STOPPED</span>
    if (workflow.state === 'POLICY_APPROVED') return <span className="bg-blue-500/15 text-blue-400 border border-blue-500/40 text-xs px-3 py-1 rounded-full font-bold uppercase font-mono">AUTHORIZED BY POLICY</span>
    return <span className="bg-slate-800 text-slate-300 border border-slate-700 text-xs px-3 py-1 rounded-full font-bold uppercase font-mono">DIAGNOSIS PENDING</span>
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-[#111827] border border-[#1E293B] rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="px-6 py-3.5 border-b border-[#1E293B] flex items-center justify-between bg-slate-900/60">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-blue-600/15 border border-blue-500/30 text-blue-400">
              <BrainCircuit className="h-4.5 w-4.5" />
            </div>
            <div>
              <div className="flex items-center space-x-2.5">
                <h3 className="text-sm font-bold text-white tracking-tight">Recovery Decision Studio</h3>
                <StatusBadge status={workflow.state} />
              </div>
              <p className="text-[11px] text-slate-400 font-mono mt-0.5">Workflow: {workflow.id} • Txn: {workflow.transaction_id}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
          >
            <X className="h-4.5 w-4.5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 space-y-5 overflow-y-auto max-h-[calc(92vh-130px)]">
          {/* Section 1: Transaction Context */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-[#0B0F17]/80 border border-[#1E293B] rounded-xl p-4 space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Transaction Profile</span>
              <div className="flex items-baseline justify-between">
                <span className="text-2xl font-bold font-mono text-white">{formatINR(txn?.amount || 0)}</span>
                <span className="text-xs text-slate-400 font-mono">{txn?.payment_method?.toUpperCase()} • Attempt {txn?.attempts_count}</span>
              </div>
              <div className="text-xs text-slate-300 bg-rose-500/10 border border-rose-500/20 p-2 rounded-lg">
                <strong className="text-rose-400">Failure Code:</strong> {txn?.failure_code}
                <p className="text-[11px] text-slate-400 mt-0.5">{txn?.failure_reason}</p>
              </div>
            </div>

            <div className="bg-[#0B0F17]/80 border border-[#1E293B] rounded-xl p-4 space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Customer Credibility</span>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white">{cust?.name || 'Customer'}</span>
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border uppercase font-mono ${cust?.is_returning ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-slate-800 text-slate-400 border-slate-700'}`}>
                  {cust?.is_returning ? 'Returning Customer' : 'New Customer'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                <div className="bg-slate-900/90 border border-[#1E293B] p-2 rounded-lg">
                  <span className="text-[10px] text-slate-500 block">Past Successes</span>
                  <strong className="text-emerald-400 font-mono">{cust?.total_successful_payments} settled</strong>
                </div>
                <div className="bg-slate-900/90 border border-[#1E293B] p-2 rounded-lg">
                  <span className="text-[10px] text-slate-500 block">Past Failures</span>
                  <strong className="text-rose-400 font-mono">{cust?.total_failed_payments} failed</strong>
                </div>
              </div>
            </div>
          </div>

          {/* Section 2: AI Diagnostic Recommendation */}
          <div className="bg-blue-950/15 border border-blue-500/30 rounded-xl p-5 space-y-3.5">
            <div className="flex items-center justify-between border-b border-blue-500/20 pb-2.5">
              <div className="flex items-center space-x-2">
                <BrainCircuit className="h-4 w-4 text-blue-400" />
                <span className="text-xs font-bold uppercase tracking-wider text-blue-400">AI / Expert Recommendation</span>
              </div>
              <div className="flex items-center space-x-2 text-xs">
                <span className="text-slate-400 text-[11px]">Diagnostic Confidence:</span>
                <span className="font-mono font-bold text-blue-300">{(workflow.ai_confidence * 100).toFixed(0)}%</span>
              </div>
            </div>

            {reasoning ? (
              <div className="space-y-3">
                <div className="bg-slate-900/90 border border-blue-500/20 p-3 rounded-lg flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-white block">Proposed Strategy: {reasoning.recommended_intervention.replace(/_/g, ' ')}</span>
                    <p className="text-[11px] text-slate-400 mt-0.5">{reasoning.summary}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] text-slate-500 uppercase block">Expected Recovery</span>
                    <span className="text-xs font-mono font-bold text-emerald-400">{formatINR(reasoning.expected_recovery_amount)}</span>
                  </div>
                </div>

                {/* Signals Breakdown */}
                <div className="space-y-1.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Diagnostic Decision Factors</span>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {reasoning.factors.map((f, idx) => (
                      <div key={idx} className="bg-slate-900/70 border border-[#1E293B] p-2.5 rounded-lg flex items-start space-x-2">
                        <div className="p-1 rounded bg-slate-800 shrink-0 mt-0.5">
                          {getFactorIcon(f.icon)}
                        </div>
                        <div>
                          <span className="text-xs font-semibold text-slate-200 block">{f.title || f.factor_name || 'Factor'}</span>
                          <p className="text-[10px] text-slate-400 leading-snug">{f.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <p className="text-[10px] text-blue-300/70 italic flex items-center space-x-1">
                  <ShieldCheck className="h-3 w-3" />
                  <span>Recommendation only. AI cannot execute financial operations without passing deterministic policy validation.</span>
                </p>
              </div>
            ) : (
              <div className="p-4 text-center space-y-2">
                <p className="text-xs text-slate-400">Diagnostic plan not yet generated for this workflow.</p>
                <button
                  onClick={() => onPlan(workflow.id)}
                  disabled={isProcessing}
                  className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition"
                >
                  Generate AI Plan
                </button>
              </div>
            )}
          </div>

          {/* Section 3: Deterministic Policy Gate & Final Authorization */}
          <div className="bg-slate-900/90 border border-[#1E293B] rounded-xl p-5 space-y-3.5">
            <div className="flex items-center justify-between border-b border-[#1E293B] pb-2.5">
              <div className="flex items-center space-x-2">
                <Lock className="h-4 w-4 text-emerald-400" />
                <span className="text-xs font-bold uppercase tracking-wider text-slate-300">Deterministic Policy Gate</span>
              </div>
              <div>
                {getFinalDecisionBadge()}
              </div>
            </div>

            {policy ? (
              <div className="space-y-2">
                <div className="grid grid-cols-1 gap-1.5">
                  {(policy.checks || []).map((c, idx) => (
                    <div key={idx} className="flex items-center justify-between text-xs py-1.5 px-3 rounded-lg bg-slate-950/60 border border-[#1E293B]/80">
                      <div className="flex items-center space-x-2">
                        {c.passed ? (
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                        ) : (
                          <XCircle className="h-3.5 w-3.5 text-rose-400 shrink-0" />
                        )}
                        <span className="font-semibold text-slate-200">{c.rule_description}</span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">{c.details}</span>
                    </div>
                  ))}
                </div>

                {policy.rejection_reason && (
                  <div className="bg-amber-500/10 border border-amber-500/30 p-2.5 rounded-lg text-xs text-amber-300 flex items-center space-x-2">
                    <AlertTriangle className="h-4 w-4 shrink-0" />
                    <span><strong>Policy Decision:</strong> {policy.rejection_reason}</span>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">Policy checks will execute upon planning.</p>
            )}
          </div>

          {/* Section 4: Decision Trace Timeline */}
          <div className="bg-slate-900/60 border border-[#1E293B] rounded-xl p-4 space-y-2.5">
            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Causal Decision Trace (Subsystem Attribution)</span>
            <div className="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-9 gap-1.5 text-center">
              {traceSteps.map((st, sIdx) => (
                <div key={sIdx} className="bg-slate-950/60 border border-[#1E293B] p-2 rounded-lg space-y-1">
                  <span className="text-[10px] font-mono font-bold text-blue-400 block">{st.name}</span>
                  <span className="text-[9px] text-slate-400 block">{st.layer}</span>
                  <span className="text-[9px] font-semibold text-slate-300 block truncate" title={st.state}>{st.state}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Modal Footer Actions */}
        <div className="px-6 py-3.5 border-t border-[#1E293B] bg-slate-900/80 flex items-center justify-between">
          <div className="text-[11px] text-slate-400 font-mono">
            Updated: {formatRelativeTime(workflow.updated_at)}
          </div>

          <div className="flex items-center space-x-2.5">
            <button
              onClick={() => onStop(workflow.id)}
              disabled={isProcessing || workflow.state === 'STOPPED' || workflow.state === 'RECOVERED'}
              className="px-3 py-1.5 border border-rose-500/30 text-rose-300 hover:bg-rose-500/10 rounded-lg text-xs font-semibold transition disabled:opacity-30"
            >
              Stop Workflow
            </button>

            {workflow.state === 'ESCALATED' && (
              <button
                onClick={() => onApprove(workflow.id)}
                disabled={isProcessing}
                className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 disabled:opacity-50"
              >
                <Check className="h-3.5 w-3.5" />
                <span>Human Signoff & Execute</span>
              </button>
            )}

            {workflow.state === 'POLICY_APPROVED' && (
              <button
                onClick={() => onExecute(workflow.id)}
                disabled={isProcessing}
                className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 disabled:opacity-50"
              >
                <Play className="h-3.5 w-3.5" />
                <span>Execute Recovery</span>
              </button>
            )}

            {workflow.state === 'PAYMENT_FAILED' && (
              <button
                onClick={() => onPlan(workflow.id)}
                disabled={isProcessing}
                className="px-4 py-1.5 bg-purple-600 hover:bg-purple-500 text-white rounded-lg text-xs font-semibold transition flex items-center space-x-1.5 disabled:opacity-50"
              >
                <BrainCircuit className="h-3.5 w-3.5" />
                <span>Diagnose & Plan</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
