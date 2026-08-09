const API_BASE = 'http://localhost:8000/api/v1'

async function request(path, options = {}, role = 'Analyst') {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
  if (response.status === 401) {
    localStorage.removeItem('access_token')
    localStorage.removeItem('role')
    localStorage.removeItem('username')
    window.location.href = '/login'
    throw new Error('Session expired')
  }
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`HTTP ${response.status}: ${text}`)
  }
  return response.json()
}

function mapPredictionToTransaction(pred) {
  const confidence = pred.probability ?? pred.confidence ?? 0
  const decision = pred.decision || (confidence >= 0.75 ? 'block' : confidence >= 0.45 ? 'review' : 'approve')
  const statusMap = { block: 'Escalated', review: 'Pending', approve: 'Approved' }
  const shapValues = (pred.explanations?.top_features || []).map(([feature, value]) => ({ feature, value: Number(value) }))
  return {
    id: pred.request_id || pred.id,
    timestamp: pred.timestamp || pred.created_at,
    amount: pred.amount ?? pred.raw_features?.amount ?? 0,
    confidence,
    prediction: pred.prediction,
    modelVersion: pred.model_version,
    status: statusMap[decision] || 'Pending',
    decision,
    features: pred.raw_features || pred.engineered_features || {},
    shapValues,
    topFactor: shapValues[0]?.feature || 'N/A',
    reason: pred.explanations?.fallback ? 'Rule-based score' : 'Model prediction',
  }
}

function mapAuditToGovernance(entry) {
  const action = (entry.action || '').toLowerCase()
  const isRollback = action.includes('rollback')
  const isFreeze = action.includes('freeze')
  const governanceAction = isRollback ? 'Rollback' : isFreeze ? 'Freeze' : entry.action
  const metadata = entry.metadata || {}
  const reason = metadata.reason || `Prediction ${entry.status}`
  const modelVersion = metadata.model_version || metadata.rollback_to_version || 'v4.8.2'
  return {
    id: entry.id,
    action: governanceAction,
    reason,
    timestamp: entry.created_at || entry.timestamp,
    severity: entry.status === 'block' ? 'Alert' : entry.status === 'review' ? 'Watch' : 'Normal',
    modelVersion,
    triggeredBy: metadata.policy_name || metadata.policy_id || 'System policy',
  }
}

function mapAuditToStory(entry) {
  const metadata = entry.metadata || {}
  return {
    id: entry.id,
    timestamp: entry.created_at || entry.timestamp,
    title: entry.action,
    detail: metadata.reason || `Action: ${entry.action}`,
    tone: entry.status === 'block' ? 'Alert' : entry.status === 'review' ? 'Watch' : 'Normal',
  }
}

function mapAuditToTable(entry) {
  const metadata = entry.metadata || {}
  const features = metadata.features || metadata.raw_features || {}
  const featureKeys = Object.keys(features)
  const inputFeatures = featureKeys.length
    ? featureKeys.map((key) => `${key}=${features[key]}`).join(', ')
    : '—'
  return {
    id: entry.id,
    decisionId: entry.resource_id || entry.id,
    transactionId: entry.resource_id || entry.id,
    governanceAction: entry.action,
    approver: entry.actor,
    reason: metadata.reason || '',
    modelVersion: metadata.model_version || 'v4.8.2',
    prediction: metadata.prediction ?? entry.status,
    confidence: metadata.probability ?? metadata.confidence ?? 0,
    timestamp: entry.created_at || entry.timestamp,
    inputFeatures,
  }
}

export async function getHealth(role = 'Analyst') {
  return request('/health', {}, role)
}

export async function getPolicies(role = 'Analyst') {
  return request('/policies', {}, role)
}

export async function getPolicyHistory(role = 'Analyst') {
  try {
    return await request('/policies', {}, role)
  } catch {
    return []
  }
}

export async function savePolicyDraft(policy, role = 'Analyst') {
  return request('/policies', {
    method: 'POST',
    body: JSON.stringify(policy),
  }, role)
}

export async function getAuditLog(role = 'Analyst') {
  const audit = await request('/audit', {}, role)
  return audit.map(mapAuditToTable)
}

export async function getDashboard(role = 'Analyst') {
  return request('/dashboard', {}, role)
}

export async function predictTransaction(features, role = 'Analyst') {
  return request('/predict', {
    method: 'POST',
    body: JSON.stringify({ model_name: 'fraud_classifier', features }),
  }, role)
}

export async function getDriftHistory(role = 'Analyst') {
  return request('/summary', {}, role)
}

export async function postDriftStatistical(payload, role = 'Analyst') {
  return request('/drift/statistical', {
    method: 'POST',
    body: JSON.stringify(payload),
  }, role)
}

export async function getTransactions(role = 'Analyst') {
  const predictions = await request('/predictions?limit=200', {}, role)
  return predictions.map((pred) => mapPredictionToTransaction(pred, role))
}

export async function updateTransactionStatus(requestId, status) {
  return Promise.resolve({ request_id: requestId, status: status.toLowerCase() })
}

export async function getGovernanceActions(role = 'Analyst') {
  const audit = await request('/audit', {}, role)
  return audit.map(mapAuditToGovernance).slice(0, 10)
}

export async function getStoryTimeline(role = 'Analyst') {
  const audit = await request('/audit', {}, role)
  return audit.map(mapAuditToStory).slice(0, 10)
}
