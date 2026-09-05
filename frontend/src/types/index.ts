import { LucideIcon } from 'lucide-react'

export type PaymentStatus =
  | 'PAYMENT_PENDING'
  | 'CAPTURED'
  | 'FAILED'
  | 'RECOVERED'
  | 'REFUNDED'

export type RecoveryState =
  | 'PAYMENT_FAILED'
  | 'RECOVERY_ELIGIBLE'
  | 'RECOVERY_PLANNED'
  | 'POLICY_APPROVED'
  | 'ACTION_EXECUTING'
  | 'AWAITING_PAYMENT_EVENT'
  | 'RECOVERED'
  | 'ESCALATED'
  | 'STOPPED'

export type FailureCategory =
  | 'TEMPORARY_ISSUER_DECLINE'
  | 'AUTHENTICATION_FAILURE'
  | 'NETWORK_TIMEOUT'
  | 'INSUFFICIENT_FUNDS'
  | 'SUSPICIOUS_FRAUD'
  | 'CUSTOMER_DROPOFF'
  | 'UNKNOWN'

export type InterventionType =
  | 'DELAYED_RETRY'
  | 'SMART_PAYMENT_LINK'
  | 'ALTERNATIVE_PAYMENT'
  | 'CUSTOMER_NOTIFICATION'
  | 'ROUTE_TO_HUMAN_OPS'
  | 'NO_ACTION'
  | 'STOP'

export type ActorType =
  | 'AI_AGENT'
  | 'POLICY_ENGINE'
  | 'RISK_ENGINE'
  | 'MERCHANT_ADMIN'
  | 'RAZORPAY_WEBHOOK'
  | 'SYSTEM'

export type RiskTier = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface Customer {
  id: string
  merchant_id: string
  name?: string
  email: string
  phone?: string
  total_successful_payments: number
  total_failed_payments: number
  is_returning: boolean
  risk_tier: RiskTier
  created_at: string
}

export interface Transaction {
  id: string
  merchant_id: string
  customer_id: string
  razorpay_payment_id?: string
  razorpay_order_id?: string
  amount: number
  currency: string
  status: PaymentStatus
  failure_code?: string
  failure_reason?: string
  payment_method?: string
  attempts_count: number
  created_at: string
  customer?: Customer
}

export interface ExplainabilityFactor {
  factor_name?: string
  title?: string
  impact?: 'POSITIVE' | 'NEGATIVE' | 'NEUTRAL'
  weight?: number
  description: string
  icon?: string
}

export interface AIReasoning {
  confidence: number
  recommended_intervention: InterventionType
  expected_recovery_amount: number
  factors: ExplainabilityFactor[]
  summary: string
}

export interface PolicyCheckItem {
  rule_id?: string
  rule_description: string
  passed: boolean
  details?: string
}

export interface PolicyEvaluation {
  status: 'ALLOWED' | 'STOPPED' | 'OVERRIDDEN_TO_ESCALATE'
  requires_human_approval: boolean
  rejection_reason?: string
  checks?: PolicyCheckItem[]
  checked_rules?: Record<string, boolean>
}

export interface RecoveryWorkflow {
  id: string
  transaction_id: string
  state: RecoveryState
  risk_score: number
  failure_category: FailureCategory | string
  recommended_action: InterventionType | string
  ai_confidence: number
  ai_reasoning?: AIReasoning
  policy_evaluation?: PolicyEvaluation
  execution_payload?: Record<string, any>
  recovered_amount: number
  stopping_rule_triggered?: string
  escalation_reason?: string
  created_at: string
  updated_at: string
  transaction?: Transaction
}

export interface MetricSummary {
  total_revenue_processed: number
  revenue_at_risk: number
  recovered_revenue: number
  recovery_rate: number
  total_transactions: number
  failed_transactions: number
  active_recovery_workflows: number
  automatic_recovery_count: number
  human_escalations_count: number
  stopped_actions_count: number
  average_recovery_time_seconds: number
  ai_automation_rate: number
  safety_health_score?: number
  prevented_loss_amount?: number
}

export interface TimeSeriesPoint {
  date?: string
  date_label?: string
  timestamp?: string
  at_risk?: number
  failed_amount?: number
  recovered?: number
  recovered_amount?: number
  recovery_rate?: number
}

export interface ActivityFeedItem {
  id: string
  workflow_id: string
  transaction_id: string
  amount: number
  action_type: string
  state: string
  reason: string
  timestamp: string
  customer_name?: string
  payment_method?: string
}

export interface FailureCategoryItem {
  category: string
  count: number
}

export interface DashboardOverviewResponse {
  metrics: MetricSummary
  timeseries?: TimeSeriesPoint[]
  activity_feed?: ActivityFeedItem[]
  recovery_by_intervention?: Record<string, Record<string, any>>
  recovery_by_failure_category?: Record<string, Record<string, any>>
  recovery_trend_7d?: TimeSeriesPoint[]
  top_failure_categories?: FailureCategoryItem[]
}

export interface SafetyOverviewResponse {
  total_blocked_actions: number
  total_stopped_workflows: number
  total_human_escalations: number
  total_duplicate_events_prevented: number
  total_fraud_anomalies_contained: number
  high_value_transactions_routed: number
  policy_violations_prevented: number
  safety_health_score: number
}

