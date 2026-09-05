import httpx
import json

client = httpx.Client(base_url='http://127.0.0.1:8000', timeout=10.0)

results = {}

# --- Scenario 1 ---
client.post('/api/v1/demo/reset')
s1 = client.post('/api/v1/demo/scenario/successful_delayed_retry').json()
wf1 = client.get(f"/api/v1/recovery/{s1['workflow_id']}").json()
results['Scenario 1'] = {
    'workflow_id': s1['workflow_id'],
    'state': wf1['state'],
    'recovered_amount': wf1['recovered_amount'],
    'financial_outcome': s1.get('financial_outcome'),
    'pass': wf1['state'] == 'RECOVERED' and wf1['recovered_amount'] == 4999.0 and 'Settled' in s1.get('financial_outcome', '')
}

# --- Scenario 2 ---
client.post('/api/v1/demo/reset')
s2 = client.post('/api/v1/demo/scenario/high_risk_escalation').json()
wf2 = client.get(f"/api/v1/recovery/{s2['workflow_id']}").json()
results['Scenario 2'] = {
    'workflow_id': s2['workflow_id'],
    'state': wf2['state'],
    'recovered_amount': wf2['recovered_amount'],
    'exposure_amount': s2.get('exposure_amount'),
    'financial_outcome': s2.get('financial_outcome'),
    'pass': (
        wf2['state'] == 'ESCALATED' and 
        wf2['recovered_amount'] == 0.0 and 
        s2.get('recovered_amount') == 0.0 and 
        '₹0 Recovered' in s2.get('financial_outcome', '')
    )
}

# --- Scenario 3 ---
client.post('/api/v1/demo/reset')
s3 = client.post('/api/v1/demo/scenario/max_retries_stopped').json()
wf3 = client.get(f"/api/v1/recovery/{s3['workflow_id']}").json()
results['Scenario 3'] = {
    'workflow_id': s3['workflow_id'],
    'state': wf3['state'],
    'recovered_amount': wf3['recovered_amount'],
    'financial_outcome': s3.get('financial_outcome'),
    'pass': wf3['state'] == 'STOPPED' and wf3['recovered_amount'] == 0.0 and '₹0 Recovered' in s3.get('financial_outcome', '')
}

# --- Scenario 4 ---
client.post('/api/v1/demo/reset')
s4 = client.post('/api/v1/demo/scenario/duplicate_webhook_protection').json()
results['Scenario 4'] = {
    'event_id': s4['event_id'],
    'duplicate_detected': s4['duplicate_detected'],
    'financial_outcome': s4.get('financial_outcome'),
    'pass': s4['duplicate_detected'] is True and 'Zero Financial Mutation' in s4.get('financial_outcome', '')
}

# --- Scenario 5 ---
client.post('/api/v1/demo/reset')
s5 = client.post('/api/v1/demo/scenario/already_recovered_no_action').json()
wf5 = client.get(f"/api/v1/recovery/{s5['workflow_id']}").json()
results['Scenario 5'] = {
    'workflow_id': s5['workflow_id'],
    'state': wf5['state'],
    'recommended_action': wf5['recommended_action'],
    'financial_outcome': s5.get('financial_outcome'),
    'pass': wf5['recommended_action'] == 'NO_ACTION' and 'Zero Duplicate Action' in s5.get('financial_outcome', '')
}

print(json.dumps(results, indent=2))
