import React, { useState, useRef, useEffect } from 'react'
import {
  MessageSquare,
  X,
  Send,
  Sparkles,
  Bot,
  User,
  ShieldCheck,
  Zap,
  ArrowRight,
  Database,
  Layers,
  HelpCircle
} from 'lucide-react'
import { apiService } from '../services/api'
import { AssistantResponse } from '../types'

interface ChatMessage {
  id: string
  sender: 'user' | 'assistant'
  text?: string
  response?: AssistantResponse
  timestamp: string
}

export const OperationsAssistant: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'init_1',
      sender: 'assistant',
      text: 'Hello! I am your RecoverAI Operations Assistant. I am grounded in your live transaction records, recovery workflows, and merchant policy engine. How can I help you today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ])

  const chatEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOpen) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isOpen])

  const handleSend = async (userQuery?: string) => {
    const q = userQuery || query
    if (!q.trim()) return

    const userMsg: ChatMessage = {
      id: `usr_${Date.now()}`,
      sender: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }

    setMessages((prev) => [...prev, userMsg])
    if (!userQuery) setQuery('')
    setIsLoading(true)

    try {
      const res = await apiService.queryAssistant(q)
      const botMsg: ChatMessage = {
        id: `bot_${Date.now()}`,
        sender: 'assistant',
        response: res,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
      setMessages((prev) => [...prev, botMsg])
    } catch {
      const errorMsg: ChatMessage = {
        id: `bot_${Date.now()}`,
        sender: 'assistant',
        text: 'Sorry, I encountered an error querying the operations database. Please try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }

  const suggestedPrompts = [
    'Why was txn_demo_27000 blocked?',
    'How much revenue has been recovered?',
    'What are the current merchant limits?',
    'What happened during Scenario 4?'
  ]

  return (
    <>
      {/* Floating Action Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-40 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white p-3.5 rounded-full shadow-2xl shadow-blue-500/30 flex items-center space-x-2 transition-all hover:scale-105 group"
        aria-label="Open Operations Assistant"
      >
        <Bot className="h-5 w-5 animate-pulse" />
        <span className="text-xs font-bold pr-1 hidden sm:inline-block">Operations Assistant</span>
        <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
      </button>

      {/* Slide-out Drawer */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs animate-fade-in">
          <div className="w-full max-w-lg bg-[#0B0F17] border-l border-[#1E293B] h-full flex flex-col shadow-2xl">
            {/* Header */}
            <div className="p-4 border-b border-[#1E293B] bg-[#111827] flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 rounded-xl bg-blue-600/15 border border-blue-500/30 text-blue-400">
                  <Bot className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="text-sm font-bold text-white tracking-tight">Recovery Operations Assistant</h3>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-1.5 py-0.2 rounded-full font-bold">
                      Grounded
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-400">Connected to live SQLite DB & Policy Engine</p>
                </div>
              </div>

              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            {/* Chat Body */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex items-start space-x-2.5 ${
                    msg.sender === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                  }`}
                >
                  <div
                    className={`h-7 w-7 rounded-lg flex items-center justify-center shrink-0 ${
                      msg.sender === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-800 border border-slate-700 text-blue-400'
                    }`}
                  >
                    {msg.sender === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>

                  <div className={`max-w-[85%] space-y-2 text-xs`}>
                    {msg.text && (
                      <div
                        className={`p-3 rounded-2xl ${
                          msg.sender === 'user'
                            ? 'bg-blue-600 text-white rounded-tr-none'
                            : 'bg-[#111827] border border-[#1E293B] text-slate-200 rounded-tl-none leading-relaxed'
                        }`}
                      >
                        {msg.text}
                      </div>
                    )}

                    {/* Grounded 4-Layer Breakdown */}
                    {msg.response && (
                      <div className="bg-[#111827] border border-[#1E293B] rounded-2xl p-3.5 space-y-3 shadow-md rounded-tl-none">
                        <div className="font-bold text-white text-xs border-b border-[#1E293B] pb-2">
                          {msg.response.summary}
                        </div>

                        <div className="space-y-2">
                          <div className="bg-slate-950/70 border border-[#1E293B] p-2 rounded-lg space-y-0.5">
                            <span className="text-[10px] font-bold uppercase text-slate-500 block">
                              1. Observed Data
                            </span>
                            <p className="text-slate-300 text-[11px] leading-snug">{msg.response.observed_data}</p>
                          </div>

                          <div className="bg-slate-950/70 border border-[#1E293B] p-2 rounded-lg space-y-0.5">
                            <span className="text-[10px] font-bold uppercase text-blue-400 block">
                              2. AI Recommendation
                            </span>
                            <p className="text-slate-300 text-[11px] leading-snug">{msg.response.ai_recommendation}</p>
                          </div>

                          <div className="bg-slate-950/70 border border-[#1E293B] p-2 rounded-lg space-y-0.5">
                            <span className="text-[10px] font-bold uppercase text-emerald-400 block">
                              3. Policy Decision
                            </span>
                            <p className="text-slate-300 text-[11px] leading-snug whitespace-pre-line">{msg.response.policy_decision}</p>
                          </div>

                          <div className="bg-slate-950/70 border border-[#1E293B] p-2 rounded-lg space-y-0.5">
                            <span className="text-[10px] font-bold uppercase text-amber-400 block">
                              4. Final Outcome
                            </span>
                            <p className="text-slate-200 font-semibold text-[11px] leading-snug">{msg.response.final_outcome}</p>
                          </div>
                        </div>

                        {msg.response.references && msg.response.references.length > 0 && (
                          <div className="flex items-center space-x-1.5 pt-1 text-[10px] text-slate-500 font-mono">
                            <span>Ref:</span>
                            {msg.response.references.map((ref, rIdx) => (
                              <span key={rIdx} className="bg-slate-800 text-slate-300 px-1.5 py-0.2 rounded">
                                {ref}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    <span className="text-[9px] text-slate-500 font-mono block px-1">{msg.timestamp}</span>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex items-center space-x-2 text-xs text-slate-400 font-mono p-2 bg-[#111827] rounded-xl w-fit border border-[#1E293B]">
                  <Sparkles className="h-3.5 w-3.5 text-blue-400 animate-spin" />
                  <span>Synthesizing database records...</span>
                </div>
              )}

              <div ref={chatEndRef} />
            </div>

            {/* Suggested Prompt Chips */}
            <div className="p-3 border-t border-[#1E293B] bg-slate-900/60 space-y-2">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Suggested Questions</span>
              <div className="flex flex-wrap gap-1.5">
                {suggestedPrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSend(prompt)}
                    disabled={isLoading}
                    className="text-[11px] text-slate-300 bg-slate-800 hover:bg-slate-700 border border-slate-700 hover:border-slate-600 px-2.5 py-1 rounded-lg transition text-left"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>

            {/* Query Input Box */}
            <div className="p-3 border-t border-[#1E293B] bg-[#111827]">
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  handleSend()
                }}
                className="flex items-center space-x-2"
              >
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Ask about transactions, policies, or revenue..."
                  className="flex-1 bg-[#0B0F17] border border-[#1E293B] focus:border-blue-500 text-xs text-slate-100 rounded-xl px-3 py-2.5 outline-none transition"
                  disabled={isLoading}
                />
                <button
                  type="submit"
                  disabled={isLoading || !query.trim()}
                  className="p-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl transition disabled:opacity-50"
                >
                  <Send className="h-4 w-4" />
                </button>
              </form>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
