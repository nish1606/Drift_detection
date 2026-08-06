import { useEffect, useMemo, useRef, useState } from 'react'
import ShapBarChart from '../components/ShapBarChart'
import TransactionRow from '../components/TransactionRow'
import TooltipTerm from '../components/TooltipTerm'
import { getTransactions, updateTransactionStatus } from '../api'
import { formatCurrency, formatDateTime, formatPercent } from '../utils/formatters'

const statusOptions = ['All', 'Pending', 'Approved', 'Declined', 'Escalated']
const dateOptions = [
  { value: '24h', label: 'Last 24h' },
  { value: '7d', label: 'Last 7 days' },
  { value: '30d', label: 'Last 30 days' },
]

function matchesDateRange(timestamp, range) {
  const age = Date.now() - new Date(timestamp).getTime()
  const thresholds = {
    '24h': 24 * 60 * 60 * 1000,
    '7d': 7 * 24 * 60 * 60 * 1000,
    '30d': 30 * 24 * 60 * 60 * 1000,
  }

  return age <= thresholds[range]
}

export default function ReviewQueue({ role }) {
  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedTransaction, setSelectedTransaction] = useState(null)
  const [newlyAddedIds, setNewlyAddedIds] = useState([])
  const [showExplanation, setShowExplanation] = useState(false)
  const [dateRange, setDateRange] = useState('7d')
  const [statusFilter, setStatusFilter] = useState('All')
  const [minimumConfidence, setMinimumConfidence] = useState(0.5)
  const [savingStatus, setSavingStatus] = useState(false)
  const [confirmation, setConfirmation] = useState('')
  const previousIdsRef = useRef([])

  useEffect(() => {
    let active = true

    const load = async () => {
      setLoading(true)
      const nextTransactions = await getTransactions()

      if (!active) {
        return
      }

      const previousIds = previousIdsRef.current
      const nextIds = nextTransactions.map((transaction) => transaction.id)
      const arrivingIds = nextIds.filter((id) => !previousIds.includes(id))

      if (arrivingIds.length) {
        setNewlyAddedIds(arrivingIds)
        window.setTimeout(() => setNewlyAddedIds((current) => current.filter((id) => !arrivingIds.includes(id))), 2200)
      }

      previousIdsRef.current = nextIds

      setTransactions(nextTransactions)
      setLoading(false)
    }

    load()
    const timer = window.setInterval(load, 15000)

    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [])

  const filteredTransactions = useMemo(() => {
    return transactions.filter((transaction) => {
      const statusMatch = statusFilter === 'All' || transaction.status === statusFilter
      const confidenceMatch = transaction.confidence >= minimumConfidence
      const dateMatch = matchesDateRange(transaction.timestamp, dateRange)

      return statusMatch && confidenceMatch && dateMatch
    })
  }, [dateRange, minimumConfidence, statusFilter, transactions])

  async function handleStatusUpdate(status) {
    if (!selectedTransaction) {
      return
    }

    setSavingStatus(true)
    const updated = await updateTransactionStatus(selectedTransaction.id, status, role)
    setTransactions((current) => current.map((transaction) => (transaction.id === updated.id ? updated : transaction)))
    setSelectedTransaction(updated)
    setSavingStatus(false)
    setConfirmation(`${status} logged for ${updated.id} by ${role} at ${formatDateTime(new Date().toISOString())}`)
  }

  if (loading && !transactions.length) {
    return <QueueSkeleton />
  }

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
        <div className="grid gap-3 lg:grid-cols-3">
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
            Status
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
              {statusOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
            Minimum confidence: {formatPercent(minimumConfidence, 0)}
            <input type="range" min="0.4" max="0.98" step="0.01" value={minimumConfidence} onChange={(event) => setMinimumConfidence(Number(event.target.value))} className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-slate-900 dark:bg-slate-800" />
          </label>
        </div>
      </section>

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-800">
          <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">Flagged transactions</h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Click any row to inspect model features and decide the next action.</p>
        </div>

        {filteredTransactions.length ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-100 dark:divide-slate-800">
              <thead className="bg-slate-50 text-left text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:bg-slate-900 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Amount</th>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">
                    <TooltipTerm label="Confidence" tip="The model’s risk score for this transaction, expressed as a percentage." />
                  </th>
                  <th className="px-4 py-3">
                    <TooltipTerm label="Top SHAP factor" tip="The single feature that most influenced the model’s decision for this row." />
                  </th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredTransactions.map((transaction) => (
                  <TransactionRow key={transaction.id} transaction={transaction} onSelect={setSelectedTransaction} isNew={newlyAddedIds.includes(transaction.id)} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState title="No transactions match the current filters." description="Broaden the date range or lower the confidence threshold to see more rows." />
        )}
      </section>

      {selectedTransaction ? (
        <div className="fixed inset-0 z-30 flex justify-end bg-slate-950/30">
          <button type="button" aria-label="Close detail panel" className="absolute inset-0 cursor-default" onClick={() => setSelectedTransaction(null)} />
          <aside className="relative z-10 h-full w-full max-w-3xl overflow-y-auto border-l border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Transaction detail</p>
                <h3 className="mt-1 text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">{selectedTransaction.id}</h3>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{selectedTransaction.reason}</p>
              </div>
              <button type="button" onClick={() => setSelectedTransaction(null)} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-medium text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
                Close
              </button>
            </div>

            <div className="mt-5 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
              <section className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
                <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Feature snapshot</h4>
                <dl className="mt-3 grid gap-2 text-sm">
                  {Object.entries(selectedTransaction.features).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between gap-4 rounded-lg bg-white px-3 py-2 dark:bg-slate-950">
                      <dt className="font-medium text-slate-500 dark:text-slate-400">{key}</dt>
                      <dd className="text-right text-slate-800 dark:text-slate-200">{String(value)}</dd>
                    </div>
                  ))}
                  <div className="flex items-center justify-between gap-4 rounded-lg bg-white px-3 py-2 dark:bg-slate-950">
                    <dt className="font-medium text-slate-500 dark:text-slate-400">Amount</dt>
                    <dd className="text-right text-slate-800 dark:text-slate-200">{formatCurrency(selectedTransaction.amount)}</dd>
                  </div>
                </dl>
              </section>

              <section className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
                <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Model context</h4>
                <div className="mt-3 grid gap-2 text-sm">
                  <div className="flex justify-between rounded-lg bg-white px-3 py-2 dark:bg-slate-950">
                    <span className="text-slate-500 dark:text-slate-400">Version</span>
                    <span className="font-medium text-slate-800 dark:text-slate-200">{selectedTransaction.modelVersion}</span>
                  </div>
                  <div className="flex justify-between rounded-lg bg-white px-3 py-2 dark:bg-slate-950">
                    <span className="text-slate-500 dark:text-slate-400">Confidence</span>
                    <span className="font-medium text-slate-800 dark:text-slate-200">{formatPercent(selectedTransaction.confidence, 0)}</span>
                  </div>
                  <div className="flex justify-between rounded-lg bg-white px-3 py-2 dark:bg-slate-950">
                    <span className="text-slate-500 dark:text-slate-400">Status</span>
                    <span className="font-medium text-slate-800 dark:text-slate-200">{selectedTransaction.status}</span>
                  </div>
                  <div className="flex justify-between rounded-lg bg-white px-3 py-2 dark:bg-slate-950">
                    <span className="text-slate-500 dark:text-slate-400">Top factor</span>
                    <span className="font-medium text-slate-800 dark:text-slate-200">{selectedTransaction.topFactor}</span>
                  </div>
                </div>
              </section>
            </div>

            <div className="mt-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h4 className="text-sm font-semibold text-slate-900 dark:text-slate-50">
                  Top 5 <TooltipTerm label="SHAP" tip="Feature attribution values showing which inputs pushed the model toward a risky or safe prediction." /> contributions
                </h4>
                <button type="button" onClick={() => setShowExplanation((current) => !current)} className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
                  {showExplanation ? 'Show SHAP chart' : 'Explain like I’m new here'}
                </button>
              </div>

              <div className="mt-3 grid gap-4 lg:grid-cols-[1fr_0.9fr]">
                {showExplanation ? (
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
                    <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">Plain-language explanation</p>
                    <p className="mt-3 text-sm leading-6 text-slate-700 dark:text-slate-200">{buildExplanation(selectedTransaction)}</p>
                    <p className="mt-4 text-xs text-slate-500 dark:text-slate-400">This same ranking can be switched back to the bar chart at any time.</p>
                  </div>
                ) : (
                  <ShapBarChart values={[...selectedTransaction.shapValues].sort((left, right) => Math.abs(right.value) - Math.abs(left.value)).slice(0, 5)} />
                )}
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">{showExplanation ? 'Technical view' : 'Plain-language view'}</p>
                  <p className="mt-3 text-sm leading-6 text-slate-700 dark:text-slate-200">
                    {showExplanation ? 'Switch back to the chart to inspect the exact feature contributions and sign of impact.' : buildExplanation(selectedTransaction)}
                  </p>
                </div>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap gap-3">
              <button type="button" disabled={savingStatus} onClick={() => handleStatusUpdate('Approved')} className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60">
                Approve
              </button>
              <button type="button" disabled={savingStatus} onClick={() => handleStatusUpdate('Declined')} className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60">
                Decline
              </button>
              <button type="button" disabled={savingStatus} onClick={() => handleStatusUpdate('Escalated')} className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-60">
                Escalate to compliance
              </button>
            </div>

            {confirmation ? <p className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{confirmation}</p> : null}
          </aside>
        </div>
      ) : null}
    </div>
  )
}

