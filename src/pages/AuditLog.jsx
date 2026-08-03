import { useEffect, useMemo, useState } from 'react'
import { getAuditLog } from '../mockApi'
import { createCsv, formatDateTime, formatPercent } from '../utils/formatters'

const dateOptions = [
  { value: '24h', label: 'Last 24h' },
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
]

const actionOptions = ['All', 'Approve', 'Decline', 'Escalate to compliance', 'Alert fired', 'Retrain recommended', 'Freeze triggered', 'Policy published']

function matchesDateRange(timestamp, range) {
  const age = Date.now() - new Date(timestamp).getTime()
  const thresholds = {
    '24h': 24 * 60 * 60 * 1000,
    '7d': 7 * 24 * 60 * 60 * 1000,
    '30d': 30 * 24 * 60 * 60 * 1000,
  }

  return age <= thresholds[range]
}

export default function AuditLog() {
  const [entries, setEntries] = useState([])
  const [loading, setLoading] = useState(true)
  const [query, setQuery] = useState('')
  const [dateRange, setDateRange] = useState('30d')
  const [modelVersion, setModelVersion] = useState('All')
  const [actionType, setActionType] = useState('All')
  const [exportStatus, setExportStatus] = useState('')

  useEffect(() => {
    let active = true

    const load = async () => {
      setLoading(true)
      const nextEntries = await getAuditLog()

      if (!active) {
        return
      }

      setEntries(nextEntries)
      setLoading(false)
    }

    load()

    return () => {
      active = false
    }
  }, [])

  const versionOptions = useMemo(() => ['All', ...new Set(entries.map((entry) => entry.modelVersion))], [entries])

  const filteredEntries = useMemo(() => {
    return entries.filter((entry) => {
      const queryMatch = [entry.decisionId, entry.transactionId, entry.governanceAction, entry.approver, entry.reason]
        .join(' ')
        .toLowerCase()
        .includes(query.toLowerCase())
      const dateMatch = matchesDateRange(entry.timestamp, dateRange)
      const versionMatch = modelVersion === 'All' || entry.modelVersion === modelVersion
      const actionMatch = actionType === 'All' || entry.governanceAction === actionType

      return queryMatch && dateMatch && versionMatch && actionMatch
    })
  }, [actionType, dateRange, entries, modelVersion, query])

  function exportCsv() {
    const csv = createCsv(filteredEntries, [
      { label: 'Decision ID', getValue: (entry) => entry.decisionId },
      { label: 'Timestamp', getValue: (entry) => entry.timestamp },
      { label: 'Model version', getValue: (entry) => entry.modelVersion },
      { label: 'Prediction', getValue: (entry) => entry.prediction },
      { label: 'Confidence', getValue: (entry) => formatPercent(entry.confidence, 0) },
      { label: 'Governance action', getValue: (entry) => entry.governanceAction },
      { label: 'Approver', getValue: (entry) => entry.approver },
    ])

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = window.URL.createObjectURL(blob)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = 'audit-log.csv'
    anchor.click()
    window.URL.revokeObjectURL(url)
    setExportStatus(`Exported ${filteredEntries.length} rows to CSV.`)
  }

  if (loading) {
    return <div className="h-80 animate-pulse rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950" />
  }

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
        <div className="grid gap-3 xl:grid-cols-5">
          <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200 xl:col-span-2">
            Search
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Decision ID, approver, action, reason" className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200" />
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
            Date range
            <select value={dateRange} onChange={(event) => setDateRange(event.target.value)} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
              {dateOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
            Model version
            <select value={modelVersion} onChange={(event) => setModelVersion(event.target.value)} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
              {versionOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
            Action type
            <select value={actionType} onChange={(event) => setActionType(event.target.value)} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
              {actionOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm text-slate-600">Compliance reporting log with search and export support.</p>
          <button type="button" onClick={exportCsv} className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white">
            Export
          </button>
        </div>
        {exportStatus ? <p className="mt-3 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{exportStatus}</p> : null}
      </section>

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        {filteredEntries.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 text-sm dark:divide-slate-800">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">Decision ID</th>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Model version</th>
                  <th className="px-4 py-3">Prediction</th>
                  <th className="px-4 py-3">Confidence</th>
                  <th className="px-4 py-3">Governance action</th>
                  <th className="px-4 py-3">Approver</th>
                </tr>
              </thead>
              <tbody>
                {filteredEntries.map((entry) => (
                  <tr key={entry.decisionId} className="border-b border-slate-100">
                    <td className="px-4 py-3 font-medium text-slate-900">{entry.decisionId}</td>
                    <td className="px-4 py-3 text-slate-600">{formatDateTime(entry.timestamp)}</td>
                    <td className="px-4 py-3 text-slate-700">{entry.modelVersion}</td>
                    <td className="px-4 py-3 text-slate-700">{entry.prediction}</td>
                    <td className="px-4 py-3 text-slate-700">{formatPercent(entry.confidence, 0)}</td>
                    <td className="px-4 py-3 text-slate-700">{entry.governanceAction}</td>
                    <td className="px-4 py-3 text-slate-600">{entry.approver}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState />
        )}
      </section>
    </div>
  )
}

function EmptyState() {
  return (
    <div className="px-4 py-12 text-center">
      <p className="text-base font-semibold text-slate-900">No audit entries match the current filters.</p>
      <p className="mt-1 text-sm text-slate-600">Adjust the search or date range to broaden the result set.</p>
    </div>
  )
}