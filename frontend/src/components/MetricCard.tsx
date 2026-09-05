import React from 'react'
import { LucideIcon } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string
  subtext?: string
  icon: LucideIcon
  variant?: 'default' | 'emerald' | 'rose' | 'amber' | 'blue'
  trend?: string
  trendPositive?: boolean
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtext,
  icon: Icon,
  variant = 'default',
  trend,
  trendPositive
}) => {
  const variantStyles = {
    default: 'border-[#1E293B] bg-[#111827] text-slate-100',
    emerald: 'border-emerald-500/30 bg-emerald-950/15 text-emerald-300 glow-emerald',
    rose: 'border-rose-500/30 bg-rose-950/15 text-rose-300 glow-rose',
    amber: 'border-amber-500/30 bg-amber-950/15 text-amber-300 glow-amber',
    blue: 'border-blue-500/30 bg-blue-950/15 text-blue-300 glow-blue'
  }

  const iconColors = {
    default: 'text-slate-400 bg-slate-800/80 border-slate-700/60',
    emerald: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
    rose: 'text-rose-400 bg-rose-500/10 border-rose-500/30',
    amber: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    blue: 'text-blue-400 bg-blue-500/10 border-blue-500/30'
  }

  return (
    <div className={`rounded-xl border p-4.5 transition-all fintech-card-hover ${variantStyles[variant]}`}>
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
          {title}
        </span>
        <div className={`p-1.5 rounded-lg border ${iconColors[variant]}`}>
          <Icon className="h-3.5 w-3.5" />
        </div>
      </div>

      <div className="mt-2.5 flex items-baseline justify-between">
        <div className="text-2xl font-bold tracking-tight text-white font-mono">
          {value}
        </div>
        {trend && (
          <span className={`text-[11px] font-bold px-2 py-0.5 rounded-full border ${
            trendPositive
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              : 'bg-rose-500/10 text-rose-400 border-rose-500/30'
          }`}>
            {trend}
          </span>
        )}
      </div>

      {subtext && (
        <p className="mt-1.5 text-[11px] text-slate-400 leading-snug">
          {subtext}
        </p>
      )}
    </div>
  )
}
