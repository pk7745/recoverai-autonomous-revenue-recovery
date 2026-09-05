import React from 'react'

interface StatusBadgeProps {
  status: string
  size?: 'sm' | 'md'
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'sm' }) => {
  const getStyle = (s: string) => {
    switch (s) {
      case 'RECOVERED':
      case 'ALLOWED':
      case 'CAPTURED':
        return 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
      case 'ESCALATED':
      case 'OVERRIDDEN_TO_ESCALATE':
      case 'HUMAN_ESCALATION':
      case 'HUMAN REVIEW':
        return 'bg-amber-500/10 text-amber-300 border-amber-500/30'
      case 'STOPPED':
      case 'BLOCKED':
      case 'STOP':
      case 'FAILED':
        return 'bg-rose-500/10 text-rose-300 border-rose-500/30'
      case 'POLICY_APPROVED':
      case 'ACTION_EXECUTING':
      case 'DELAYED_RETRY':
      case 'PAYMENT_LINK':
      case 'AUTHORIZED':
        return 'bg-blue-500/10 text-blue-300 border-blue-500/30'
      case 'RECOVERY_PLANNED':
      case 'RECOVERY_ELIGIBLE':
        return 'bg-purple-500/10 text-purple-300 border-purple-500/30'
      case 'NO_ACTION':
        return 'bg-slate-800 text-slate-300 border-slate-700'
      default:
        return 'bg-slate-800/80 text-slate-400 border-slate-700'
    }
  }

  const getDotColor = (s: string) => {
    switch (s) {
      case 'RECOVERED':
      case 'ALLOWED':
      case 'CAPTURED':
        return 'bg-emerald-400'
      case 'ESCALATED':
      case 'OVERRIDDEN_TO_ESCALATE':
      case 'HUMAN_ESCALATION':
      case 'HUMAN REVIEW':
        return 'bg-amber-400 animate-pulse'
      case 'STOPPED':
      case 'BLOCKED':
      case 'STOP':
      case 'FAILED':
        return 'bg-rose-400'
      case 'POLICY_APPROVED':
      case 'ACTION_EXECUTING':
      case 'AUTHORIZED':
        return 'bg-blue-400'
      default:
        return 'bg-slate-400'
    }
  }

  const padding = size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'

  return (
    <span className={`inline-flex items-center space-x-1.5 rounded-full border font-semibold tracking-wide uppercase font-mono ${padding} ${getStyle(status)}`}>
      <span className={`h-1.5 w-1.5 rounded-full shrink-0 ${getDotColor(status)}`}></span>
      <span>{status.replace(/_/g, ' ')}</span>
    </span>
  )
}
