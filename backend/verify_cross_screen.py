import httpx
import json

client = httpx.Client(base_url='http://127.0.0.1:8000', timeout=10.0)

# Reset and run Scenario 1 + Scenario 2
client.post('/api/v1/demo/reset')
client.post('/api/v1/demo/scenario/successful_delayed_retry')
client.post('/api/v1/demo/scenario/high_risk_escalation')

dash = client.get('/api/v1/dashboard/overview').json()
wfs = client.get('/api/v1/recovery').json()
safety = client.get('/api/v1/safety/overview').json()
audit = client.get('/api/v1/audit/logs').json()

wfs_recovered_sum = sum(w['recovered_amount'] for w in wfs)
wfs_escalated_count = len([w for w in wfs if w['state'] == 'ESCALATED'])
wfs_stopped_count = len([w for w in wfs if w['state'] == 'STOPPED'])
wfs_active_count = len([w for w in wfs if w['state'] in ['PAYMENT_FAILED', 'RECOVERY_ELIGIBLE', 'RECOVERY_PLANNED', 'POLICY_APPROVED', 'ACTION_EXECUTING', 'AWAITING_PAYMENT_EVENT']])

comparison = {
    'recovered_revenue': {
        'dashboard': dash['metrics']['recovered_revenue'],
        'queue_sum': wfs_recovered_sum,
        'consistent': dash['metrics']['recovered_revenue'] == wfs_recovered_sum
    },
    'active_workflows': {
        'dashboard': dash['metrics']['active_recovery_workflows'],
        'queue_count': wfs_active_count,
        'consistent': dash['metrics']['active_recovery_workflows'] == wfs_active_count
    },
    'escalations': {
        'dashboard': dash['metrics']['human_escalations_count'],
        'queue_count': wfs_escalated_count,
        'safety_count': safety['total_human_escalations'],
        'consistent': dash['metrics']['human_escalations_count'] == wfs_escalated_count == safety['total_human_escalations']
    },
    'stopped': {
        'dashboard': dash['metrics']['stopped_actions_count'],
        'queue_count': wfs_stopped_count,
        'safety_count': safety['total_stopped_workflows'],
        'consistent': dash['metrics']['stopped_actions_count'] == wfs_stopped_count == safety['total_stopped_workflows']
    },
    'audit_entries_count': len(audit)
}

print(json.dumps(comparison, indent=2))
