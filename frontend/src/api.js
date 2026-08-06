const API_BASE = '/api/v1'

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`HTTP ${response.status}: ${text}`)
  }
  return response.json()
}

export async function getHealth() {
  return request('/health')
}

export async function getPolicies() {
  return request('/policies')
}

export async function getPolicyHistory() {
  return request('/policies/history')
}

export async function savePolicyDraft(policy) {
  return request('/policies/draft', {
    method: 'POST',
    body: JSON.stringify(policy),
  })
}

export async function getAuditLog() {
  return request('/audit')
}

export async function getMetrics() {
  return request('/metrics')
}

export async function getDashboard() {
  return request('/dashboard')
}

export async function predictTransaction(features) {
  return request('/predict', {
    method: 'POST',
    body: JSON.stringify({ model_name: 'fraud_classifier', features }),
  })
}

export async function getDriftHistory() {
  return request('/drift/history')
}

export async function postDriftStatistical(payload) {
  return request('/drift/statistical', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getTransactions() {
  return request('/transactions')
}

export async function updateTransactionStatus(requestId, status, userRole = 'Analyst') {
  return request(`/transactions/${encodeURIComponent(requestId)}/status`, {
    method: 'POST',
    body: JSON.stringify({ status }),
  })
}

export async function getGovernanceActions() {
  const audit = await request('/audit')
  return audit
    .filter((entry) => entry.action === 'predict')
    .slice(0, 10)
    .map((entry) => ({
      id: entry.decisionId || entry.id,
      action: entry.status,
      reason: entry.metadata?.reason || `Prediction ${entry.status}`,
      timestamp: entry.created_at || entry.timestamp,
      severity: entry.status === 'block' ? 'Alert' : entry.status === 'review' ? 'Watch' : 'Normal',
    }))
}

export async function getStoryTimeline() {
  const audit = await request('/audit')
  return audit.slice(0, 10).map((entry) => ({
    id: entry.decisionId || entry.id,
    timestamp: entry.created_at || entry.timestamp,
    title: entry.action,
    description: entry.metadata?.reason || `Action: ${entry.action}`,
    severity: entry.status,
  }))
}
