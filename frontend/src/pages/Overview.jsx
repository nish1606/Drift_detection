import { useEffect, useMemo, useState } from 'react'
import LiveTransactionStream from '../components/LiveTransactionStream'
import DriftChart from '../components/DriftChart'
import ModelHealthGauge from '../components/ModelHealthGauge'
import MetricCard from '../components/MetricCard'
import StoryTimeline from '../components/StoryTimeline'
import TooltipTerm from '../components/TooltipTerm'
import LastUpdated from '../components/LastUpdated'
import { getDriftHistory, getGovernanceActions, getStoryTimeline, getTransactions } from '../api'
import { formatDateTime, formatPercent } from '../utils/formatters'

const driftFeatureOptions = [
  { value: 'transactionAmount', label: 'Transaction amount' },
  { value: 'deviceVelocity', label: 'Device velocity' },
  { value: 'geoDistance', label: 'Geo distance' },
]

function getDriftStatus(latestValue) {
  if (latestValue >= 0.2) {
    return { label: 'Alert', tone: 'danger' }
  }

  if (latestValue >= 0.14) {
    return { label: 'Watch', tone: 'warning' }
  }

  return { label: 'Normal', tone: 'success' }
}

export default function Overview({ role }) {
  const [transactions, setTransactions] = useState([])
  const [driftMetrics, setDriftMetrics] = useState(null)
  const [actions, setActions] = useState([])
  const [story, setStory] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedFeature, setSelectedFeature] = useState('transactionAmount')
  const [lastRefreshed, setLastRefreshed] = useState(null)

  useEffect(() => {
    let active = true

    const load = async () => {
      try {
        setLoading(true)
        const [nextTransactions, nextDriftMetrics, nextActions, nextStory] = await Promise.all([
          getTransactions(role),
          getDriftHistory(role),
          getGovernanceActions(role),
          getStoryTimeline(role),
        ])

        if (!active) {
          return
        }

        setTransactions(nextTransactions)
        setDriftMetrics(nextDriftMetrics)
        setActions(nextActions)
        setStory(nextStory)
        setLastRefreshed(new Date().toISOString())
      } catch (error) {
        console.error('Overview load failed:', error)
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    load()
    const timer = window.setInterval(load, 12000)

    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [role])

  const dashboardMetrics = useMemo(() => buildDashboardMetrics(transactions, driftMetrics, selectedFeature), [driftMetrics, selectedFeature, transactions])

  const driftData = useMemo(() => {
    if (!driftMetrics) {
      return null
    }

    return {
      labels: driftMetrics.timeLabels.map((value) => formatDateTime(value)),
      datasets: [
        {
          label: driftFeatureOptions.find((option) => option.value === selectedFeature)?.label ?? 'Feature',
          data: driftMetrics.statisticalDrift[selectedFeature],
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
        },
      ],
    }
  }, [driftMetrics, selectedFeature])

  const confidenceData = useMemo(() => {
    if (!driftMetrics) {
      return null
    }

    return {
      labels: driftMetrics.timeLabels.map((value) => formatDateTime(value)),
      datasets: [
        {
          label: 'Average model confidence',
          data: driftMetrics.confidenceTrend.map((point) => point.confidence),
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
        },
      ],
    }
  }, [driftMetrics])

  if (loading && !driftMetrics) {
    return <SkeletonOverview />
  }

  return (
    <div className="space-y-6">
      <ModelHealthGauge score={dashboardMetrics.healthScore} summary={dashboardMetrics} />

      <section className="flex items-center justify-between">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">Live dashboard</h2>
        <LastUpdated lastRefreshed={lastRefreshed} />
      </section>

      <section className="grid gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <LiveTransactionStream transactions={transactions} />
        <StoryTimeline entries={story} />
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Transactions today" value={dashboardMetrics.transactionsToday} sublabel="All inbound scored events" />
        <MetricCard label="Flagged for review" value={dashboardMetrics.flaggedForReview} sublabel="Pending and escalated cases" tone="warning" />
        <MetricCard label="Avg model confidence" value={dashboardMetrics.averageConfidencePercent} suffix="%" sublabel="Running across the sampled queue" tone="success" />
        <MetricCard label="Drift status" value={dashboardMetrics.driftStatusLabel} sublabel={<span><TooltipTerm label="PSI" tip="Population Stability Index, a simple measure of whether the current data distribution differs from the baseline." /> latest signal: {formatPercent(dashboardMetrics.latestDriftValue, 0)}</span>} tone={dashboardMetrics.driftStatusTone} animate={false} />
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        {driftData ? (
          <DriftChart
            title="Drift trend"
            subtitle="Last 24 hours with feature selector"
            labels={driftData.labels}
            datasets={driftData.datasets}
            selector={{ value: selectedFeature, options: driftFeatureOptions }}
            onSelectorChange={setSelectedFeature}
            trendMode="lowerIsBetter"
            options={{
              plugins: {
                legend: { display: true },
              },
              scales: {
                y: {
                  min: 0,
                  max: 0.3,
                },
              },
            }}
          />
        ) : null}

        {confidenceData ? (
          <DriftChart
            title="Confidence trend"
            subtitle={<span>Average <TooltipTerm label="confidence score" tip="The model’s probability-style estimate of how risky a transaction is, from low to high." /> across the last 24 hours</span>}
            labels={confidenceData.labels}
            datasets={confidenceData.datasets}
            trendMode="higherIsBetter"
            options={{
              plugins: { legend: { display: true } },
              scales: {
                y: {
                  min: 0.4,
                  max: 1,
                },
              },
            }}
          />
        ) : null}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">Recent governance actions</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Last 10 alerts, rollbacks, freezes, and retrain recommendations.</p>
          </div>
          <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
            Live feed
          </span>
        </div>

        <div className="mt-4 grid gap-2">
          {actions.map((action) => {
            const isRollback = (action.action || '').toLowerCase().includes('rollback')
            const isFreeze = (action.action || '').toLowerCase().includes('freeze')
            const actionTone = isRollback ? 'rose' : isFreeze ? 'amber' : 'slate'
            return (
              <article key={action.id} className="flex items-start justify-between gap-4 rounded-lg border border-slate-100 bg-slate-50 px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className={`font-medium ${actionTone === 'rose' ? 'text-rose-700 dark:text-rose-300' : actionTone === 'amber' ? 'text-amber-700 dark:text-amber-300' : 'text-slate-900 dark:text-slate-50'}`}>
                      {action.action}
                    </p>
                    {isRollback || isFreeze ? (
                      <span className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider text-slate-600 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-300">
                        {action.triggeredBy || 'System policy'}
                      </span>
                    ) : null}
                  </div>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{action.reason}</p>
                  {(isRollback || isFreeze) && action.modelVersion ? (
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Target version: {action.modelVersion}</p>
                  ) : null}
                </div>
                <div className="text-right text-sm text-slate-500 dark:text-slate-400">
                  <p>{formatDateTime(action.timestamp)}</p>
                  <p className={`mt-1 font-semibold ${action.severity === 'Alert' ? 'text-rose-700 dark:text-rose-300' : action.severity === 'Watch' ? 'text-amber-700 dark:text-amber-300' : 'text-slate-600 dark:text-slate-400'}`}>
                    {action.severity}
                  </p>
                </div>
              </article>
            )
          })}
        </div>
      </section>
    </div>
  )
}

function buildHealthScore(transactions, driftMetrics, fairnessPercent = 0, explainabilityLoss = 0) {
  if (!transactions.length || !driftMetrics) {
    return 70
  }

  const confidenceScore = transactions.reduce((sum, transaction) => sum + transaction.confidence, 0) / transactions.length
  const flaggedShare = transactions.filter((transaction) => ['Pending', 'Escalated'].includes(transaction.status)).length / transactions.length
  const latestDrift = Math.max(
    ...(Object.values(driftMetrics.statisticalDrift).map((values) => values.at(-1) ?? 0)),
    driftMetrics.semanticDrift.at(-1)?.distance ?? 0,
  )
  const fairnessPenalty = Math.max(0, (100 - fairnessPercent) / 100)
  const fairnessRisk = Math.min(1, fairnessPenalty + flaggedShare * 0.35)
  const explainabilityRisk = Math.min(1, explainabilityLoss / 100)
  const score =
    confidenceScore * 100 * 0.4 +
    (1 - latestDrift) * 100 * 0.2 +
    (1 - fairnessRisk) * 100 * 0.2 +
    (1 - explainabilityRisk) * 100 * 0.2

  return Math.max(0, Math.min(100, Math.round(score)))
}

function buildDashboardMetrics(transactions, driftMetrics, selectedFeature) {
  if (!transactions.length || !driftMetrics) {
    return {
      transactionsToday: 0,
      flaggedForReview: 0,
      averageConfidencePercent: 0,
      fairnessPercent: 0,
      fairnessTone: 'amber',
      driftStatusLabel: 'Normal',
      driftStatusTone: 'success',
      latestDriftValue: 0,
      confidence: 0,
      drift: 0,
      fairness: 0,
      explainabilityLoss: 0,
      explainabilityLossTone: 'violet',
      confidenceTone: 'emerald',
      healthScore: 70,
      healthSummary: 'The model is warming up and waiting for the first live measurements.',
    }
  }

  const transactionsToday = transactions.length
  const flaggedForReview = transactions.filter((transaction) => ['Pending', 'Escalated'].includes(transaction.status)).length
  const averageConfidence = transactions.reduce((sum, transaction) => sum + transaction.confidence, 0) / Math.max(1, transactions.length)
  const latestDriftValue = driftMetrics.statisticalDrift[selectedFeature].at(-1) ?? 0
  const fairnessPercent = Math.max(0, Math.round(100 - (flaggedForReview / Math.max(1, transactionsToday)) * 120))
  const fairnessTone = fairnessPercent < 45 ? 'rose' : fairnessPercent < 60 ? 'amber' : 'slate'
  const driftStatus = getDriftStatus(latestDriftValue)
  const driftStatusTone = driftStatus.tone
  const confidencePercent = Math.round(averageConfidence * 100)

  const shapCoverage = transactions.filter((t) => (t.shapValues?.length ?? 0) > 0).length
  const explainabilityLoss = Math.round(100 - (transactionsToday ? (shapCoverage / transactionsToday) * 100 : 0))
  const explainabilityLossTone = explainabilityLoss > 40 ? 'rose' : explainabilityLoss > 20 ? 'amber' : 'violet'

  const healthScore = buildHealthScore(transactions, driftMetrics, fairnessPercent, explainabilityLoss)
  const healthSummary = buildHealthSummary(transactions, driftMetrics, selectedFeature, fairnessPercent)

  return {
    transactionsToday,
    flaggedForReview,
    averageConfidencePercent: confidencePercent,
    fairnessPercent,
    fairnessTone,
    driftStatusLabel: driftStatus.label,
    driftStatusTone,
    latestDriftValue,
    confidence: confidencePercent,
    drift: Math.round(latestDriftValue * 100),
    fairness: fairnessPercent,
    explainabilityLoss,
    explainabilityLossTone,
    confidenceTone: confidencePercent < 60 ? 'amber' : 'emerald',
    healthScore,
    healthSummary,
  }
}

function buildHealthSummary(transactions, driftMetrics, selectedFeature, fairnessPercent = 0) {
  if (!transactions.length || !driftMetrics) {
    return 'The model is warming up and waiting for the first live measurements.'
  }

  const latestDrift = driftMetrics.statisticalDrift[selectedFeature].at(-1) ?? 0
  const recentConfidence = transactions.reduce((sum, transaction) => sum + transaction.confidence, 0) / transactions.length
  const flaggedCount = transactions.filter((transaction) => ['Pending', 'Escalated'].includes(transaction.status)).length

  if (fairnessPercent < 60) {
    return `Watch: fairness is down to ${fairnessPercent}%, so governance should treat this as a priority risk even if the other signals look stable.`
  }

  if (latestDrift >= 0.2) {
    return `Watch: ${driftFeatureOptions.find((option) => option.value === selectedFeature)?.label.toLowerCase() ?? 'the selected feature'} is drifting higher than usual. ${flaggedCount} transactions are already pending review.`
  }

  if (recentConfidence < 0.7) {
    return 'The model is healthy, but confidence is softening slightly and should be watched over the next few polls.'
  }

  return 'The model is healthy. Confidence is steady and no significant drift was detected in the last 24 hours.'
}

function SkeletonOverview() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="h-28 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950" />
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-2">
        <div className="h-96 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950" />
        <div className="h-96 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950" />
      </div>
      <div className="h-96 rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950" />
    </div>
  )
}