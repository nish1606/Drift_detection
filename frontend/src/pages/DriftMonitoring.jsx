import { useEffect, useMemo, useState } from 'react'
import DriftChart from '../components/DriftChart'
import DistributionCompare from '../components/DistributionCompare'
import TooltipTerm from '../components/TooltipTerm'
import WhatIfSimulator from '../components/WhatIfSimulator'
import LastUpdated from '../components/LastUpdated'
import { compareDatasets, getDatasets, getDriftHistory } from '../api'
import { formatDateTime } from '../utils/formatters'

const featureOptions = [
  { value: 'transactionAmount', label: 'Transaction amount' },
  { value: 'deviceVelocity', label: 'Device velocity' },
  { value: 'geoDistance', label: 'Geo distance' },
]

export default function DriftMonitoring({ role }) {
  const [metrics, setMetrics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedFeature, setSelectedFeature] = useState('transactionAmount')
  const [comparisonMix, setComparisonMix] = useState(58)
  const [comparisonSplit, setComparisonSplit] = useState(60)
  const [datasets, setDatasets] = useState([])
  const [referenceDataset, setReferenceDataset] = useState('')
  const [currentDataset, setCurrentDataset] = useState('')
  const [comparisonFeature, setComparisonFeature] = useState('Amount')
  const [comparison, setComparison] = useState(null)
  const [comparisonLoading, setComparisonLoading] = useState(false)
  const [comparisonError, setComparisonError] = useState('')

  useEffect(() => {
    let active = true

    const load = async () => {
      try {
        setLoading(true)
        const nextMetrics = await getDriftHistory(role)

        if (!active) {
          return
        }

        setMetrics(nextMetrics)
      } catch (error) {
        console.error('DriftMonitoring load failed:', error)
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

  useEffect(() => {
    getDatasets(role).then((nextDatasets) => {
      setDatasets(nextDatasets)
      if (nextDatasets.length > 1) {
        setReferenceDataset(nextDatasets.find((dataset) => dataset.name.includes('train'))?.name ?? nextDatasets[0].name)
        setCurrentDataset(nextDatasets.find((dataset) => dataset.name.includes('test'))?.name ?? nextDatasets[1].name)
      }
    }).catch((error) => setComparisonError(error.message))
  }, [role])

  useEffect(() => {
    if (!referenceDataset || !currentDataset || referenceDataset === currentDataset) return
    setComparisonLoading(true)
    setComparisonError('')
    compareDatasets({ reference: referenceDataset, current: currentDataset, feature: comparisonFeature }, role)
      .then(setComparison)
      .catch((error) => setComparisonError(error.message))
      .finally(() => setComparisonLoading(false))
  }, [comparisonFeature, currentDataset, referenceDataset, role])

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
      labels: metrics.semanticDrift.map((point) => formatDateTime(point.timestamp)),
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

  const comparisonBins = comparison?.bins ?? metrics?.driftDistributions?.[selectedFeature] ?? []

  if (loading && !metrics) {
    return <div className="h-80 animate-pulse rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950" />
  }

  return (
    <div className="space-y-4">
      <section className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-3 flex items-center justify-between">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">Drift monitoring</h2>
          <LastUpdated />
        </div>
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
                y: {
                  min: 0,
                  max: selectedFeature === 'deviceVelocity' ? 0.22 : 0.3,
                },
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
                y: { min: 0, max: 0.5 },
              },
            }}
          />
        ) : null}
      </section>

      {datasets.length > 1 ? (
        <section className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">Dataset comparison</h2>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Compare any two CSV datasets from the project data library.</p>
            </div>
            <div className="grid gap-2 sm:grid-cols-3">
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Reference
                <select value={referenceDataset} onChange={(event) => setReferenceDataset(event.target.value)} className="mt-1 block w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-normal normal-case tracking-normal text-slate-700">
                  {datasets.map((dataset) => <option key={dataset.name}>{dataset.name}</option>)}
                </select>
              </label>
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Current
                <select value={currentDataset} onChange={(event) => setCurrentDataset(event.target.value)} className="mt-1 block w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-normal normal-case tracking-normal text-slate-700">
                  {datasets.map((dataset) => <option key={dataset.name}>{dataset.name}</option>)}
                </select>
              </label>
              <label className="text-xs font-semibold uppercase tracking-wide text-slate-500">Feature
                <select value={comparisonFeature} onChange={(event) => setComparisonFeature(event.target.value)} className="mt-1 block w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-normal normal-case tracking-normal text-slate-700">
                  <option>Amount</option><option>Time</option><option>FraudLabel</option>
                </select>
              </label>
            </div>
          </div>
          {comparisonError ? <p className="mt-3 text-sm text-rose-600">{comparisonError}</p> : null}
          {comparisonLoading ? <p className="mt-4 text-sm text-slate-500">Calculating comparison...</p> : null}
          {comparison ? <p className="mt-4 text-sm text-slate-600">Drift score <strong className="text-slate-900">{comparison.driftScore}</strong> · {comparison.referenceRows.toLocaleString()} reference rows · {comparison.currentRows.toLocaleString()} current rows · means {comparison.referenceMean} vs {comparison.currentMean}</p> : null}
        </section>
      ) : null}

      {comparisonBins.length ? (
        <DistributionCompare
          title={comparison ? `${comparison.reference} vs ${comparison.current}` : 'Baseline vs current split'}
          subtitle={comparison ? `${comparisonFeature} distribution comparison` : 'Compare how the distribution has evolved.'}
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