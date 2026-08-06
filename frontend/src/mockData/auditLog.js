const baseTimestamp = Date.now()

const actions = ['Approve', 'Decline', 'Escalate to compliance', 'Alert fired', 'Retrain recommended', 'Freeze triggered']
const predictions = ['Low risk', 'Medium risk', 'High risk']
const approvers = ['Analyst', 'Risk Engineer', 'Compliance', 'System']

function round(value, digits = 2) {
  return Number(value.toFixed(digits))
}

export const auditLog = Array.from({ length: 50 }, (_, index) => {
  const action = actions[index % actions.length]
  const isDecision = index % 2 === 0

  return {
    decisionId: `DEC-${String(91000 + index).padStart(5, '0')}`,
    timestamp: new Date(baseTimestamp - index * 26 * 60 * 1000).toISOString(),
    modelVersion: index % 3 === 0 ? 'v4.8.2' : index % 3 === 1 ? 'v4.8.1' : 'v4.7.9',
    prediction: predictions[index % predictions.length],
    confidence: round(0.48 + (index % 12) * 0.035, 2),
    governanceAction: action,
    approver: isDecision ? approvers[index % 3] : 'System',
    userRole: isDecision ? approvers[index % 3] : 'System',
    transactionId: `TX-${String(18420 + (index % 30)).padStart(5, '0')}`,
    reason: isDecision
      ? 'Human review completed for a flagged payment.'
      : 'Automated governance event logged during the monitoring sweep.',
    type: isDecision ? 'Decision' : 'Governance',
  }
})