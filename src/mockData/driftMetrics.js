const baseTimestamp = Date.now()

function round(value, digits = 3) {
  return Number(value.toFixed(digits))
}

function buildHours() {
  return Array.from({ length: 24 }, (_, index) => {
    const timestamp = new Date(baseTimestamp - (23 - index) * 60 * 60 * 1000)
    return timestamp.toISOString()
  })
}

const hours = buildHours()

export const driftTimeSeries = hours

export const statisticalDrift = {
  transactionAmount: Array.from({ length: 24 }, (_, index) => round(0.07 + index * 0.004 + Math.sin(index / 4) * 0.018, 3)),
  deviceVelocity: Array.from({ length: 24 }, (_, index) => round(0.05 + index * 0.0035 + Math.cos(index / 5) * 0.02, 3)),
  geoDistance: Array.from({ length: 24 }, (_, index) => round(0.06 + index * 0.0025 + Math.sin((index + 2) / 3) * 0.016, 3)),
}

export const semanticDrift = Array.from({ length: 24 }, (_, index) => ({
  timestamp: hours[index],
  distance: round(0.11 + index * 0.006 + Math.sin(index / 2.8) * 0.02, 3),
}))

export const confidenceTrend = Array.from({ length: 24 }, (_, index) => ({
  timestamp: hours[index],
  confidence: round(0.94 - index * 0.004 - Math.sin(index / 4) * 0.015, 3),
}))

function buildDistribution(referenceCenter, currentCenter, width, count = 10) {
  return Array.from({ length: count }, (_, index) => {
    const position = index / Math.max(1, count - 1)
    const referenceDistance = Math.abs(position - referenceCenter)
    const currentDistance = Math.abs(position - currentCenter)

    return {
      bin: index,
      label: `${Math.round(position * 100)}th`,
      reference: Math.max(2, Math.round((1 - referenceDistance * width) * 18)),
      current: Math.max(2, Math.round((1 - currentDistance * width) * 18)),
    }
  })
}

export const driftDistributions = {
  transactionAmount: buildDistribution(0.42, 0.56, 1.1),
  deviceVelocity: buildDistribution(0.35, 0.67, 1.2),
  geoDistance: buildDistribution(0.5, 0.44, 1),
}

export const conceptDriftEvents = [
  {
    timestamp: hours[4],
    feature: 'merchantCategory',
    severity: 'Low',
    driftType: 'ADWIN',
    triggeredAction: false,
    reason: 'New merchant mix observed in card-present traffic.',
  },
  {
    timestamp: hours[8],
    feature: 'transactionAmount',
    severity: 'Medium',
    driftType: 'ADWIN',
    triggeredAction: true,
    reason: 'Amount distribution shifted above expected variance.',
  },
  {
    timestamp: hours[11],
    feature: 'deviceVelocity',
    severity: 'High',
    driftType: 'ADWIN',
    triggeredAction: true,
    reason: 'Velocity spike aligned with account takeover pattern.',
  },
  {
    timestamp: hours[16],
    feature: 'geoDistance',
    severity: 'Medium',
    driftType: 'ADWIN',
    triggeredAction: false,
    reason: 'Cross-border routing increased for a small cohort.',
  },
  {
    timestamp: hours[20],
    feature: 'merchantCategory',
    severity: 'High',
    driftType: 'ADWIN',
    triggeredAction: true,
    reason: 'Concept drift correlated with repeat escalation decisions.',
  },
]

export const governanceActions = [
  {
    id: 'GA-014',
    timestamp: hours[22],
    action: 'Alert fired',
    reason: 'PSI threshold breached on deviceVelocity.',
    severity: 'Watch',
  },
  {
    id: 'GA-015',
    timestamp: hours[19],
    action: 'Retrain recommended',
    reason: 'Confidence decay exceeded the configured tolerance.',
    severity: 'Watch',
  },
  {
    id: 'GA-016',
    timestamp: hours[16],
    action: 'Rollback executed',
    reason: 'Risk committee approved fallback to previous model.',
    severity: 'Alert',
  },
  {
    id: 'GA-017',
    timestamp: hours[13],
    action: 'Freeze triggered',
    reason: 'Fraud pattern volatility crossed emergency boundary.',
    severity: 'Alert',
  },
  {
    id: 'GA-018',
    timestamp: hours[11],
    action: 'Alert fired',
    reason: 'Semantic drift detected in device descriptions.',
    severity: 'Watch',
  },
  {
    id: 'GA-019',
    timestamp: hours[9],
    action: 'Retrain recommended',
    reason: 'Feature attribution changes stayed elevated for 3 checks.',
    severity: 'Watch',
  },
  {
    id: 'GA-020',
    timestamp: hours[7],
    action: 'Alert fired',
    reason: 'Low confidence approvals trended upward.',
    severity: 'Normal',
  },
  {
    id: 'GA-021',
    timestamp: hours[5],
    action: 'Freeze triggered',
    reason: 'Escalation policy entered manual review mode.',
    severity: 'Alert',
  },
  {
    id: 'GA-022',
    timestamp: hours[3],
    action: 'Rollback executed',
    reason: 'Rollback aligned with compliance guidance.',
    severity: 'Alert',
  },
  {
    id: 'GA-023',
    timestamp: hours[1],
    action: 'Alert fired',
    reason: 'Latest poll remained in watch state.',
    severity: 'Watch',
  },
]

export const storyTimeline = [
  {
    timestamp: hours[9],
    title: 'Drift alert on device velocity',
    detail: 'PSI crossed the watch threshold and flagged a cluster of new devices.',
    tone: 'Watch',
  },
  {
    timestamp: hours[8],
    title: 'Model auto-froze and fallback rules activated',
    detail: 'Emergency governance policy paused automated approvals until review completed.',
    tone: 'Alert',
  },
  {
    timestamp: hours[6],
    title: 'Review queue volume increased',
    detail: 'Flagged transactions from new geographies were routed to the analyst queue.',
    tone: 'Watch',
  },
  {
    timestamp: hours[4],
    title: 'Retrain recommendation prepared',
    detail: 'Confidence decay and concept drift aligned enough to recommend retraining.',
    tone: 'Normal',
  },
  {
    timestamp: hours[2],
    title: 'Compliance approval received',
    detail: 'Policy draft reviewed and approved for publication in the next maintenance window.',
    tone: 'Normal',
  },
]