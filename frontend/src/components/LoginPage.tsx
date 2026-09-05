import React, { useState } from 'react'
import { ShieldCheck, Lock, Mail, ArrowRight, UserCheck, AlertCircle, KeyRound, Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'

export const LoginPage: React.FC = () => {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      setError('Please provide email and password')
      return
    }
    setIsLoading(true)
    setError(null)
    try {
      await login(email, password)
    } catch (err: any) {
      setError(err.message || 'Invalid email or password')
    } finally {
      setIsLoading(false)
    }
  }

  const handleQuickFill = async (quickEmail: string) => {
    setEmail(quickEmail)
    setPassword('RecoverAI2026!')
    setIsLoading(true)
    setError(null)
    try {
      await login(quickEmail, 'RecoverAI2026!')
    } catch (err: any) {
      setError(err.message || 'Failed to authenticate')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 flex flex-col justify-center items-center p-4 relative overflow-hidden">
      {/* Background glow accents */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[300px] bg-blue-600/10 blur-[120px] pointer-events-none rounded-full" />
      <div className="absolute bottom-1/4 left-1/3 w-[400px] h-[250px] bg-emerald-600/5 blur-[100px] pointer-events-none rounded-full" />

      <div className="w-full max-w-md space-y-6 relative z-10">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center space-x-2.5 bg-slate-900/90 border border-blue-500/30 px-3.5 py-1.5 rounded-2xl shadow-lg shadow-blue-500/10">
            <div className="h-6 w-6 rounded-lg bg-blue-600 flex items-center justify-center font-bold text-xs text-white">
              R
            </div>
            <span className="font-bold text-sm text-white tracking-tight">RecoverAI</span>
            <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.2 rounded-md">
              v1.0
            </span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">Merchant Operations Console</h1>
          <p className="text-xs text-slate-400 max-w-sm mx-auto">
            Autonomous AI Revenue Recovery with Deterministic Policy Guardrails
          </p>
        </div>

        {/* Login Card */}
        <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-6 shadow-2xl space-y-5">
          <div className="border-b border-[#1E293B] pb-3 flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
              <Lock className="h-3.5 w-3.5 text-blue-400" />
              <span>Merchant Sign In</span>
            </span>
            <span className="text-[11px] font-mono text-slate-500">Acrobatics Apparel</span>
          </div>

          {error && (
            <div className="bg-rose-500/10 border border-rose-500/30 p-3 rounded-xl flex items-center space-x-2 text-xs text-rose-300">
              <AlertCircle className="h-4 w-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 block">Merchant Email</label>
              <div className="relative">
                <Mail className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@acrobatics.com"
                  className="w-full bg-[#0B0F17] border border-[#1E293B] focus:border-blue-500 text-xs text-slate-100 rounded-xl pl-9 pr-3 py-2.5 outline-none transition"
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 block">Password</label>
              <div className="relative">
                <KeyRound className="h-4 w-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-[#0B0F17] border border-[#1E293B] focus:border-blue-500 text-xs text-slate-100 rounded-xl pl-9 pr-3 py-2.5 outline-none transition"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold py-2.5 rounded-xl transition flex items-center justify-center space-x-2 shadow-md shadow-blue-500/20 disabled:opacity-50"
            >
              <span>{isLoading ? 'Authenticating...' : 'Sign In to Console'}</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </form>

          {/* Quick Demo Sign In Options for Judges / Evaluators */}
          <div className="pt-4 border-t border-[#1E293B] space-y-2.5">
            <div className="flex items-center space-x-1.5 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
              <Sparkles className="h-3 w-3 text-amber-400" />
              <span>1-Click Seeded Demo Sign-In</span>
            </div>

            <div className="grid grid-cols-1 gap-2">
              <button
                type="button"
                onClick={() => handleQuickFill('admin@acrobatics.com')}
                disabled={isLoading}
                className="w-full bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-blue-500/40 p-3 rounded-xl text-left flex items-start justify-between transition group space-x-3"
              >
                <div className="space-y-0.5 flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-slate-200 group-hover:text-blue-400 transition">
                      Lead Merchant Admin
                    </span>
                    <span className="text-[9px] font-mono text-blue-400 bg-blue-500/10 border border-blue-500/20 px-1.5 py-0.2 rounded font-bold">
                      MERCHANT_ADMIN
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400">
                    Full Control: Manage policies, approve actions and oversee merchant operations
                  </p>
                  <div className="text-[10px] text-slate-500 font-mono">admin@acrobatics.com</div>
                </div>
                <span className="text-[10px] font-bold bg-blue-500/15 text-blue-400 border border-blue-500/30 px-2 py-0.5 rounded-md uppercase shrink-0">
                  ADMIN
                </span>
              </button>

              <button
                type="button"
                onClick={() => handleQuickFill('ops@acrobatics.com')}
                disabled={isLoading}
                className="w-full bg-slate-900 hover:bg-slate-800 border border-slate-700 hover:border-amber-500/40 p-3 rounded-xl text-left flex items-start justify-between transition group space-x-3"
              >
                <div className="space-y-0.5 flex-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-slate-200 group-hover:text-amber-300 transition">
                      Operations Agent
                    </span>
                    <span className="text-[9px] font-mono text-amber-300 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.2 rounded font-bold">
                      OPERATIONS_AGENT
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400">
                    Operations Access: Monitor and review recovery operations; policies are read-only
                  </p>
                  <div className="text-[10px] text-slate-500 font-mono">ops@acrobatics.com</div>
                </div>
                <span className="text-[10px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded-md uppercase shrink-0">
                  AGENT
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Security Statement Footer */}
        <div className="text-center text-[11px] text-slate-500 flex items-center justify-center space-x-1.5">
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
          <span>PBKDF2 Password Hashing & HMAC-SHA256 JWT Authorization</span>
        </div>
      </div>
    </div>
  )
}
