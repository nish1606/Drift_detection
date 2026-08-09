import { useEffect, useMemo, useState } from 'react'
import { getTransactions } from '../api'
import { formatPercent } from '../utils/formatters'

const PROTECTED_ATTRIBUTES = [
  { key: 'amount', label: 'Transaction amount' },
  { key: 'deviceVelocity', label: 'Device velocity' },
  { key: 'geoDistance', label: 'Geo distance' },
]

function SegmentTable({ segments, title }) {
  if (!segments?.length) return null
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">{title}</h3>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Flagged rate and approval parity by segment.</p>
      <div className="mt-3 overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-100 text-sm dark:divide-slate-800">
          <thead>
            <tr className="text-left text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              <th className="px-3 py-2">Segment</th>
              <th className="px-3 py-2">Decisions</th>
              <th className="px-3 py-2">Flagged rate</th>
              <th className="px-3 py-2">Approval rate</th>
              <th className="px-3 py-2">Disparity</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {segments.map((row) => (
              <tr key={row.segment}>
                <td className="px-3 py-2 font-medium text-slate-900 dark:text-slate-50">{row.segment}</td>
                <td className="px-3 py-2 text-slate-700 dark:text-slate-200">{row.count}</td>
                <td className="px-3 py-2 text-slate-700 dark:text-slate-200">{formatPercent(row.flaggedRate, 1)}</td>
                <td className="px-3 py-2 text-slate-700 dark:text-slate-200">{formatPercent(1 - row.flaggedRate, 1)}</td>
                <td className="px-3 py-2">
                  <span className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-semibold ${row.disparity > 0.15 ? 'border border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-300' : 'border border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300'}`}>
                    {row.disparity > 0.15 ? 'High disparity' : 'Within tolerance'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function FairnessMonitoring({ role }) {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    getTransactions(role)
      .then((tx) => {
        if (!active) return
        setTransactions(tx)
      })
      .catch(() => setLoading(false))
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [role])

  const segmentBreakdown = useMemo(() => {
    if (!transactions.length) return []
    const result = []
    const features = [
      { key: 'amount', label: 'amount' },
      { key: 'velocity_1h', label: 'deviceVelocity' },
      { key: 'geo_distance', label: 'geoDistance' },
    ]
    features.forEach(({ key, label }) => {
      const values = transactions.map((t) => t.features?.[key] ?? t.raw_features?.[key] ?? 0)
      const sorted = [...values].sort((a, b) => a - b)
      const q1 = sorted[Math.floor(sorted.length * 0.33)] || sorted[0]
      const q2 = sorted[Math.floor(sorted.length * 0.67)] || sorted[sorted.length - 1]
      const bins = ['low', 'mid', 'high']
      const binsData = bins.map((bin) => {
        let filtered
        if (bin === 'low') filtered = transactions.filter((t) => (t.features?.[key] ?? t.raw_features?.[key] ?? 0) <= q1)
        else if (bin === 'mid') filtered = transactions.filter((t) => {
          const v = t.features?.[key] ?? t.raw_features?.[key] ?? 0
          return v > q1 && v <= q2
        })
        else filtered = transactions.filter((t) => (t.features?.[key] ?? t.raw_features?.[key] ?? 0) > q2)
        const flagged = filtered.filter((t) => ['Pending', 'Escalated'].includes(t.status)).length
        const flaggedRate = filtered.length ? flagged / filtered.length : 0
        const approvalRate = filtered.length ? 1 - flaggedRate : 0
        return {
          segment: `${bin} ${label}`,
          count: filtered.length,
          flaggedRate,
          approvalRate,
          disparity: 0,
        }
      })
      const maxRate = Math.max(...binsData.map((b) => b.flaggedRate), 0.001)
      binsData.forEach((bin) => {
        bin.disparity = maxRate > 0 ? Math.abs(bin.flaggedRate - maxRate) : 0
      })
      result.push({ feature: label, bins: binsData })
    })
    return result
  }, [transactions])

  const overallFairness = useMemo(() => {
    if (!transactions.length) return { score: 0, tone: 'slate' }
    const flagged = transactions.filter((t) => ['Pending', 'Escalated'].includes(t.status)).length
    const rate = transactions.length ? flagged / transactions.length : 0
    const score = Math.round((1 - rate) * 100)
    const tone = score < 60 ? 'rose' : score < 80 ? 'amber' : 'emerald'
    return { score, tone }
  }, [transactions])

  if (loading) {
    return <div className="p-6 text-sm text-slate-500 dark:text-slate-400">Loading fairness metrics...</div>
  }

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">Fairness monitoring</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Bias metrics broken down by protected attribute and model feature segment.</p>
          </div>
          <span className={`rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-wider ${overallFairness.tone === 'emerald' ? 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300' : overallFairness.tone === 'amber' ? 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-300' : 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-300'}`}>
            Fairness score {overallFairness.score}%
          </span>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        {segmentBreakdown.map((group) => (
          <SegmentTable key={group.feature} segments={group.bins} title={group.feature} />
        ))}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Protected attribute segments</h3>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Simulated segment parity for age, region, and channel.</p>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {PROTECTED_ATTRIBUTES.map((attr, index) => {
            const group = segmentBreakdown[index]
            const bins = group?.bins ?? []
            const avgFlagged = bins.length ? bins.reduce((sum, s) => sum + s.flaggedRate, 0) / bins.length : 0
            const tone = avgFlagged > 0.15 ? 'rose' : avgFlagged > 0.1 ? 'amber' : 'emerald'
            return (
              <div key={attr.key} className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">{attr.label}</p>
                <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-slate-50">{formatPercent(avgFlagged, 1)}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Avg flagged rate across segments</p>
                <div className="mt-3 h-2 w-full rounded-full bg-slate-200 dark:bg-slate-800">
                  <div
                    className={`h-2 rounded-full ${tone === 'emerald' ? 'bg-emerald-500' : tone === 'amber' ? 'bg-amber-500' : 'bg-rose-500'}`}
                    style={{ width: `${Math.min(100, avgFlagged * 100 * 5)}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      </section>
    </div>
  )
}
