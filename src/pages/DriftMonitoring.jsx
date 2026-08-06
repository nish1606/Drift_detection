import { useEffect, useMemo, useState } from 'react'
import DriftChart from '../components/DriftChart'
import DistributionCompare from '../components/DistributionCompare'
import TooltipTerm from '../components/TooltipTerm'
import WhatIfSimulator from '../components/WhatIfSimulator'
import { getDriftMetrics } from '../mockApi'
import { formatDateTime } from '../utils/formatters'

const featureOptions = [
  { value: 'transactionAmount', label: 'Transaction amount' },
  { value: 'deviceVelocity', label: 'Device velocity' },
  { value: 'geoDistance', label: 'Geo distance' },
]

export default function DriftMonitoring({ role }) {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedFeature, setSelectedFeature] = useState('deviceVelocity')
  const [comparisonMix, setComparisonMix] = useState(58)
  const [comparisonSplit, setComparisonSplit] = useState(60)

  useEffect(() => {
    let active = true

    const load = async () => {
      setLoading(true)
      const nextMetrics = await getDriftMetrics()

      if (!active) {
        return
      }

      setMetrics(nextMetrics)
      setLoading(false)
    }

    load()
    const timer = window.setInterval(load, 12000)

    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [])

  const statisticalData = useMemo(() => {
    if (!metrics) {
      return null
    }

    return {
      labels: metrics.timeLabels.map((value) => formatDateTime(value)),
      datasets: [
        {
          label: featureOptions.find((option) => option.value === selectedFeature)?.label ?? 'PSI',
          data: metrics.statisticalDrift[selectedFeature],
          borderColor: '#0f172a',
          backgroundColor: 'rgba(15, 23, 42, 0.08)',
        },
        {
          label: 'Threshold 0.2',
          data: metrics.timeLabels.map(() => 0.2),
          borderColor: '#dc2626',
          borderDash: [6, 4],
          pointRadius: 0,
          backgroundColor: 'transparent',
        },
      ],
    }
  }, [metrics, selectedFeature])

  const semanticData = useMemo(() => {
    if (!metrics) {
      return null
    }

    return {
      labels: metrics.timeLabels.map((value) => formatDateTime(value)),
      datasets: [
        {
          label: 'Embedding distance',
          data: metrics.semanticDrift.map((point) => point.distance),
          borderColor: '#2563eb',
          backgroundColor: 'rgba(37, 99, 235, 0.1)',
        },
      ],
    }
  }, [metrics])

  const comparisonBins = metrics?.driftDistributions?.[selectedFeature] ?? []

  if (loading && !metrics) {
    return <div className="h-80 animate-pulse rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950" />
  }

  return (
    <div className="space-y-4">
      <section className="grid gap-4 xl:grid-cols-3">
        {statisticalData ? (
          <DriftChart
            title="Statistical drift"
            subtitle={<span><TooltipTerm label="PSI" tip="Population Stability Index, a simple measure of whether the current data distribution differs from the baseline." /> and KL-style signal for the selected feature</span>}
            labels={statisticalData.labels}
            datasets={statisticalData.datasets}
            selector={{ value: selectedFeature, options: featureOptions }}
            onSelectorChange={setSelectedFeature}
            options={{
              scales: {
                y: { min: 0, max: 0.3 },
              },
            }}
          />
        ) : null}

        <section className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950 xl:col-span-1">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h3 className="text-base font-semibold text-slate-900">Concept drift</h3>
              <p className="mt-1 text-sm text-slate-600"><TooltipTerm label="ADWIN" tip="An adaptive window detector that flags when the underlying data pattern has changed over time." /> events with severity markers</p>
            </div>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
              Timeline
            </span>
          </div>

          <div className="mt-4 space-y-4">
            {metrics.conceptDriftEvents.map((event, index) => (
              <article key={`${event.timestamp}-${index}`} className="relative pl-6">
                <span className={`absolute left-0 top-1.5 h-3 w-3 rounded-full ${severityColor[event.severity]}`} />
                <div className="rounded-lg border border-slate-100 bg-slate-50 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
                    <p className="font-semibold text-slate-900">{event.feature}</p>
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${severityBadge[event.severity]}`}>{event.severity}</span>
                  </div>
                  <p className="mt-1 text-sm text-slate-600">{event.reason}</p>
                  <div className="mt-2 flex items-center justify-between text-xs text-slate-500">
                    <span>{formatDateTime(event.timestamp)}</span>
                    <span>{event.triggeredAction ? 'Triggered governance action' : 'Observed only'}</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </section>

        {semanticData ? (
          <DriftChart
            title="Semantic drift"
            subtitle="Embedding distance for text field monitoring"
            labels={semanticData.labels}
            datasets={semanticData.datasets}
            options={{
              scales: {
                y: { min: 0.05, max: 0.4 },
              },
            }}
          />
        ) : null}
      </section>

      {comparisonBins.length ? (
        <DistributionCompare
          title="Baseline vs current split"
          subtitle="Split one dataset into a baseline slice and a current slice to compare how the distribution has evolved."
          bins={comparisonBins}
          mix={comparisonMix}
          onMixChange={setComparisonMix}
          split={comparisonSplit}
          onSplitChange={setComparisonSplit}
        />
      ) : null}

      {role !== 'Analyst' ? <WhatIfSimulator /> : null}

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">Drift events log</h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Operational record of drift detection and governance linkages.</p>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-100 text-sm dark:divide-slate-800">
            <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:bg-slate-900 dark:text-slate-400">
              <tr>
                <th className="px-4 py-3">Timestamp</th>
                <th className="px-4 py-3">Drift type</th>
                <th className="px-4 py-3">Severity</th>
                <th className="px-4 py-3">Affected feature</th>
                <th className="px-4 py-3">Governance action</th>
              </tr>
            </thead>
            <tbody>
              {metrics.conceptDriftEvents.map((event, index) => (
                <tr key={`log-${index}`} className="border-b border-slate-100">
                    <td className="px-4 py-3 text-slate-600">{formatDateTime(event.timestamp)}</td>
                    <td className="px-4 py-3 text-slate-700"><TooltipTerm label={event.driftType} tip="The detector family that emitted the drift event." /></td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${severityBadge[event.severity]}`}>{event.severity}</span>
                  </td>
                  <td className="px-4 py-3 text-slate-700">{event.feature}</td>
                  <td className="px-4 py-3 text-slate-600">{event.triggeredAction ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

const severityColor = {
  Low: 'bg-emerald-500',
  Medium: 'bg-amber-500',
  High: 'bg-rose-500',
}

const severityBadge = {
  Low: 'bg-emerald-50 text-emerald-700',
  Medium: 'bg-amber-50 text-amber-700',
  High: 'bg-rose-50 text-rose-700',
}