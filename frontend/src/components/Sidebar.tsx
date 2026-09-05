import React from 'react'
import {
  LayoutDashboard,
  GitPullRequest,
  ShieldAlert,
  FlaskConical,
  ScrollText,
  Sliders,
  PlayCircle,
  ShieldCheck
} from 'lucide-react'

export type TabId = 'overview' | 'queue' | 'safety' | 'experiments' | 'audit' | 'policies' | 'demo'

interface NavItem {
  id: TabId
  label: string
  icon: any
  badge?: number
  highlight?: boolean
}

interface NavSection {
  group: string
  items: NavItem[]
}

interface SidebarProps {
  currentTab: TabId
  onSelectTab: (tab: TabId) => void
  escalationCount?: number
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onSelectTab, escalationCount = 0 }) => {
  const sections: NavSection[] = [
    {
      group: 'OPERATIONS',
      items: [
        { id: 'overview', label: 'Command Center', icon: LayoutDashboard },
        { id: 'queue', label: 'Recovery Queue', icon: GitPullRequest, badge: escalationCount > 0 ? escalationCount : undefined }
      ]
    },
    {
      group: 'CONTROL & SAFETY',
      items: [
        { id: 'safety', label: 'Safety Center', icon: ShieldAlert },
        { id: 'policies', label: 'Merchant Policies', icon: Sliders }
      ]
    },
    {
      group: 'ANALYTICS',
      items: [
        { id: 'experiments', label: '10k Benchmark', icon: FlaskConical }
      ]
    },
    {
      group: 'AUDIT & COMPLIANCE',
      items: [
        { id: 'audit', label: 'Audit Trail', icon: ScrollText }
      ]
    },
    {
      group: 'DEMO & EVALUATION',
      items: [
        { id: 'demo', label: 'Demo Lab', icon: PlayCircle, highlight: true }
      ]
    }
  ]

  return (
    <aside className="w-64 border-r border-[#1E293B] bg-[#0B0F17] flex flex-col justify-between p-4 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        {sections.map((sec, sIdx) => (
          <div key={sIdx} className="space-y-1">
            <div className="text-[10px] font-bold tracking-wider text-slate-500 uppercase px-3 mb-1.5">
              {sec.group}
            </div>
            <nav className="space-y-0.5">
              {sec.items.map((item) => {
                const Icon = item.icon
                const isActive = currentTab === item.id

                return (
                  <button
                    key={item.id}
                    onClick={() => onSelectTab(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-semibold transition-all ${
                      isActive
                        ? 'bg-blue-600/15 text-blue-400 border border-blue-500/30'
                        : item.highlight
                        ? 'text-amber-300 hover:bg-amber-500/10 border border-amber-500/20'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5">
                      <Icon className={`h-4 w-4 shrink-0 ${isActive ? 'text-blue-400' : item.highlight ? 'text-amber-400' : 'text-slate-400'}`} />
                      <span>{item.label}</span>
                    </div>

                    {item.badge !== undefined && (
                      <span className="bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] px-1.5 py-0.2 rounded-full font-bold">
                        {item.badge}
                      </span>
                    )}
                  </button>
                )
              })}
            </nav>
          </div>
        ))}
      </div>

      {/* Bounded Autonomy Guard Badge */}
      <div className="bg-slate-900/70 border border-[#1E293B] rounded-xl p-3.5 space-y-2">
        <div className="flex items-center justify-between text-[11px] text-slate-400">
          <span className="font-semibold text-slate-300 flex items-center space-x-1">
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" />
            <span>Bounded Autonomy</span>
          </span>
          <span className="text-emerald-400 font-mono text-[10px]">ACTIVE</span>
        </div>
        <div className="w-full bg-slate-800 rounded-full h-1 overflow-hidden">
          <div className="bg-emerald-500 h-full w-[100%]"></div>
        </div>
        <p className="text-[10px] text-slate-500 leading-tight">
          AI Recommends • Policy Decides • Bounded Execution
        </p>
      </div>
    </aside>
  )
}
