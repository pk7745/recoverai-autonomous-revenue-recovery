import React, { useState, useEffect } from 'react'
import {
  Layers,
  ShoppingCart,
  Repeat,
  Building2,
  CreditCard,
  Mic,
  Handshake,
  Zap,
  Play,
  CheckCircle2,
  Clock,
  AlertTriangle,
  RefreshCw,
  Sparkles,
  ShieldCheck,
  PhoneCall,
  FileText,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Volume2
} from 'lucide-react'
import { api } from '../services/api'
import {
  ProgramsOverviewResponse,
  CheckoutSessionItem,
  SubscriptionItem,
  ReceivableInvoiceItem,
  MandateItem,
  VoiceRecoverySessionItem,
  PromiseToPayItem
} from '../types'
import { formatINR } from '../lib/utils'

interface RecoveryProgramsPageProps {
  onSelectWorkflow?: (workflowId: string) => void
}

export const RecoveryProgramsPage: React.FC<RecoveryProgramsPageProps> = () => {
  const [activeTab, setActiveTab] = useState<'checkout' | 'subscription' | 'receivables' | 'mandates' | 'voice' | 'promises'>('checkout')
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [overview, setOverview] = useState<ProgramsOverviewResponse | null>(null)
  
  // Entity states
  const [checkoutSessions, setCheckoutSessions] = useState<CheckoutSessionItem[]>([])
  const [subscriptions, setSubscriptions] = useState<SubscriptionItem[]>([])
  const [receivables, setReceivables] = useState<ReceivableInvoiceItem[]>([])
  const [mandates, setMandates] = useState<MandateItem[]>([])
  const [voiceSessions, setVoiceSessions] = useState<VoiceRecoverySessionItem[]>([])
  const [promises, setPromises] = useState<PromiseToPayItem[]>([])

  // Modal / details viewer
  const [selectedScript, setSelectedScript] = useState<VoiceRecoverySessionItem | null>(null)
  const [toastMessage, setToastMessage] = useState<string | null>(null)

  const showToast = (msg: string) => {
    setToastMessage(msg)
    setTimeout(() => setToastMessage(null), 4000)
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const [ov, chk, sub, rec, man, voc, ptp] = await Promise.all([
        api.getProgramsOverview().catch(() => null),
        api.getCheckoutSessions().catch(() => []),
        api.getSubscriptions().catch(() => []),
        api.getReceivables().catch(() => []),
        api.getMandates().catch(() => []),
        api.getVoiceSessions().catch(() => []),
        api.getPromisesToPay().catch(() => [])
      ])
      if (ov) setOverview(ov)
      setCheckoutSessions(chk)
      setSubscriptions(sub)
      setReceivables(rec)
      setMandates(man)
      setVoiceSessions(voc)
      setPromises(ptp)
    } catch (err) {
      console.error('Error loading programs data:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  // Program Handlers
  const handlePlanCheckout = async (sessionId: string) => {
    setActionLoading(`plan_chk_${sessionId}`)
    try {
      await api.planCheckout(sessionId)
      showToast(`AI diagnostic plan generated for checkout session ${sessionId}`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleExecuteCheckout = async (sessionId: string) => {
    setActionLoading(`exec_chk_${sessionId}`)
    try {
      await api.executeCheckout(sessionId)
      showToast(`[SIMULATED] Checkout recovery incentive dispatched for ${sessionId}`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handlePlanSubscription = async (subId: string) => {
    setActionLoading(`plan_sub_${subId}`)
    try {
      await api.planSubscription(subId)
      showToast(`AI dunning cycle computed for subscription ${subId}`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleExecuteSubscription = async (subId: string) => {
    setActionLoading(`exec_sub_${subId}`)
    try {
      await api.executeSubscription(subId)
      showToast(`[SIMULATED] Smart dunning sequence dispatched for ${subId}`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handlePlanReceivable = async (invId: string) => {
    setActionLoading(`plan_rec_${invId}`)
    try {
      await api.planReceivable(invId)
      showToast(`Dynamic B2B chasing plan generated for invoice ${invId}`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleExecuteReceivable = async (invId: string) => {
    setActionLoading(`exec_rec_${invId}`)
    try {
      await api.executeReceivable(invId)
      showToast(`[SIMULATED] Tone-adaptive chaser dispatched for ${invId}`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handlePlanMandate = async (manId: string) => {
    setActionLoading(`plan_man_${manId}`)
    try {
      await api.planMandate(manId)
      showToast(`Optimal clearing window calculated for mandate ${manId}`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleExecuteMandate = async (manId: string) => {
    setActionLoading(`exec_man_${manId}`)
    try {
      await api.executeMandate(manId)
      showToast(`[SIMULATED] Auto-debit retry presented for ${manId}`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handlePlanVoice = async (vocId: string) => {
    setActionLoading(`plan_voc_${vocId}`)
    try {
      await api.planVoice(vocId)
      showToast(`Hinglish conversational script generated for voice session ${vocId}`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleExecuteVoice = async (vocId: string) => {
    setActionLoading(`exec_voc_${vocId}`)
    try {
      await api.executeVoice(vocId)
      showToast(`[SIMULATED] Outbound Hinglish voice call simulated for ${vocId}`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handlePlanPromise = async (ptpId: string) => {
    setActionLoading(`plan_ptp_${ptpId}`)
    try {
      await api.planPromise(ptpId)
      showToast(`SLA tracking and reminder schedule activated for PTP ${ptpId}`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleFulfillPromise = async (ptpId: string) => {
    setActionLoading(`ful_ptp_${ptpId}`)
    try {
      await api.fulfillPromise(ptpId)
      showToast(`Promise ${ptpId} marked FULFILLED! Debtor score updated.`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleBreachPromise = async (ptpId: string) => {
    setActionLoading(`brk_ptp_${ptpId}`)
    try {
      await api.breachPromise(ptpId)
      showToast(`Promise ${ptpId} breached! Automated escalation triggered.`)
      await loadData()
    } catch (err: any) {
      showToast(`Error: ${err.message}`)
    } finally {
      setActionLoading(null)
    }
  }

  const programTabs = [
    { id: 'checkout', label: 'Checkout Drop-off', icon: ShoppingCart, count: checkoutSessions.length, badge: 'Cart Recapture' },
    { id: 'subscription', label: 'Subscription Dunning', icon: Repeat, count: subscriptions.length, badge: 'Recurring Retention' },
    { id: 'receivables', label: 'B2B Receivables', icon: Building2, count: receivables.length, badge: 'Invoice Chaser' },
    { id: 'mandates', label: 'Mandate Sequencer', icon: CreditCard, count: mandates.length, badge: 'RBI 3-Cap Guarded' },
    { id: 'voice', label: 'Hinglish Voice Recovery', icon: Mic, count: voiceSessions.length, badge: 'AI Conversational' },
    { id: 'promises', label: 'Promise-to-Pay (PTP)', icon: Handshake, count: promises.length, badge: 'SLA Commitment' }
  ]

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 bg-emerald-950/90 border border-emerald-500/40 text-emerald-200 px-4 py-3 rounded-xl shadow-2xl backdrop-blur-md text-xs font-semibold flex items-center space-x-2 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/80 border border-[#1E293B] p-6 rounded-2xl backdrop-blur-md">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Razorpay Buildathon 2026
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              7 Autonomous Programs Active
            </span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight mt-2 flex items-center space-x-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            <span>RecoverAI Revenue Recovery Programs</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl">
            Autonomous multi-modal revenue recapture pipelines across checkout drop-offs, subscriptions, B2B invoices, recurring mandates, conversational Hinglish voice agents, and commitment trackers.
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={loading}
          className="flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-4 py-2.5 rounded-xl text-xs font-semibold transition disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Sync Programs</span>
        </button>
      </div>

      {/* KPI Overview Strip */}
      {overview && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Active Recovery Pipelines</span>
            <div className="text-2xl font-bold text-white mt-1">{overview.total_active_pipelines}</div>
            <span className="text-[10px] text-indigo-400 mt-1 inline-flex items-center">
              <Zap className="w-3 h-3 mr-1" /> Autonomous AI Execution
            </span>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Total Recaptured Value</span>
            <div className="text-2xl font-bold text-emerald-400 mt-1">{formatINR(overview.total_recovered_inr)}</div>
            <span className="text-[10px] text-slate-400 mt-1 inline-flex items-center">
              <TrendingUp className="w-3 h-3 mr-1 text-emerald-400" /> Razorpay Test Mode & Simulated
            </span>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Voice Dialect Modules</span>
            <div className="text-2xl font-bold text-amber-400 mt-1">{overview.programs.voice?.total_records || voiceSessions.length}</div>
            <span className="text-[10px] text-slate-400 mt-1">Hinglish NCR / Mumbai dialects</span>
          </div>
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl">
            <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Policy Engine Guardrails</span>
            <div className="text-2xl font-bold text-sky-400 mt-1">100%</div>
            <span className="text-[10px] text-slate-400 mt-1">RBI 3-Cap & TRAI Time Bounded</span>
          </div>
        </div>
      )}

      {/* Program Selector Tabs */}
      <div className="flex flex-wrap gap-2 border-b border-slate-800 pb-2">
        {programTabs.map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2.5 rounded-xl text-xs font-medium transition-all ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/25 border border-indigo-500'
                  : 'bg-slate-900/80 hover:bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                isActive ? 'bg-indigo-800 text-indigo-200' : 'bg-slate-800 text-slate-400'
              }`}>
                {tab.count}
              </span>
            </button>
          )
        })}
      </div>

      {/* Tab 1: Checkout Drop-off */}
      {activeTab === 'checkout' && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Program 2 — Checkout Drop-off Recovery</h3>
              <p className="text-xs text-slate-400 mt-0.5">Recaptures abandoned carts by synthesizing drop-off stage, friction telemetry, and buyer return history into targeted recovery nudges.</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Deterministic Bounded
            </span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800 font-semibold">
                  <tr>
                    <th className="p-4">Session ID</th>
                    <th className="p-4">Customer</th>
                    <th className="p-4">Cart Value</th>
                    <th className="p-4">Exit Step</th>
                    <th className="p-4">Friction Root Cause</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Autonomous Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {checkoutSessions.map((chk) => (
                    <tr key={chk.id} className="hover:bg-slate-800/40 transition">
                      <td className="p-4 font-mono text-indigo-400 font-medium">{chk.id}</td>
                      <td className="p-4">
                        <div className="font-medium text-white">{chk.customer_name}</div>
                        <div className="text-[10px] text-slate-400">{chk.customer_email}</div>
                      </td>
                      <td className="p-4 font-bold text-white">{formatINR(chk.cart_value)}</td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                          {chk.exit_step}
                        </span>
                      </td>
                      <td className="p-4 text-slate-300">{chk.detected_friction}</td>
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          chk.recovery_status === 'RECOVERY_INITIATED' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                          chk.recovery_status === 'RECOVERED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                          'bg-slate-800 text-slate-400'
                        }`}>
                          {chk.recovery_status}
                        </span>
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <button
                          onClick={() => handlePlanCheckout(chk.id)}
                          disabled={actionLoading === `plan_chk_${chk.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold transition border border-slate-700 disabled:opacity-50"
                        >
                          <Sparkles className="w-3 h-3 inline mr-1 text-indigo-400" />
                          Plan AI
                        </button>
                        <button
                          onClick={() => handleExecuteCheckout(chk.id)}
                          disabled={actionLoading === `exec_chk_${chk.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-[11px] font-semibold transition shadow-md shadow-indigo-600/20 disabled:opacity-50"
                        >
                          <Play className="w-3 h-3 inline mr-1" />
                          Simulate Nudge
                        </button>
                      </td>
                    </tr>
                  ))}
                  {checkoutSessions.length === 0 && (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">No checkout drop-off records found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Subscriptions */}
      {activeTab === 'subscription' && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Program 3 — Failed-Subscription Smart Dunning</h3>
              <p className="text-xs text-slate-400 mt-0.5">Enforces 24-hour retry cooldowns, aligns debits with customer payroll windows, and dispatches dynamic payment update links.</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              Cooldown Protected
            </span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800 font-semibold">
                  <tr>
                    <th className="p-4">Subscription ID</th>
                    <th className="p-4">Subscriber</th>
                    <th className="p-4">Plan & Amount</th>
                    <th className="p-4">Billing Interval</th>
                    <th className="p-4">Retry Attempts</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Autonomous Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {subscriptions.map((sub) => (
                    <tr key={sub.id} className="hover:bg-slate-800/40 transition">
                      <td className="p-4 font-mono text-emerald-400 font-medium">{sub.id}</td>
                      <td className="p-4">
                        <div className="font-medium text-white">{sub.customer_name}</div>
                        <div className="text-[10px] text-slate-400">{sub.customer_email}</div>
                      </td>
                      <td className="p-4">
                        <div className="font-bold text-white">{formatINR(sub.recurring_amount)}</div>
                        <div className="text-[10px] text-slate-400">{sub.plan_name}</div>
                      </td>
                      <td className="p-4 font-mono text-[11px] uppercase text-slate-300">{sub.billing_interval}</td>
                      <td className="p-4 font-mono text-[11px] text-amber-400">{sub.failed_attempts} / {sub.max_retries}</td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          {sub.status}
                        </span>
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <button
                          onClick={() => handlePlanSubscription(sub.id)}
                          disabled={actionLoading === `plan_sub_${sub.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold transition border border-slate-700 disabled:opacity-50"
                        >
                          <Sparkles className="w-3 h-3 inline mr-1 text-emerald-400" />
                          Plan Dunning
                        </button>
                        <button
                          onClick={() => handleExecuteSubscription(sub.id)}
                          disabled={actionLoading === `exec_sub_${sub.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-semibold transition shadow-md shadow-emerald-600/20 disabled:opacity-50"
                        >
                          <Play className="w-3 h-3 inline mr-1" />
                          Execute Retry
                        </button>
                      </td>
                    </tr>
                  ))}
                  {subscriptions.length === 0 && (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">No subscription records found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: B2B Receivables */}
      {activeTab === 'receivables' && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Program 4 — B2B Receivables Dynamic Chaser</h3>
              <p className="text-xs text-slate-400 mt-0.5">Multi-stakeholder tone-adaptive chasing across Gentle Reminder, Formal Follow-up, and Executive Escalation with dynamic payment links.</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
              Aging Aware
            </span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800 font-semibold">
                  <tr>
                    <th className="p-4">Invoice #</th>
                    <th className="p-4">Debtor Client</th>
                    <th className="p-4">Amount Due</th>
                    <th className="p-4">Aging Days</th>
                    <th className="p-4">Chasing Stage</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Autonomous Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {receivables.map((inv) => (
                    <tr key={inv.id} className="hover:bg-slate-800/40 transition">
                      <td className="p-4 font-mono text-amber-400 font-medium">{inv.invoice_number}</td>
                      <td className="p-4">
                        <div className="font-medium text-white">{inv.customer_name}</div>
                        <div className="text-[10px] text-slate-400">{inv.customer_email}</div>
                      </td>
                      <td className="p-4 font-bold text-white">{formatINR(inv.invoice_amount)}</td>
                      <td className="p-4">
                        <span className={`font-mono text-xs font-bold ${
                          inv.overdue_days > 40 ? 'text-rose-400' : inv.overdue_days > 15 ? 'text-amber-400' : 'text-emerald-400'
                        }`}>
                          {inv.overdue_days} days
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                          {inv.chasing_stage}
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                          {inv.status}
                        </span>
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <button
                          onClick={() => handlePlanReceivable(inv.id)}
                          disabled={actionLoading === `plan_rec_${inv.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold transition border border-slate-700 disabled:opacity-50"
                        >
                          <Sparkles className="w-3 h-3 inline mr-1 text-amber-400" />
                          Plan Chaser
                        </button>
                        <button
                          onClick={() => handleExecuteReceivable(inv.id)}
                          disabled={actionLoading === `exec_rec_${inv.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-[11px] font-semibold transition shadow-md shadow-amber-600/20 disabled:opacity-50"
                        >
                          <Play className="w-3 h-3 inline mr-1" />
                          Dispatch Chaser
                        </button>
                      </td>
                    </tr>
                  ))}
                  {receivables.length === 0 && (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">No B2B receivables records found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Mandates */}
      {activeTab === 'mandates' && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Program 5 — Mandate Retry Sequencer</h3>
              <p className="text-xs text-slate-400 mt-0.5">Strictly enforces RBI 3-attempt hard caps on UPI AutoPay and eNACH debits, preventing clearing penalty fees through intelligent liquidity window prediction.</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
              RBI Hard Cap Enforced
            </span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800 font-semibold">
                  <tr>
                    <th className="p-4">Mandate ID</th>
                    <th className="p-4">Holder</th>
                    <th className="p-4">Type</th>
                    <th className="p-4">Scheduled Debit</th>
                    <th className="p-4">RBI Retry Count</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Autonomous Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {mandates.map((m) => (
                    <tr key={m.id} className="hover:bg-slate-800/40 transition">
                      <td className="p-4 font-mono text-rose-400 font-medium">{m.id}</td>
                      <td className="p-4 font-medium text-white">{m.customer_name}</td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono text-[10px]">
                          {m.mandate_type}
                        </span>
                      </td>
                      <td className="p-4 font-bold text-white">{formatINR(m.scheduled_amount)}</td>
                      <td className="p-4">
                        <span className={`font-mono text-xs font-bold ${
                          m.attempt_number >= 3 ? 'text-rose-400' : 'text-emerald-400'
                        }`}>
                          {m.attempt_number} / {m.max_attempts} (RBI Hard Cap)
                        </span>
                      </td>
                      <td className="p-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/10 text-sky-400 border border-sky-500/20">
                          {m.status}
                        </span>
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <button
                          onClick={() => handlePlanMandate(m.id)}
                          disabled={actionLoading === `plan_man_${m.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold transition border border-slate-700 disabled:opacity-50"
                        >
                          <Sparkles className="w-3 h-3 inline mr-1 text-rose-400" />
                          Compute Slot
                        </button>
                        <button
                          onClick={() => handleExecuteMandate(m.id)}
                          disabled={actionLoading === `exec_man_${m.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-[11px] font-semibold transition shadow-md shadow-rose-600/20 disabled:opacity-50"
                        >
                          <Play className="w-3 h-3 inline mr-1" />
                          Simulate Debit
                        </button>
                      </td>
                    </tr>
                  ))}
                  {mandates.length === 0 && (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">No mandate records found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 5: Hinglish Voice Recovery */}
      {activeTab === 'voice' && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Program 6 — Hinglish Voice Recovery Agent</h3>
              <p className="text-xs text-slate-400 mt-0.5">Empathetic conversational outreach using authentic Indian regional dialects (Delhi NCR, Mumbai) with real-time sentiment tracking and TRAI 9am-8pm IST time constraints.</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              TRAI Compliant
            </span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800 font-semibold">
                  <tr>
                    <th className="p-4">Session ID</th>
                    <th className="p-4">Debtor Customer</th>
                    <th className="p-4">Phone & Dialect</th>
                    <th className="p-4">Call Status</th>
                    <th className="p-4">Detected Intent</th>
                    <th className="p-4">Script Preview</th>
                    <th className="p-4 text-right">Autonomous Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {voiceSessions.map((v) => (
                    <tr key={v.id} className="hover:bg-slate-800/40 transition">
                      <td className="p-4 font-mono text-cyan-400 font-medium">{v.id}</td>
                      <td className="p-4 font-medium text-white">{v.customer_name}</td>
                      <td className="p-4">
                        <div className="font-mono text-slate-300">{v.phone_number}</div>
                        <div className="text-[10px] text-cyan-400">{v.language}</div>
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          v.call_status === 'CONNECTED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                          v.call_status === 'SIMULATED_READY' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                          'bg-slate-800 text-slate-400'
                        }`}>
                          {v.call_status}
                        </span>
                      </td>
                      <td className="p-4 font-mono text-[10px] text-slate-300">{v.detected_intent}</td>
                      <td className="p-4 max-w-xs truncate">
                        <button
                          onClick={() => setSelectedScript(v)}
                          className="text-indigo-400 hover:text-indigo-300 text-left underline underline-offset-2 flex items-center space-x-1"
                        >
                          <Volume2 className="w-3 h-3 inline" />
                          <span className="truncate">{v.generated_script.slice(0, 45)}...</span>
                        </button>
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <button
                          onClick={() => handlePlanVoice(v.id)}
                          disabled={actionLoading === `plan_voc_${v.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold transition border border-slate-700 disabled:opacity-50"
                        >
                          <Sparkles className="w-3 h-3 inline mr-1 text-cyan-400" />
                          Generate Script
                        </button>
                        <button
                          onClick={() => handleExecuteVoice(v.id)}
                          disabled={actionLoading === `exec_voc_${v.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-[11px] font-semibold transition shadow-md shadow-cyan-600/20 disabled:opacity-50"
                        >
                          <PhoneCall className="w-3 h-3 inline mr-1" />
                          Simulate Call
                        </button>
                      </td>
                    </tr>
                  ))}
                  {voiceSessions.length === 0 && (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">No voice recovery records found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Script Modal */}
          {selectedScript && (
            <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
              <div className="bg-slate-900 border border-slate-800 max-w-lg w-full rounded-2xl p-6 space-y-4 shadow-2xl">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h4 className="text-sm font-bold text-white flex items-center space-x-2">
                    <Mic className="w-4 h-4 text-cyan-400" />
                    <span>Hinglish Voice Agent Script — {selectedScript.customer_name}</span>
                  </h4>
                  <button onClick={() => setSelectedScript(null)} className="text-slate-400 hover:text-white text-xs">
                    ✕ Close
                  </button>
                </div>
                <div className="p-4 bg-slate-950 rounded-xl text-xs font-mono text-slate-300 leading-relaxed border border-slate-800 whitespace-pre-wrap">
                  {selectedScript.generated_script}
                </div>
                <div className="flex items-center justify-between text-[11px] text-slate-400">
                  <span>Language: <strong className="text-cyan-400">{selectedScript.language}</strong></span>
                  <span>Duration: <strong className="text-white">{selectedScript.duration_seconds}s</strong></span>
                  <span>Execution: <strong className="text-amber-400">{selectedScript.execution_mode}</strong></span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Tab 6: Promise-to-Pay (PTP) */}
      {activeTab === 'promises' && (
        <div className="space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Program 7 — Promise-to-Pay (PTP) Tracker</h3>
              <p className="text-xs text-slate-400 mt-0.5">Automated commitment tracking with SLA countdown timers, gentle multi-channel reminders, and deterministic breach escalation.</p>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-violet-500/10 text-violet-400 border border-violet-500/20">
              SLA Monitored
            </span>
          </div>

          <div className="bg-slate-900/60 border border-slate-800 rounded-2xl overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950/80 text-[11px] uppercase tracking-wider text-slate-400 border-b border-slate-800 font-semibold">
                  <tr>
                    <th className="p-4">PTP ID</th>
                    <th className="p-4">Debtor</th>
                    <th className="p-4">Promised Amount</th>
                    <th className="p-4">Reference Link</th>
                    <th className="p-4">Grace Window</th>
                    <th className="p-4">Status</th>
                    <th className="p-4 text-right">Autonomous Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {promises.map((p) => (
                    <tr key={p.id} className="hover:bg-slate-800/40 transition">
                      <td className="p-4 font-mono text-violet-400 font-medium">{p.id}</td>
                      <td className="p-4 font-medium text-white">{p.customer_name}</td>
                      <td className="p-4 font-bold text-white">{formatINR(p.promised_amount)}</td>
                      <td className="p-4 font-mono text-[10px] text-slate-400">{p.reference_id}</td>
                      <td className="p-4 font-mono text-xs text-slate-300">{p.grace_period_hours} hours</td>
                      <td className="p-4">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          p.status === 'FULFILLED' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                          p.status === 'BREACHED' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                          'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                        }`}>
                          {p.status}
                        </span>
                      </td>
                      <td className="p-4 text-right space-x-2">
                        <button
                          onClick={() => handlePlanPromise(p.id)}
                          disabled={actionLoading === `plan_ptp_${p.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold transition border border-slate-700 disabled:opacity-50"
                        >
                          <Sparkles className="w-3 h-3 inline mr-1 text-violet-400" />
                          Plan SLA
                        </button>
                        <button
                          onClick={() => handleFulfillPromise(p.id)}
                          disabled={actionLoading === `ful_ptp_${p.id}` || p.status === 'FULFILLED'}
                          className="px-2.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-[11px] font-semibold transition shadow-md shadow-emerald-600/20 disabled:opacity-50"
                        >
                          <CheckCircle2 className="w-3 h-3 inline mr-1" />
                          Fulfill
                        </button>
                        <button
                          onClick={() => handleBreachPromise(p.id)}
                          disabled={actionLoading === `brk_ptp_${p.id}` || p.status === 'BREACHED'}
                          className="px-2.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-[11px] font-semibold transition shadow-md shadow-rose-600/20 disabled:opacity-50"
                        >
                          <AlertTriangle className="w-3 h-3 inline mr-1" />
                          Breach SLA
                        </button>
                      </td>
                    </tr>
                  ))}
                  {promises.length === 0 && (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-slate-500">No Promise-to-Pay commitments found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
