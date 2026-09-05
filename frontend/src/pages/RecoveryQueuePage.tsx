import React, { useState } from 'react'
import {
  Search,
  Filter,
  ArrowUpDown,
  RefreshCw,
  GitPullRequest,
  CheckCircle2,
  AlertTriangle,
  Layers,
  ChevronRight,
  ShieldCheck,
  BrainCircuit
} from 'lucide-react'
import { RecoveryWorkflow } from '../types'
import { StatusBadge } from '../components/StatusBadge'
import { formatINR, formatRelativeTime } from '../lib/utils'

interface RecoveryQueuePageProps {
  workflows: RecoveryWorkflow[]
  onSelectWorkflow: (wf: RecoveryWorkflow) => void
  onRefresh: () => void
  isRefreshing: boolean
}

export const RecoveryQueuePage: React.FC<RecoveryQueuePageProps> = ({
  workflows,
  onSelectWorkflow,
  onRefresh,
  isRefreshing
}) => {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('ALL')

  const filterTabs = [
    { id: 'ALL', label: 'All Cases', count: workflows.length },
    { id: 'ESCALATED', label: 'Escalated', count: workflows.filter(w => w.state === 'ESCALATED').length },
    { id: 'POLICY_APPROVED', label: 'Approved', count: workflows.filter(w => w.state === 'POLICY_APPROVED').length },
    { id: 'RECOVERED', label: 'Recovered', count: workflows.filter(w => w.state === 'RECOVERED').length },
    { id: 'STOPPED', label: 'Stopped', count: workflows.filter(w => w.state === 'STOPPED').length }
  ]

  const filteredWorkflows = workflows.filter((wf) => {
    const matchesSearch =
      wf.transaction_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      wf.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (wf.transaction?.customer?.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      wf.failure_category.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesStatus =
      statusFilter === 'ALL' ||
      (statusFilter === 'ESCALATED' && wf.state === 'ESCALATED') ||
      (statusFilter === 'POLICY_APPROVED' && (wf.state === 'POLICY_APPROVED' || wf.state === 'ACTION_EXECUTING' || wf.state === 'AWAITING_PAYMENT_EVENT')) ||
      (statusFilter === 'RECOVERED' && wf.state === 'RECOVERED') ||
      (statusFilter === 'STOPPED' && wf.state === 'STOPPED')

    return matchesSearch && matchesStatus
  })

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 border border-[#1E293B] p-5 rounded-2xl">
        <div>
          <h2 className="text-lg font-bold text-white tracking-tight">Recovery Operations Queue</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Active revenue recovery workflows managed by Bounded AI & Policy Automation.
          </p>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3.5 py-2 rounded-xl text-xs font-semibold transition disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Filter Tabs & Search Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
        {/* Status Filter Tabs */}
        <div className="flex items-center space-x-1.5 overflow-x-auto pb-1">
          {filterTabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setStatusFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 shrink-0 ${
                statusFilter === tab.id
                  ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                  : 'bg-slate-900 text-slate-400 hover:text-slate-200 border border-[#1E293B]'
              }`}
            >
              <span>{tab.label}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold ${
                statusFilter === tab.id ? 'bg-blue-500/30 text-blue-200' : 'bg-slate-800 text-slate-500'
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Search Field */}
        <div className="relative min-w-[260px]">
          <Search className="h-3.5 w-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search txn ID, customer, category..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-900 border border-[#1E293B] rounded-xl pl-9 pr-3.5 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition"
          />
        </div>
      </div>

      {/* Operational Table */}
      <div className="bg-[#111827] border border-[#1E293B] rounded-2xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="bg-slate-900/80 border-b border-[#1E293B] text-slate-400 font-bold uppercase text-[10px] tracking-wider">
                <th className="py-3 px-4">Transaction & Customer</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Diagnosis Root Cause</th>
                <th className="py-3 px-4">AI Recommendation</th>
                <th className="py-3 px-4">Policy Gate</th>
                <th className="py-3 px-4">Workflow State</th>
                <th className="py-3 px-4 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#1E293B]/70">
              {filteredWorkflows.length > 0 ? (
                filteredWorkflows.map((wf) => {
                  const txn = wf.transaction
                  const cust = txn?.customer

                  return (
                    <tr
                      key={wf.id}
                      onClick={() => onSelectWorkflow(wf)}
                      className="hover:bg-slate-800/40 cursor-pointer transition"
                    >
                      <td className="py-3.5 px-4">
                        <div className="font-mono font-bold text-slate-200 text-xs">{wf.transaction_id}</div>
                        <div className="text-[11px] text-slate-400 flex items-center space-x-1.5 mt-0.5">
                          <span>{cust?.name || 'Customer'}</span>
                          <span>•</span>
                          <span className="font-mono">{txn?.payment_method?.toUpperCase()}</span>
                        </div>
                      </td>

                      <td className="py-3.5 px-4 font-mono font-bold text-white text-xs">
                        {formatINR(txn?.amount || 0)}
                      </td>

                      <td className="py-3.5 px-4">
                        <span className="text-slate-300 font-medium">{wf.failure_category}</span>
                        <p className="text-[10px] text-slate-500 truncate max-w-[180px]">{txn?.failure_reason}</p>
                      </td>

                      <td className="py-3.5 px-4">
                        <div className="flex items-center space-x-1.5 text-blue-400 font-semibold text-xs">
                          <BrainCircuit className="h-3.5 w-3.5" />
                          <span>{wf.recommended_action.replace(/_/g, ' ')}</span>
                        </div>
                        {wf.ai_confidence > 0 && (
                          <span className="text-[10px] font-mono text-slate-500">{(wf.ai_confidence * 100).toFixed(0)}% confidence</span>
                        )}
                      </td>

                      <td className="py-3.5 px-4">
                        <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-md border ${
                          wf.policy_evaluation?.status === 'ALLOWED'
                            ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                            : wf.policy_evaluation?.status === 'OVERRIDDEN_TO_ESCALATE'
                            ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                            : 'bg-slate-800 text-slate-400 border-slate-700'
                        }`}>
                          {wf.policy_evaluation?.status || 'PENDING'}
                        </span>
                      </td>

                      <td className="py-3.5 px-4">
                        <StatusBadge status={wf.state} />
                      </td>

                      <td className="py-3.5 px-4 text-right">
                        <button className="text-slate-400 hover:text-blue-400 font-semibold flex items-center space-x-0.5 ml-auto text-xs">
                          <span>Studio</span>
                          <ChevronRight className="h-3.5 w-3.5" />
                        </button>
                      </td>
                    </tr>
                  )
                })
              ) : (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500 text-xs font-mono">
                    No recovery workflows match the selected criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
