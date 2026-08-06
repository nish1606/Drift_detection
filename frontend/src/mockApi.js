import { auditLog as seedAuditLog } from './mockData/auditLog'
import { confidenceTrend, conceptDriftEvents, driftDistributions, driftTimeSeries, governanceActions, semanticDrift, statisticalDrift, storyTimeline } from './mockData/driftMetrics'
import { policyHistory as seedPolicyHistory, policies as seedPolicies } from './mockData/policies'
import { transactions as seedTransactions } from './mockData/transactions'

const delay = (ms = 240) => new Promise((resolve) => setTimeout(resolve, ms))

const clone = (value) => JSON.parse(JSON.stringify(value))

let transactionState = clone(seedTransactions)
let policyState = clone(seedPolicies)
let policyHistoryState = clone(seedPolicyHistory)
let auditLogState = clone(seedAuditLog)
let liveTick = 0
let transactionSequence = seedTransactions.length

function buildLiveTransaction() {
  transactionSequence += 1
  const amount = Number((1800 + (liveTick % 5) * 430 + transactionSequence * 12).toFixed(0))
  const confidence = Number((0.41 + (liveTick % 4) * 0.07).toFixed(2))

  return {
    id: `TX-${String(18420 + transactionSequence).padStart(5, '0')}`,
    amount,
    timestamp: new Date().toISOString(),
    confidence,
    features: {
      transactionAmount: amount,
      deviceVelocity: Number((1.6 + (liveTick % 3) * 0.55).toFixed(2)),
      geoDistance: Number((22 + (liveTick % 5) * 8.4).toFixed(2)),
      accountAgeDays: 11 + (liveTick % 7),
      ipRiskScore: Number((0.33 + (liveTick % 4) * 0.09).toFixed(2)),
      merchantRiskScore: Number((0.42 + (liveTick % 3) * 0.08).toFixed(2)),
      previousChargebacks: liveTick % 2,
      browserAgeDays: 4 + (liveTick % 6),
      paymentInstrumentAgeDays: 6 + (liveTick % 5),
      riskProfile: liveTick % 2 === 0 ? 'new device with elevated spend' : 'high-velocity device pattern',
    },
    shapValues: [
      { feature: 'deviceVelocity', value: 0.19 },
      { feature: 'transactionAmount', value: 0.14 },
      { feature: 'geoDistance', value: 0.09 },
      { feature: 'accountAgeDays', value: -0.06 },
      { feature: 'ipRiskScore', value: 0.05 },
    ],
    topFactor: 'deviceVelocity',
    status: 'Pending',
    modelVersion: 'v4.8.2',
    prediction: 'Medium risk',
    reason: 'Live transaction entered the queue from the polling stream.',
  }
}

function bumpLiveState() {
  liveTick += 1

  transactionState = transactionState.map((transaction, index) => {
    if (index !== liveTick % transactionState.length) {
      return transaction
    }

    const confidenceShift = (liveTick % 4 - 1.5) * 0.01
    return {
      ...transaction,
      confidence: Number(Math.max(0.35, Math.min(0.98, transaction.confidence + confidenceShift)).toFixed(2)),
    }
  })

  if (liveTick % 4 === 0) {
    transactionState = [buildLiveTransaction(), ...transactionState].slice(0, 32)
  }

  if (liveTick % 3 === 0) {
    const action = governanceActions[liveTick % governanceActions.length]
    auditLogState = [
      {
        decisionId: `DEC-${String(98000 + liveTick).padStart(5, '0')}`,
        timestamp: new Date().toISOString(),
        modelVersion: 'v4.8.2',
        prediction: 'Medium risk',
        confidence: 0.61,
        governanceAction: action.action,
        approver: 'System',
        userRole: 'System',
        transactionId: transactionState[liveTick % transactionState.length].id,
        reason: action.reason,
        type: 'Governance',
      },
      ...auditLogState,
    ].slice(0, 60)
  }
}

export async function getTransactions() {
  await delay()
  bumpLiveState()
  return clone(transactionState)
}

export async function getTransactionById(id) {
  await delay()
  bumpLiveState()
  return clone(transactionState.find((transaction) => transaction.id === id) ?? null)
}