export interface MerchantPolicyResponse {
  merchant_id: string
  merchant_name: string
  autonomous_limit: number
  max_retries: number
  min_retry_interval_mins: number
  risk_threshold: number
}

export interface StrategyMetrics {
  name: string
  total_transactions: number
  failed_transactions: number
  total_revenue_at_risk: number
  recovered_revenue: number
  recovery_rate: number
  unnecessary_retries: number
  human_escalations: number
  stopped_unsafe_actions: number
  average_attempts_per_recovery: number
  roi_multiple: number
}

export interface CategoryCohortItem {
  category: string
  total_transactions: number
  baseline_rate: number
  recoverai_rate: number
  uplift: number
}

export interface BenchmarkComparisonResponse {
  dataset_size: number
  run_timestamp: string
  baseline_strategy: StrategyMetrics
  recoverai_strategy: StrategyMetrics
  uplift_percentage: number
  additional_revenue_recovered?: number
  incremental_recovered_revenue?: number
  wasteful_retries_prevented: number
  breakdown_by_category?: Record<string, any>
  category_breakdown?: CategoryCohortItem[]
}

export interface AuditLogItem {
  id: string
  workflow_id?: string
  transaction_id?: string
  actor: string
  action: string
  details?: Record<string, any>
  created_at: string
}

// Phase 6 Types
export type UserRole = 'MERCHANT_ADMIN' | 'OPERATIONS_AGENT'

export interface UserProfile {
  id: string
  merchant_id: string
  email: string
  name: string
  role: UserRole
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: UserProfile
}

export interface NotificationEvent {
  id: string
  event_type: string
  title: string
  message: string
  severity: 'SUCCESS' | 'WARNING' | 'INFO' | 'ERROR'
  workflow_id?: string
  transaction_id?: string
  amount?: number
  timestamp: string
  read: boolean
}

export interface AssistantResponse {
  query: string
  summary: string
  observed_data: string
  ai_recommendation: string
  policy_decision: string
  final_outcome: string
  references: string[]
}

export type DashboardOverview = DashboardOverviewResponse
export type SafetyOverview = SafetyOverviewResponse
export type MerchantPolicy = MerchantPolicyResponse
export type AuditLog = AuditLogItem

// 7-Program Suite Types
export interface ProgramSummary {
  name: string
  total_records: number
  active_workflows: number
  recovered_amount: number
  status: string
}

export interface ProgramsOverviewResponse {
  programs: {
    payment: ProgramSummary
    checkout: ProgramSummary
    subscription: ProgramSummary
    receivables: ProgramSummary
    mandates: ProgramSummary
    voice: ProgramSummary
    promises: ProgramSummary
  }
  total_active_pipelines: number
  total_recovered_inr: number
}

export interface CheckoutSessionItem {
  id: string
  customer_id: string
  customer_name: string
  customer_email: string
  cart_value: number
  currency: string
  items_count: number
  exit_step: string
  detected_friction: string
  recovery_status: string
  recovery_link_url?: string
  created_at: string
  workflow?: Partial<RecoveryWorkflow>
}

export interface SubscriptionItem {
  id: string
  customer_id: string
  customer_name: string
  customer_email: string
  plan_name: string
  recurring_amount: number
  currency: string
  billing_interval: string
  status: string
  failed_attempts: number
  max_retries: number
  last_failure_reason?: string
  next_retry_at?: string
  created_at: string
  workflow?: Partial<RecoveryWorkflow>
}

export interface ReceivableInvoiceItem {
  id: string
  invoice_number: string
  customer_id: string
  customer_name: string
  customer_email: string
  invoice_amount: number
  currency: string
  issue_date: string
  due_date: string
  overdue_days: number
  chasing_stage: string
  status: string
  last_contact_at?: string
  contact_count: number
  created_at: string
  workflow?: Partial<RecoveryWorkflow>
}

export interface MandateItem {
  id: string
  customer_id: string
  customer_name: string
  mandate_token: string
  mandate_type: string
  max_amount: number
  scheduled_amount: number
  currency: string
  frequency: string
  status: string
  attempt_number: number
  max_attempts: number
  failure_code: string
  next_attempt_at?: string
  created_at: string
  workflow?: Partial<RecoveryWorkflow>
}

export interface VoiceRecoverySessionItem {
  id: string
  customer_id: string
  customer_name: string
  phone_number: string
  language: string
  generated_script: string
  audio_simulation_state?: Record<string, any>
  call_status: string
  detected_intent: string
  payment_link_sent: boolean
  duration_seconds: number
  execution_mode: string
  created_at: string
  workflow?: Partial<RecoveryWorkflow>
}

export interface PromiseToPayItem {
  id: string
  customer_id: string
  customer_name: string
  reference_type: string
  reference_id: string
  promised_amount: number
  currency: string
  promised_date: string
  grace_period_hours: number
  status: string
  reminder_sent_count: number
  notes?: string
  fulfilled_at?: string
  breached_at?: string
  created_at: string
  workflow?: Partial<RecoveryWorkflow>
}

