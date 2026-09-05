import React, { useState, useEffect } from 'react'
import {
  Sliders,
  ShieldCheck,
  AlertTriangle,
  Save,
  CheckCircle2,
  Lock,
  RotateCcw,
  Info,
  ShieldAlert
} from 'lucide-react'
import { MerchantPolicy } from '../types'
import { apiService } from '../services/api'
import { formatINR } from '../lib/utils'
import { useAuth } from '../context/AuthContext'

interface PoliciesPageProps {
  policies: MerchantPolicy | null
  onPoliciesUpdated: (updated: MerchantPolicy) => void
}

export const PoliciesPage: React.FC<PoliciesPageProps> = ({
  policies,
  onPoliciesUpdated
}) => {
  const { isAdmin, user } = useAuth()

  const [form, setForm] = useState<MerchantPolicy>({
    merchant_id: 'merch_razorpay_demo',
    merchant_name: 'Acrobatics Apparel Pvt Ltd',
    autonomous_limit: 5000.0,
    max_retries: 2,
    min_retry_interval_mins: 30,
    risk_threshold: 0.70
  })

  const [isSaving, setIsSaving] = useState(false)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  useEffect(() => {
    if (policies) {
      setForm(policies)
    }
  }, [policies])

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isAdmin) {
      setErrorMsg('Permission Denied: Only users with the MERCHANT_ADMIN role can modify merchant policy guardrails.')
      return
    }
    setIsSaving(true)
    setSuccessMsg(null)
    setErrorMsg(null)

    try {
      const res = await apiService.updatePolicies(form)
      onPoliciesUpdated(res)
      setSuccessMsg('Merchant guardrail policies successfully updated in authoritative backend engine.')
      setTimeout(() => setSuccessMsg(null), 4000)
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update policies.')
    } finally {
      setIsSaving(false)
    }
  }

  const handleResetDefaults = () => {
    if (!isAdmin) return
    setForm({
      merchant_id: 'merch_razorpay_demo',
      merchant_name: 'Acrobatics Apparel Pvt Ltd',
      autonomous_limit: 5000.0,
      max_retries: 2,
      min_retry_interval_mins: 30,
      risk_threshold: 0.70
    })
  }

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header Bar */}
      <div className="bg-slate-900/80 border border-[#1E293B] p-5 rounded-2xl flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <span className="bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
              Authoritative Guardrail Settings
            </span>
            <h2 className="text-lg font-bold text-white tracking-tight">Merchant Policy Control Plane</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Configure hard deterministic boundaries for autonomous AI interventions and human escalation gates.
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={handleResetDefaults}
            className="text-xs text-slate-400 hover:text-slate-200 border border-[#1E293B] px-3 py-1.5 rounded-xl font-semibold transition"
          >
            Reset to Defaults
          </button>
        )}
      </div>

      {/* RBAC Notice if logged in as Operations Agent */}
      {!isAdmin && (
        <div className="bg-amber-500/10 border border-amber-500/30 p-4 rounded-xl text-xs text-amber-300 flex items-start space-x-3 animate-fade-in">
          <Lock className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
          <div className="space-y-0.5">
            <span className="font-bold block">Read-Only View (Role: OPERATIONS_AGENT)</span>
            <p className="text-[11px] text-amber-200/80">
              You are logged in as <strong>{user?.name}</strong>. Operations Agents have read-only inspection access to guardrails. To modify authoritative parameters, log in with a <strong>MERCHANT_ADMIN</strong> account (<span className="font-mono text-white">admin@acrobatics.com</span>).
            </p>
          </div>
        </div>
      )}

      {successMsg && (
        <div className="bg-emerald-500/10 border border-emerald-500/30 p-4 rounded-xl text-xs text-emerald-300 flex items-center space-x-2 animate-fade-in">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {errorMsg && (
        <div className="bg-rose-500/10 border border-rose-500/30 p-4 rounded-xl text-xs text-rose-300 flex items-center space-x-2 animate-fade-in">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="space-y-5">
        {/* Policy 1: Autonomous Amount Limit */}
        <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-5 space-y-3 fintech-card-hover">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Autonomous Amount Ceiling (INR)</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Maximum invoice value eligible for automated retries without human manager signoff.
              </p>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-500 uppercase block font-bold">Current Ceiling</span>
              <span className="text-base font-mono font-bold text-emerald-400">{formatINR(form.autonomous_limit)}</span>
            </div>
          </div>

          <div className="space-y-2">
            <input
              type="range"
              min={1000}
              max={50000}
              step={500}
              disabled={!isAdmin}
              value={form.autonomous_limit}
              onChange={(e) => setForm({ ...form, autonomous_limit: Number(e.target.value) })}
              className={`w-full h-1.5 rounded-lg appearance-none ${
                isAdmin ? 'bg-slate-800 cursor-pointer accent-emerald-500' : 'bg-slate-900 cursor-not-allowed opacity-50'
              }`}
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>₹1,000 (Conservative)</span>
              <span>₹5,000 (Default)</span>
              <span>₹50,000 (Aggressive)</span>
            </div>
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-[#1E293B] text-[11px] text-slate-400 space-y-1">
            <strong className="text-slate-300">Why it matters:</strong> High-ticket orders (e.g. ₹27,000) carry greater fraud exposure and are automatically intercepted and routed to human managers for dual signoff.
          </div>
        </div>

        {/* Policy 2: Max Autonomous Retries */}
        <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-5 space-y-3 fintech-card-hover">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-white">Maximum Autonomous Retries</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Maximum number of automated attempts before a Stopping Rule halts the workflow permanently.
              </p>
            </div>
            <div className="text-right">
              <span className="text-[10px] text-slate-500 uppercase block font-bold">Current Max</span>
              <span className="text-base font-mono font-bold text-blue-400">{form.max_retries} Retries</span>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {[1, 2, 3, 4].map((cnt) => (
              <button
                key={cnt}
                type="button"
                disabled={!isAdmin}
                onClick={() => setForm({ ...form, max_retries: cnt })}
                className={`flex-1 py-2 rounded-xl text-xs font-mono font-bold border transition ${
                  form.max_retries === cnt
                    ? 'bg-blue-600/20 text-blue-400 border-blue-500/40'
                    : 'bg-slate-900 text-slate-400 border-[#1E293B] hover:bg-slate-800'
                } ${!isAdmin ? 'opacity-60 cursor-not-allowed' : ''}`}
              >
                {cnt} {cnt === 1 ? 'Attempt' : 'Attempts'}
              </button>
            ))}
          </div>

          <div className="bg-slate-950/60 p-3 rounded-xl border border-[#1E293B] text-[11px] text-slate-400 space-y-1">
            <strong className="text-slate-300">Why it matters:</strong> Prevents retry storms and card network spam penalties. Exceeding this limit forces a state transition to `STOPPED`.
          </div>
        </div>

        {/* Policy 3: Risk Threshold & Delayed Retry Interval */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-5 space-y-3 fintech-card-hover">
            <div className="flex justify-between items-baseline">
              <h3 className="text-sm font-bold text-white">Risk Score Threshold</h3>
              <span className="text-sm font-mono font-bold text-amber-400">{form.risk_threshold}</span>
            </div>
            <p className="text-[11px] text-slate-400">Transactions with calculated risk score at or above this value are escalated.</p>
            <input
              type="range"
              min={0.3}
              max={0.9}
              step={0.05}
              disabled={!isAdmin}
              value={form.risk_threshold}
              onChange={(e) => setForm({ ...form, risk_threshold: Number(e.target.value) })}
              className={`w-full h-1.5 rounded-lg appearance-none ${
                isAdmin ? 'bg-slate-800 cursor-pointer accent-amber-500' : 'bg-slate-900 cursor-not-allowed opacity-50'
              }`}
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>0.30 (Strict)</span>
              <span>0.70 (Standard)</span>
              <span>0.90 (Permissive)</span>
            </div>
          </div>

          <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-5 space-y-3 fintech-card-hover">
            <div className="flex justify-between items-baseline">
              <h3 className="text-sm font-bold text-white">Retry Cooldown Window</h3>
              <span className="text-sm font-mono font-bold text-purple-400">{form.min_retry_interval_mins} mins</span>
            </div>
            <p className="text-[11px] text-slate-400">Delay before executing a smart retry to allow bank node recovery.</p>
            <input
              type="range"
              min={10}
              max={120}
              step={10}
              disabled={!isAdmin}
              value={form.min_retry_interval_mins}
              onChange={(e) => setForm({ ...form, min_retry_interval_mins: Number(e.target.value) })}
              className={`w-full h-1.5 rounded-lg appearance-none ${
                isAdmin ? 'bg-slate-800 cursor-pointer accent-purple-500' : 'bg-slate-900 cursor-not-allowed opacity-50'
              }`}
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono">
              <span>10 mins</span>
              <span>30 mins</span>
              <span>120 mins</span>
            </div>
          </div>
        </div>

        {/* Action Save Button */}
        <div className="flex items-center justify-between pt-2">
          <p className="text-[11px] text-slate-500 italic">
            {isAdmin
              ? 'Changes take immediate effect in backend PolicyEngine for all incoming workflows.'
              : 'Sign in as Lead Merchant Admin to unlock policy modifications.'}
          </p>

          <button
            type="submit"
            disabled={isSaving || !isAdmin}
            className="bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold px-6 py-2.5 rounded-xl transition flex items-center space-x-2 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm shadow-blue-500/20"
          >
            <Save className="h-4 w-4" />
            <span>{isSaving ? 'Updating Backend...' : 'Save Guardrail Policy'}</span>
          </button>
        </div>
      </form>
    </div>
  )
}
