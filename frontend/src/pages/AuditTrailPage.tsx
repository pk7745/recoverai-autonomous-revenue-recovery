import React, { useState } from 'react'
import {
  ScrollText,
  Filter,
  RefreshCw,
  Clock,
  ShieldCheck,
  BrainCircuit,
  Lock,
  Building2,
  Terminal,
  ChevronRight,
  Fingerprint
} from 'lucide-react'
import { AuditLog } from '../types'
import { formatRelativeTime } from '../lib/utils'

interface AuditTrailPageProps {
  logs: AuditLog[]
  onRefresh: () => void
  isRefreshing: boolean
}

export const AuditTrailPage: React.FC<AuditTrailPageProps> = ({
  logs,
  onRefresh,
  isRefreshing
}) => {
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(logs.length > 0 ? logs[0] : null)
  const [actorFilter, setActorFilter] = useState<string>('ALL')

  const actorFilters = ['ALL', 'SYSTEM_AGENT', 'POLICY_ENGINE', 'RAZORPAY_WEBHOOK', 'MERCHANT_ADMIN']

  const filteredLogs = logs.filter(
    (l) => actorFilter === 'ALL' || l.actor === actorFilter
  )

  const getActorBadge = (actor: string) => {
    switch (actor) {
      case 'POLICY_ENGINE':
        return <span className="bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 text-[10px] px-2 py-0.5 rounded-full font-mono font-bold">POLICY ENGINE</span>
      case 'SYSTEM_AGENT':
        return <span className="bg-blue-500/10 text-blue-300 border border-blue-500/30 text-[10px] px-2 py-0.5 rounded-full font-mono font-bold">AI AGENT</span>
      case 'RAZORPAY_WEBHOOK':
        return <span className="bg-purple-500/10 text-purple-300 border border-purple-500/30 text-[10px] px-2 py-0.5 rounded-full font-mono font-bold">GATEWAY WEBHOOK</span>
      case 'MERCHANT_ADMIN':
        return <span className="bg-amber-500/10 text-amber-300 border border-amber-500/30 text-[10px] px-2 py-0.5 rounded-full font-mono font-bold">MERCHANT ADMIN</span>
      default:
        return <span className="bg-slate-800 text-slate-400 border border-slate-700 text-[10px] px-2 py-0.5 rounded-full font-mono font-bold">{actor}</span>
    }
  }

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-[#1E293B] p-5 rounded-2xl">
        <div>
          <div className="flex items-center space-x-2">
            <span className="bg-blue-500/10 text-blue-300 border border-blue-500/30 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
              Tamper-Evident Ledger
            </span>
            <h2 className="text-lg font-bold text-white tracking-tight">Audit Trail & Compliance Ledger</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Append-only audit ledger with HMAC and SHA-256 correlation of all AI diagnostic inferences, policy evaluations, and gateway mutations.
          </p>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3.5 py-2 rounded-xl text-xs font-semibold transition disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Ledger</span>
        </button>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center space-x-1.5 overflow-x-auto pb-1">
        {actorFilters.map((af) => (
          <button
            key={af}
            onClick={() => setActorFilter(af)}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition shrink-0 ${
              actorFilter === af
                ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30 font-bold'
                : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-[#1E293B]'
            }`}
          >
            {af.replace(/_/g, ' ')}
          </button>
        ))}
      </div>

      {/* 2-Column Master-Detail Ledger */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 min-h-[500px]">
        {/* Left Column: Event Stream (7 cols) */}
        <div className="lg:col-span-7 bg-[#111827] border border-[#1E293B] rounded-2xl overflow-hidden shadow-sm flex flex-col">
          <div className="p-4 border-b border-[#1E293B] bg-slate-900/80 flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">Recorded Operations ({filteredLogs.length})</span>
            <span className="text-[10px] text-slate-500 font-mono">Append-Only</span>
          </div>

          <div className="divide-y divide-[#1E293B]/70 overflow-y-auto max-h-[600px]">
            {filteredLogs.length > 0 ? (
              filteredLogs.map((log) => {
                const isSelected = selectedLog?.id === log.id

                return (
                  <div
                    key={log.id}
                    onClick={() => setSelectedLog(log)}
                    className={`p-4 cursor-pointer transition flex items-start justify-between ${
                      isSelected ? 'bg-blue-950/20 border-l-2 border-blue-500' : 'hover:bg-slate-800/30'
                    }`}
                  >
                    <div className="space-y-1.5 pr-2">
                      <div className="flex items-center space-x-2">
                        {getActorBadge(log.actor)}
                        <span className="text-xs font-bold text-white font-mono">{log.action}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono flex items-center space-x-2">
                        <span>ID: {log.id}</span>
                        {log.workflow_id && (
                          <>
                            <span>•</span>
                            <span className="text-blue-400">WF: {log.workflow_id}</span>
                          </>
                        )}
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-[10px] text-slate-500 font-mono block">{formatRelativeTime(log.created_at)}</span>
                      <ChevronRight className="h-4 w-4 text-slate-600 ml-auto mt-1" />
                    </div>
                  </div>
                )
              })
            ) : (
              <div className="p-12 text-center text-slate-500 text-xs font-mono">
                No audit events recorded for the selected actor filter.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Structured Detail Inspector (5 cols) */}
        <div className="lg:col-span-5 bg-[#111827] border border-[#1E293B] rounded-2xl p-5 space-y-4 shadow-sm flex flex-col justify-between">
          {selectedLog ? (
            <div className="space-y-4">
              <div className="border-b border-[#1E293B] pb-3 space-y-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Event Telemetry Inspector</span>
                <h3 className="text-sm font-bold text-white font-mono">{selectedLog.action}</h3>
                <div className="flex items-center space-x-2 mt-1">
                  {getActorBadge(selectedLog.actor)}
                  <span className="text-[10px] text-slate-400 font-mono">{selectedLog.created_at}</span>
                </div>
              </div>

              <div className="space-y-2 text-xs">
                <div className="bg-slate-900/80 border border-[#1E293B] p-2.5 rounded-lg flex justify-between">
                  <span className="text-slate-400">Ledger Entry ID:</span>
                  <span className="font-mono text-slate-200 font-bold">{selectedLog.id}</span>
                </div>

                {selectedLog.workflow_id && (
                  <div className="bg-slate-900/80 border border-[#1E293B] p-2.5 rounded-lg flex justify-between">
                    <span className="text-slate-400">Workflow Reference:</span>
                    <span className="font-mono text-blue-400 font-bold">{selectedLog.workflow_id}</span>
                  </div>
                )}

                {selectedLog.transaction_id && (
                  <div className="bg-slate-900/80 border border-[#1E293B] p-2.5 rounded-lg flex justify-between">
                    <span className="text-slate-400">Transaction ID:</span>
                    <span className="font-mono text-emerald-400 font-bold">{selectedLog.transaction_id}</span>
                  </div>
                )}
              </div>

              {/* JSON Payload Viewer */}
              <div className="space-y-1.5">
                <div className="flex items-center space-x-1.5 text-slate-400 text-xs font-bold">
                  <Terminal className="h-3.5 w-3.5" />
                  <span>Structured Event Context</span>
                </div>
                <pre className="bg-[#0B0F17] border border-[#1E293B] rounded-xl p-3.5 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-[300px]">
                  {JSON.stringify(selectedLog.details, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-slate-500 text-xs font-mono">
              Select an audit event from the ledger to inspect its cryptographic payload.
            </div>
          )}

          <div className="bg-slate-900/60 border border-[#1E293B] p-3 rounded-xl text-[10px] text-slate-500 leading-snug flex items-center space-x-2">
            <Fingerprint className="h-4 w-4 text-emerald-400 shrink-0" />
            <span>Cryptographically sealed record. Changes to historical audit events will invalidate ledger integrity.</span>
          </div>
        </div>
      </div>
    </div>
  )
}