function EmptyState({ title, description }) {
  return (
    <div className="px-4 py-12 text-center">
      <p className="text-base font-semibold text-slate-900">{title}</p>
      <p className="mt-1 text-sm text-slate-600">{description}</p>
    </div>
  )
}

function QueueSkeleton() {
  return (
    <div className="space-y-4 animate-pulse">
      <div className="h-28 rounded-xl border border-slate-200 bg-white" />
      <div className="h-[32rem] rounded-xl border border-slate-200 bg-white" />
    </div>
  )
}

function buildExplanation(transaction) {
  const topFeatures = [...transaction.shapValues].sort((left, right) => Math.abs(right.value) - Math.abs(left.value)).slice(0, 3)
  const phrases = topFeatures.map((item) => featureToPhrase(item.feature))
  const lead = phrases[0] ?? 'the transaction pattern looked unusual'
  const second = phrases[1] ? `, combined with ${phrases[1]}` : ''
  const third = phrases[2] ? ` and some additional pressure from ${phrases[2]}` : ''

  return `This transaction was flagged mainly because ${lead}${second}${third}. In plain English, the model saw a mix of unfamiliar device behavior, a higher-than-usual amount, and location signals that together looked more like fraud than a normal purchase.`
}

function featureToPhrase(feature) {
  const map = {
    deviceVelocity: 'a device we have not seen move this quickly before',
    transactionAmount: 'an amount that is higher than what this account usually spends',
    geoDistance: 'a location pattern that does not match the account’s normal travel pattern',
    accountAgeDays: 'an account that is still relatively new',
    ipRiskScore: 'an IP address pattern that carries extra risk',
  }

  return map[feature] ?? 'another unusual risk signal'
}