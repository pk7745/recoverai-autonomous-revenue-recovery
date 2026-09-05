import React, { useState, useEffect } from 'react'
import { Header } from './components/Header'
import { Sidebar, TabId } from './components/Sidebar'
import { OverviewPage } from './pages/OverviewPage'
import { RecoveryQueuePage } from './pages/RecoveryQueuePage'
import { SafetyCenterPage } from './pages/SafetyCenterPage'
import { ExperimentsPage } from './pages/ExperimentsPage'
import { AuditTrailPage } from './pages/AuditTrailPage'
import { PoliciesPage } from './pages/PoliciesPage'
import { DemoScenarioRunner } from './components/DemoScenarioRunner'
import { RecoveryDecisionModal } from './components/RecoveryDecisionModal'
import { OperationsAssistant } from './components/OperationsAssistant'
import { LoginPage } from './components/LoginPage'
import { AuthProvider, useAuth } from './context/AuthContext'
import { api } from './services/api'
import {
  DashboardOverview,
  RecoveryWorkflow,
  SafetyOverview,
  BenchmarkComparisonResponse,
  MerchantPolicy,
  AuditLog
} from './types'

import { RecoveryProgramsPage } from './pages/RecoveryProgramsPage'

const AppContent: React.FC = () => {
  const { user, isLoading } = useAuth()

  const [currentTab, setCurrentTab] = useState<TabId>('overview')
  const [dashboardData, setDashboardData] = useState<DashboardOverview | null>(null)
  const [workflows, setWorkflows] = useState<RecoveryWorkflow[]>([])
  const [safetyData, setSafetyData] = useState<SafetyOverview | null>(null)
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkComparisonResponse | null>(null)
  const [merchantPolicies, setMerchantPolicies] = useState<MerchantPolicy | null>(null)
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [selectedWorkflow, setSelectedWorkflow] = useState<RecoveryWorkflow | null>(null)
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false)
  const [isProcessingModal, setIsProcessingModal] = useState<boolean>(false)

  const refreshAllData = async () => {
    if (!user) return
    try {
      setIsRefreshing(true)
      const [dash, wfs, safety, bench, pol, logs] = await Promise.all([
        api.getDashboardOverview(),
        api.getRecoveryWorkflows(),
        api.getSafetyOverview(),
        api.getBenchmark(),
        api.getMerchantPolicy(),
        api.getAuditLogs(100)
      ])
      setDashboardData(dash)
      setWorkflows(wfs)
      setSafetyData(safety)
      setBenchmarkData(bench)
      setMerchantPolicies(pol)
      setAuditLogs(logs)

      if (selectedWorkflow) {
        const updated = wfs.find((w) => w.id === selectedWorkflow.id)
        if (updated) setSelectedWorkflow(updated)
      }
    } catch (err) {
      console.error('Error fetching RecoverAI telemetry:', err)
    } finally {
      setIsRefreshing(false)
    }
  }

  useEffect(() => {
    if (user) {
      refreshAllData()
    }
  }, [user])

  const handlePlan = async (id: string) => {
    try {
      setIsProcessingModal(true)
      const updated = await api.planRecoveryWorkflow(id)
      setSelectedWorkflow(updated)
      await refreshAllData()
    } catch (err: any) {
      alert(`Plan error: ${err.message}`)
    } finally {
      setIsProcessingModal(false)
    }
  }

  const handleExecute = async (id: string) => {
    try {
      setIsProcessingModal(true)
      const updated = await api.executeRecoveryWorkflow(id)
      setSelectedWorkflow(updated)
      await refreshAllData()
    } catch (err: any) {
      alert(`Execution error: ${err.message}`)
    } finally {
      setIsProcessingModal(false)
    }
  }

  const handleApprove = async (id: string) => {
    try {
      setIsProcessingModal(true)
      const updated = await api.approveEscalation(id, 'Approved via Manager Decision Studio')
      setSelectedWorkflow(updated)
      await refreshAllData()
    } catch (err: any) {
      alert(`Approval error: ${err.message}`)
    } finally {
      setIsProcessingModal(false)
    }
  }

  const handleStop = async (id: string) => {
    try {
      setIsProcessingModal(true)
      const updated = await api.stopWorkflow(id)
      setSelectedWorkflow(updated)
      await refreshAllData()
    } catch (err: any) {
      alert(`Stop error: ${err.message}`)
    } finally {
      setIsProcessingModal(false)
    }
  }

  const handleSelectWorkflowById = async (wfId: string) => {
    try {
      const wf = await api.getRecoveryWorkflow(wfId)
      if (wf) {
        setSelectedWorkflow(wf)
      }
    } catch {
      // Fallback
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0B0F17] flex items-center justify-center text-slate-400 font-mono text-xs">
        <div className="flex items-center space-x-2">
          <div className="h-2 w-2 rounded-full bg-blue-500 animate-ping"></div>
          <span>Initializing RecoverAI Secure Session...</span>
        </div>
      </div>
    )
  }

  if (!user) {
    return <LoginPage />
  }

  const escalationCount = workflows.filter((w) => w.state === 'ESCALATED').length

  const getTabLabel = (tab: TabId) => {
    switch (tab) {
      case 'overview': return 'Command Center'
      case 'programs': return 'Recovery Programs'
      case 'queue': return 'Recovery Queue'
      case 'safety': return 'Safety Center'
      case 'policies': return 'Merchant Policies'
      case 'experiments': return '10k Benchmark'
      case 'audit': return 'Audit Trail'
      case 'demo': return 'Demo Lab'
      default: return 'Command Center'
    }
  }

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 flex flex-col font-sans relative">
      <Header
        onRefresh={refreshAllData}
        isRefreshing={isRefreshing}
        currentTabLabel={getTabLabel(currentTab)}
        onSelectWorkflowId={handleSelectWorkflowById}
      />

      <div className="flex-1 flex">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          escalationCount={escalationCount}
        />

        <main className="flex-1 p-6 md:p-8 overflow-y-auto max-h-[calc(100vh-4rem)]">
          {currentTab === 'overview' && (
            <OverviewPage
              overview={dashboardData}
              workflows={workflows}
              onSelectWorkflow={setSelectedWorkflow}
              onNavigateToQueue={() => setCurrentTab('queue')}
              onNavigateToDemo={() => setCurrentTab('demo')}
            />
          )}

          {currentTab === 'programs' && (
            <RecoveryProgramsPage
              onSelectWorkflow={handleSelectWorkflowById}
            />
          )}

          {currentTab === 'queue' && (
            <RecoveryQueuePage
              workflows={workflows}
              onSelectWorkflow={setSelectedWorkflow}
              onRefresh={refreshAllData}
              isRefreshing={isRefreshing}
            />
          )}

          {currentTab === 'safety' && (
            <SafetyCenterPage
              safety={safetyData}
              workflows={workflows}
              onSelectWorkflow={setSelectedWorkflow}
            />
          )}

          {currentTab === 'experiments' && (
            <ExperimentsPage
              benchmark={benchmarkData}
              onBenchmarkUpdate={setBenchmarkData}
            />
          )}

          {currentTab === 'audit' && (
            <AuditTrailPage
              logs={auditLogs}
              onRefresh={refreshAllData}
              isRefreshing={isRefreshing}
            />
          )}

          {currentTab === 'policies' && (
            <PoliciesPage
              policies={merchantPolicies}
              onPoliciesUpdated={setMerchantPolicies}
            />
          )}

          {currentTab === 'demo' && (
            <DemoScenarioRunner onScenarioComplete={refreshAllData} />
          )}
        </main>
      </div>

      {/* Decision & Policy Inspector Modal */}
      <RecoveryDecisionModal
        workflow={selectedWorkflow}
        onClose={() => setSelectedWorkflow(null)}
        onPlan={handlePlan}
        onExecute={handleExecute}
        onApprove={handleApprove}
        onStop={handleStop}
        isProcessing={isProcessingModal}
      />

      {/* Phase 6: Grounded Operations Assistant */}
      <OperationsAssistant />
    </div>
  )
}

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}
