import React, { useState, useEffect, useRef } from 'react'
import {
  Bell,
  CheckCircle2,
  AlertTriangle,
  ShieldAlert,
  Info,
  Check,
  Trash2,
  Zap,
  Radio
} from 'lucide-react'
import { NotificationEvent } from '../types'
import { api, API_BASE } from '../services/api'
import { formatRelativeTime } from '../lib/utils'

interface NotificationCenterProps {
  onSelectWorkflowId?: (workflowId: string) => void
}

export const NotificationCenter: React.FC<NotificationCenterProps> = ({ onSelectWorkflowId }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [notifications, setNotifications] = useState<NotificationEvent[]>([])
  const [isConnected, setIsConnected] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  // Fetch initial history
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const history = await api.getNotificationHistory()
        setNotifications(history)
      } catch {
        // Silently fail if history not yet seeded
      }
    }
    fetchHistory()
  }, [])

  // Connect to SSE Stream
  useEffect(() => {
    let eventSource: EventSource | null = null
    try {
      eventSource = new EventSource(`${API_BASE}/events/stream`)

      eventSource.onopen = () => {
        setIsConnected(true)
      }

      eventSource.onmessage = (e) => {
        try {
          const notif: NotificationEvent = JSON.parse(e.data)
          if (notif && notif.title) {
            setNotifications((prev) => [notif, ...prev.filter((n) => n.id !== notif.id)])
          }
        } catch {
          // Non-JSON ping
        }
      }

      eventSource.onerror = () => {
        setIsConnected(false)
      }
    } catch {
      setIsConnected(false)
    }

    return () => {
      if (eventSource) eventSource.close()
    }
  }, [])

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const unreadCount = notifications.filter((n) => !n.read).length

  const handleMarkAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }

  const handleClearAll = () => {
    setNotifications([])
  }

  const handleItemClick = (notif: NotificationEvent) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === notif.id ? { ...n, read: true } : n))
    )
    if (notif.workflow_id && onSelectWorkflowId) {
      onSelectWorkflowId(notif.workflow_id)
      setIsOpen(false)
    }
  }

  const getSeverityIcon = (sev: string) => {
    switch (sev) {
      case 'SUCCESS':
        return <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
      case 'WARNING':
        return <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />
      case 'ERROR':
        return <ShieldAlert className="h-4 w-4 text-rose-400 shrink-0" />
      default:
        return <Info className="h-4 w-4 text-blue-400 shrink-0" />
    }
  }

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-xl bg-slate-900 border border-[#1E293B] hover:border-slate-600 text-slate-300 hover:text-white transition"
        aria-label="Notifications"
      >
        <Bell className="h-4 w-4" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-rose-500 text-white font-mono text-[9px] font-bold h-4.5 w-4.5 rounded-full flex items-center justify-center border-2 border-[#0B0F17] animate-pulse">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Panel */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 md:w-96 bg-[#111827] border border-[#1E293B] rounded-2xl shadow-2xl z-50 overflow-hidden animate-fade-in flex flex-col max-h-[480px]">
          {/* Header */}
          <div className="p-3.5 border-b border-[#1E293B] bg-slate-900/80 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-white">Live Event Feed</span>
              <span className="flex items-center space-x-1 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.2 rounded-full">
                <Radio className="h-2.5 w-2.5 animate-pulse text-emerald-400" />
                <span>{isConnected ? 'SSE Live' : 'Reconnecting'}</span>
              </span>
            </div>

            <div className="flex items-center space-x-2">
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllRead}
                  className="text-[11px] text-blue-400 hover:text-blue-300 font-semibold flex items-center space-x-0.5"
                  title="Mark all as read"
                >
                  <Check className="h-3 w-3" />
                  <span>Read all</span>
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  onClick={handleClearAll}
                  className="text-[11px] text-slate-500 hover:text-slate-400"
                  title="Clear all"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              )}
            </div>
          </div>

          {/* List */}
          <div className="overflow-y-auto divide-y divide-[#1E293B]/60 flex-1">
            {notifications.length === 0 ? (
              <div className="py-12 text-center space-y-1">
                <Zap className="h-5 w-5 text-slate-600 mx-auto" />
                <p className="text-xs text-slate-400 font-medium">No live notifications yet</p>
                <p className="text-[11px] text-slate-600">Recovery events will stream here in real time</p>
              </div>
            ) : (
              notifications.map((n) => (
                <div
                  key={n.id}
                  onClick={() => handleItemClick(n)}
                  className={`p-3.5 flex items-start space-x-3 transition cursor-pointer hover:bg-slate-800/40 ${
                    !n.read ? 'bg-blue-500/5' : ''
                  }`}
                >
                  {getSeverityIcon(n.severity)}
                  <div className="space-y-1 flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <h4 className="text-xs font-bold text-slate-100 truncate">{n.title}</h4>
                      <span className="text-[10px] text-slate-500 font-mono shrink-0">
                        {formatRelativeTime(n.timestamp)}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-300 leading-snug">{n.message}</p>
                    {n.transaction_id && (
                      <span className="inline-block font-mono text-[10px] text-blue-400 bg-blue-500/10 border border-blue-500/20 px-1.5 py-0.2 rounded">
                        {n.transaction_id}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}
