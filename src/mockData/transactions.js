const baseTimestamp = Date.now()

const riskProfiles = [
  'unusual card testing',
  'high-velocity device pattern',
  'geo-location mismatch',
  'beneficiary divergence',
  'new device with elevated spend',
  'merchant risk concentration',
]

const statuses = ['Pending', 'Pending', 'Pending', 'Approved', 'Declined', 'Escalated']

function round(value, digits = 2) {
  return Number(value.toFixed(digits))
}

function buildShapValues(index) {
  const factors = [
    ['deviceVelocity', 0.17 - (index % 4) * 0.015],
    ['transactionAmount', 0.14 - (index % 3) * 0.02],
    ['geoDistance', index % 2 === 0 ? 0.12 : -0.08],
    ['accountAgeDays', -0.09 - (index % 5) * 0.01],
    ['ipRiskScore', index % 3 === 0 ? 0.11 : -0.04],
  ]

  return factors.map(([feature, value]) => ({ feature, value: round(value, 3) }))
}

function buildFeatures(index, amount) {
  return {
    transactionAmount: amount,
    deviceVelocity: round(1.1 + (index % 6) * 0.45, 2),
    geoDistance: round(18 + (index % 7) * 11.2, 2),
    accountAgeDays: 12 + (index % 8) * 9,
    ipRiskScore: round(0.22 + (index % 5) * 0.11, 2),
    merchantRiskScore: round(0.31 + (index % 4) * 0.13, 2),
    previousChargebacks: index % 4,
    browserAgeDays: 3 + (index % 6) * 4,
    paymentInstrumentAgeDays: 7 + (index % 5) * 6,
    riskProfile: riskProfiles[index % riskProfiles.length],
  }
}

export const transactions = Array.from({ length: 30 }, (_, index) => {
  const amount = round(850 + index * 245 + (index % 4) * 185, 0)
  const confidence = round(0.42 + ((index * 7) % 18) * 0.03, 2)
  const shapValues = buildShapValues(index)
  const sorted = [...shapValues].sort((left, right) => Math.abs(right.value) - Math.abs(left.value))

  return {
    id: `TX-${String(18420 + index).padStart(5, '0')}`,
    amount,
    timestamp: new Date(baseTimestamp - index * 55 * 60 * 1000).toISOString(),
    confidence,
    features: buildFeatures(index, amount),
    shapValues,
    topFactor: sorted[0].feature,
    status: statuses[index % statuses.length],
    modelVersion: index % 3 === 0 ? 'v4.8.2' : index % 3 === 1 ? 'v4.8.1' : 'v4.7.9',
    prediction: index % 5 === 0 ? 'High risk' : 'Medium risk',
    reason: riskProfiles[index % riskProfiles.length],
  }
})