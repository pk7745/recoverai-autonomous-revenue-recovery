import {
  DashboardOverviewResponse,
  RecoveryWorkflow,
  SafetyOverviewResponse,
  MerchantPolicyResponse,
  BenchmarkComparisonResponse,
  AuditLogItem,
  UserProfile,
  LoginResponse,
  NotificationEvent,
  AssistantResponse
} from '../types'

const rawBase = (import.meta.env.VITE_API_BASE_URL || '').trim()
export const API_BASE = rawBase ? `${rawBase.replace(/\/$/, '')}/api/v1` : '/api/v1'

function getAuthHeaders(): HeadersInit {
  const token = sessionStorage.getItem('recoverai_token')
  const headers: HeadersInit = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  return headers
}

export const api = {
  // Authentication
  async login(email: string, password: string): Promise<LoginResponse> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Invalid login credentials')
    }
    const data: LoginResponse = await res.json()
    // Session-scoped storage: persists during active browser session, clears on new visit
    sessionStorage.setItem('recoverai_token', data.access_token)
    localStorage.removeItem('recoverai_token') // Clear legacy persistent token if any
    return data
  },

  async getMe(): Promise<UserProfile> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders()
    })
    if (!res.ok) throw new Error('Not authenticated')
    return res.json()
  },

  logout() {
    sessionStorage.removeItem('recoverai_token')
    localStorage.removeItem('recoverai_token')
  },

  // Dashboard
  async getDashboardOverview(): Promise<DashboardOverviewResponse> {
    const res = await fetch(`${API_BASE}/dashboard/overview`, {
      headers: getAuthHeaders()
    })
    if (!res.ok) throw new Error('Failed to fetch dashboard overview')
    return res.json()
  },

  // Recovery Workflows
  async getRecoveryWorkflows(state?: string): Promise<RecoveryWorkflow[]> {
    const url = state ? `${API_BASE}/recovery?state=${state}` : `${API_BASE}/recovery`
    const res = await fetch(url, { headers: getAuthHeaders() })
    if (!res.ok) throw new Error('Failed to fetch recovery workflows')
    return res.json()
  },

  async getRecoveryWorkflow(id: string): Promise<RecoveryWorkflow> {
    const res = await fetch(`${API_BASE}/recovery/${id}`, { headers: getAuthHeaders() })
    if (!res.ok) throw new Error('Failed to fetch recovery workflow')
    return res.json()
  },

  async planRecoveryWorkflow(id: string): Promise<RecoveryWorkflow> {
    const res = await fetch(`${API_BASE}/recovery/${id}/plan`, {
      method: 'POST',
      headers: getAuthHeaders()
    })
    if (!res.ok) throw new Error('Failed to plan recovery workflow')
    return res.json()
  },

  async executeRecoveryWorkflow(id: string): Promise<RecoveryWorkflow> {
    const res = await fetch(`${API_BASE}/recovery/${id}/execute`, {
      method: 'POST',
      headers: getAuthHeaders()
    })
    if (!res.ok) throw new Error('Failed to execute recovery workflow')
    return res.json()
  },

  async approveEscalation(id: string, notes?: string): Promise<RecoveryWorkflow> {
    const res = await fetch(`${API_BASE}/recovery/${id}/approve`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ notes })
    })
    if (!res.ok) throw new Error('Failed to approve escalation')
    return res.json()
  },

  async stopWorkflow(id: string): Promise<RecoveryWorkflow> {
    const res = await fetch(`${API_BASE}/recovery/${id}/stop`, {
      method: 'POST',
      headers: getAuthHeaders()
    })
    if (!res.ok) throw new Error('Failed to stop workflow')
    return res.json()
  },

  // Safety Center
  async getSafetyOverview(): Promise<SafetyOverviewResponse> {
    const res = await fetch(`${API_BASE}/safety/overview`, { headers: getAuthHeaders() })
    if (!res.ok) throw new Error('Failed to fetch safety overview')
    return res.json()
  },

  // Policies
  async getMerchantPolicy(): Promise<MerchantPolicyResponse> {
    const res = await fetch(`${API_BASE}/policies`, { headers: getAuthHeaders() })
    if (!res.ok) throw new Error('Failed to fetch merchant policy')
    return res.json()
  },

  async updateMerchantPolicy(policy: Partial<MerchantPolicyResponse>): Promise<MerchantPolicyResponse> {
    const res = await fetch(`${API_BASE}/policies`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(policy)
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail || 'Failed to update merchant policy')
    }
    return res.json()
  },

  async updatePolicies(policy: Partial<MerchantPolicyResponse>): Promise<MerchantPolicyResponse> {
    return this.updateMerchantPolicy(policy)
  },

  // Experiments
  async getBenchmark(): Promise<BenchmarkComparisonResponse> {
    const res = await fetch(`${API_BASE}/experiments/benchmark`, { headers: getAuthHeaders() })
    if (!res.ok) throw new Error('Failed to fetch benchmark')
    return res.json()
  },

  async runBenchmark(datasetSize: number = 10000): Promise<BenchmarkComparisonResponse> {
    const res = await fetch(`${API_BASE}/experiments/run?dataset_size=${datasetSize}`, {
      method: 'POST',
      headers: getAuthHeaders()
    })
    if (!res.ok) throw new Error('Failed to run benchmark experiment')
    return res.json()
  },

  // Audit Logs
  async getAuditLogs(limit: number = 100, actor?: string): Promise<AuditLogItem[]> {
    const url = actor ? `${API_BASE}/audit/logs?limit=${limit}&actor=${actor}` : `${API_BASE}/audit/logs?limit=${limit}`
    const res = await fetch(url, { headers: getAuthHeaders() })
    if (!res.ok) throw new Error('Failed to fetch audit logs')
    return res.json()
  },

  // Demo Scenarios
  async runDemoScenario(scenarioId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/scenario/${scenarioId}`, {
      method: 'POST',
      headers: getAuthHeaders()
    })
    if (!res.ok) throw new Error('Failed to execute demo scenario')
    return res.json()
  },

  async resetDemoData(): Promise<any> {
    const res = await fetch(`${API_BASE}/demo/reset`, {
      method: 'POST',
      headers: getAuthHeaders()
    })
    if (!res.ok) throw new Error('Failed to reset demo database')
    return res.json()
  },

  // Phase 6: Operations Assistant
  async queryAssistant(query: string, context_workflow_id?: string): Promise<AssistantResponse> {
    const res = await fetch(`${API_BASE}/assistant/query`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ query, context_workflow_id })
    })
    if (!res.ok) throw new Error('Failed to query Operations Assistant')
    return res.json()
  },

  // Phase 6: Notifications History
  async getNotificationHistory(): Promise<NotificationEvent[]> {
    const res = await fetch(`${API_BASE}/events/history`, { headers: getAuthHeaders() })
    if (!res.ok) throw new Error('Failed to fetch notification history')
    return res.json()
  }
}

export const apiService = api
