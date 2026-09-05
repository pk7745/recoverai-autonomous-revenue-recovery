import React from 'react'
import {
  Layers,
  ShieldCheck,
  RefreshCw,
  Building2,
  User,
  LogOut,
  Shield,
  KeyRound
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { NotificationCenter } from './NotificationCenter'

interface HeaderProps {
  onRefresh?: () => void
  isRefreshing?: boolean
  currentTabLabel?: string
  onSelectWorkflowId?: (workflowId: string) => void
}

export const Header: React.FC<HeaderProps> = ({
  onRefresh,
  isRefreshing,
  currentTabLabel = 'Command Center',
  onSelectWorkflowId
}) => {
  const { user, logout, isAdmin } = useAuth()

  return (
    <header className="h-16 border-b border-[#1E293B] bg-[#0B0F17]/95 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-30">
      {/* Brand & Breadcrumbs */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-3">
          <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center shadow-sm shadow-blue-500/20 text-white font-bold">
            <Layers className="h-4.5 w-4.5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold tracking-tight text-white text-sm">RecoverAI</span>
              <span className="bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider">
                Razorpay Track 03
              </span>
            </div>
          </div>
        </div>

        <span className="text-slate-600 font-mono hidden md:inline">/</span>

        {/* Merchant & Page Breadcrumb */}
        <div className="hidden md:flex items-center space-x-2 text-xs">
          <div className="flex items-center space-x-1.5 text-slate-400">
            <Building2 className="h-3.5 w-3.5 text-slate-500" />
            <span className="font-medium text-slate-300">Acrobatics Apparel</span>
          </div>
          <span className="text-slate-600">/</span>
          <span className="text-slate-100 font-semibold">{currentTabLabel}</span>
        </div>
      </div>

      {/* Control Status Pills */}
      <div className="flex items-center space-x-3">
        {/* System Health */}
        <div className="hidden lg:flex items-center space-x-2 bg-slate-900/90 border border-[#1E293B] px-3 py-1.5 rounded-lg text-xs">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-slate-400 font-medium">Gateway:</span>
          <strong className="text-emerald-400 font-semibold font-mono">Test Mode</strong>
          <span className="text-slate-600">|</span>
          <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
          <span className="text-slate-300 font-medium">Safety: <strong className="text-white">99.9%</strong></span>
        </div>

        {/* Refresh button */}
        {onRefresh && (
          <button
            onClick={onRefresh}
            disabled={isRefreshing}
            className="flex items-center space-x-1.5 bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-700/80 px-3 py-1.5 rounded-lg text-xs font-semibold transition disabled:opacity-50"
            title="Refresh Live Telemetry"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin text-blue-400' : 'text-slate-400'}`} />
            <span className="hidden sm:inline">Sync</span>
          </button>
        )}

        {/* Real-time Notification Center */}
        <NotificationCenter onSelectWorkflowId={onSelectWorkflowId} />

        {/* Authenticated User Pill & Logout */}
        {user && (
          <div className="flex items-center space-x-2 pl-1 border-l border-[#1E293B]">
            <div className="flex items-center space-x-2 bg-slate-900/90 border border-[#1E293B] px-2.5 py-1 rounded-xl">
              <div className={`h-5 w-5 rounded-lg flex items-center justify-center text-[10px] font-bold ${
                isAdmin ? 'bg-blue-600/30 text-blue-400 border border-blue-500/40' : 'bg-amber-600/30 text-amber-300 border border-amber-500/40'
              }`}>
                {isAdmin ? <Shield className="h-3 w-3" /> : <User className="h-3 w-3" />}
              </div>
              <div className="hidden sm:block text-left">
                <div className="text-[11px] font-bold text-slate-200 truncate max-w-[110px] leading-tight">
                  {user.name.split(' ')[0]}
                </div>
                <div className="text-[9px] font-mono uppercase tracking-wider font-bold text-slate-400">
                  {isAdmin ? (
                    <span className="text-blue-400">ADMIN</span>
                  ) : (
                    <span className="text-amber-300">OPS AGENT</span>
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={logout}
              className="p-1.5 rounded-lg bg-slate-900 hover:bg-rose-500/10 border border-[#1E293B] hover:border-rose-500/30 text-slate-400 hover:text-rose-400 transition"
              title="Sign Out"
            >
              <LogOut className="h-3.5 w-3.5" />
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