export async function updateTransactionStatus(id, status, userRole = 'Analyst') {
  await delay(320)
  transactionState = transactionState.map((transaction) =>
    transaction.id === id
      ? {
          ...transaction,
          status,
        }
      : transaction,
  )

  const updatedTransaction = transactionState.find((transaction) => transaction.id === id)

  auditLogState = [
    {
      decisionId: `DEC-${String(99000 + liveTick).padStart(5, '0')}`,
      timestamp: new Date().toISOString(),
      modelVersion: updatedTransaction?.modelVersion ?? 'v4.8.2',
      prediction: updatedTransaction?.prediction ?? 'Medium risk',
      confidence: updatedTransaction?.confidence ?? 0.5,
      governanceAction: status,
      approver: userRole,
      userRole,
      transactionId: id,
      reason: `Transaction ${status.toLowerCase()} by ${userRole}.`,
      type: 'Decision',
    },
    ...auditLogState,
  ].slice(0, 60)

  return clone(updatedTransaction ?? null)
}

export async function getDriftMetrics() {
  await delay()
  bumpLiveState()

  const driftOffset = (liveTick % 5) * 0.002

  return {
    timeLabels: driftTimeSeries,
    statisticalDrift: {
      transactionAmount: statisticalDrift.transactionAmount.map((value, index) =>
        Number((value + (index === statisticalDrift.transactionAmount.length - 1 ? driftOffset : 0)).toFixed(3)),
      ),
      deviceVelocity: statisticalDrift.deviceVelocity.map((value, index) =>
        Number((value + (index === statisticalDrift.deviceVelocity.length - 1 ? driftOffset * 1.2 : 0)).toFixed(3)),
      ),
      geoDistance: statisticalDrift.geoDistance.map((value, index) =>
        Number((value + (index === statisticalDrift.geoDistance.length - 1 ? driftOffset * 0.8 : 0)).toFixed(3)),
      ),
    },
    semanticDrift: semanticDrift.map((point, index) => ({
      ...point,
      distance: Number((point.distance + (index === semanticDrift.length - 1 ? driftOffset * 2 : 0)).toFixed(3)),
    })),
    confidenceTrend: confidenceTrend.map((point, index) => ({
      ...point,
      confidence: Number((point.confidence - (index === confidenceTrend.length - 1 ? driftOffset * 1.5 : 0)).toFixed(3)),
    })),
    conceptDriftEvents: clone(conceptDriftEvents),
    driftDistributions: clone(driftDistributions),
  }
}

export async function getPolicies() {
  await delay()
  return clone(policyState)
}

export async function getPolicyHistory() {
  await delay()
  return clone(policyHistoryState)
}

export async function savePolicyDraft(policy) {
  await delay(360)

  const updatedPolicy = {
    ...policy,
    lastModified: new Date().toISOString(),
    modifiedBy: policy.modifiedBy ?? 'Current user',
    version: policy.version ?? '1.0',
  }

  policyState = policyState.map((entry) => (entry.id === updatedPolicy.id ? updatedPolicy : entry))

  policyHistoryState = [
    {
      id: `H-${String(100 + policyHistoryState.length).padStart(3, '0')}`,
      policyName: updatedPolicy.name,
      changedAt: updatedPolicy.lastModified,
      changedBy: updatedPolicy.modifiedBy,
      changeSummary: `Published draft for ${updatedPolicy.name}.`,
    },
    ...policyHistoryState,
  ]

  auditLogState = [
    {
      decisionId: `DEC-${String(99500 + liveTick).padStart(5, '0')}`,
      timestamp: updatedPolicy.lastModified,
      modelVersion: 'v4.8.2',
      prediction: 'Governance update',
      confidence: 1,
      governanceAction: 'Policy published',
      approver: updatedPolicy.modifiedBy,
      userRole: 'Compliance',
      transactionId: 'POLICY',
      reason: `Policy ${updatedPolicy.name} moved to publish stage.`,
      type: 'Governance',
    },
    ...auditLogState,
  ].slice(0, 60)

  return clone(updatedPolicy)
}

export async function getAuditLog() {
  await delay()
  return clone(auditLogState)
}

export async function getGovernanceActions() {
  await delay()
  bumpLiveState()
  return clone(governanceActions.slice(0, 10))
}

export async function getStoryTimeline() {
  await delay()
  return clone(storyTimeline)
}