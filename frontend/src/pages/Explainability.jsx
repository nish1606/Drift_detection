import { useEffect, useMemo, useState } from 'react'
import { getTransactions } from '../api'

function BarChart({ data, height = 220, color = '#10b981' }) {
  const max = Math.max(...data.map((d) => Math.abs(d.value)), 1)
  return (
    <div className="flex items-end gap-2" style={{ height }}>
      {data.map((item, idx) => {
        const h = Math.max(4, (Math.abs(item.value) / max) * height)
        return (
          <div key={idx} className="flex flex-1 flex-col items-center gap-2">
            <div className="relative w-full rounded-t-md bg-slate-200 dark:bg-slate-800" style={{ height }}>
              <div
                className="absolute bottom-0 w-full rounded-t-md transition-all"
                style={{ height: h, backgroundColor: color }}
              />
            </div>
            <span className="truncate text-[11px] leading-none text-slate-500 dark:text-slate-400">{item.feature}</span>
          </div>
        )
      })}
    </div>
  )
}

function LimeChart({ data, height = 220 }) {
  const max = Math.max(...data.map((d) => Math.abs(d.value)), 1)
  return (
    <div className="flex items-end gap-2" style={{ height }}>
      {data.map((item, idx) => {
        const h = Math.max(4, (Math.abs(item.value) / max) * height)
        const color = item.value >= 0 ? '#10b981' : '#ef4444'
        return (
          <div key={idx} className="flex flex-1 flex-col items-center gap-2">
            <div className="relative w-full rounded-t-md bg-slate-200 dark:bg-slate-800" style={{ height }}>
              <div
                className="absolute bottom-0 w-full rounded-t-md transition-all"
                style={{ height: h, backgroundColor: color }}
              />
            </div>
            <span className="truncate text-[11px] leading-none text-slate-500 dark:text-slate-400">{item.feature}</span>
          </div>
        )
      })}
    </div>
  )
}

export default function Explainability({ role }) {
  const [transactions, setTransactions] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    setLoading(true)
    getTransactions(role)
      .then((rows) => {
        if (!active) return
        setTransactions(rows)
        setSelectedId((prev) => prev || (rows[0]?.id ?? null))
      })
      .catch(() => setLoading(false))
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [role])

  const selected = useMemo(
    () => transactions.find((t) => t.id === selectedId) || null,
    [selectedId, transactions]
  )

  const globalImportance = useMemo(() => {
    if (!transactions.length) return []
    const map = new Map()
    transactions.forEach((t) => {
      (t.shapValues || []).forEach((s) => {
        map.set(s.feature, (map.get(s.feature) || 0) + Math.abs(s.value))
      })
    })
    return Array.from(map.entries())
      .map(([feature, value]) => ({ feature, value: Number(value.toFixed(4)) }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 12)
  }, [transactions])

  const localShap = useMemo(() => selected?.shapValues?.slice(0, 10) || [], [selected])
  const localLime = useMemo(() => {
    if (!localShap.length) return []
    return localShap.map((s) => ({
      feature: s.feature,
      value: Number(s.value.toFixed(4)),
    }))
  }, [localShap])

  if (loading) {
    return <div className="p-6 text-sm text-slate-500 dark:text-slate-400">Loading explainability data...</div>
  }

  return (
    <div className="space-y-4">
      <section className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-slate-50">Model explainability</h2>
            <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Global and local feature attribution for model decisions.</p>
          </div>
          <label className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
            Transaction / decision
            <select
              value={selectedId || ''}
              onChange={(event) => setSelectedId(event.target.value)}
              className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
            >
              {transactions.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.id}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">SHAP Auditor</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Global feature importance across recent decisions.</p>
            </div>
            <span className="rounded-full border border-emerald-200 bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300">
              Global
            </span>
          </div>
          <div className="mt-4">
            <BarChart data={globalImportance} color="#10b981" />
          </div>
          <div className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            {globalImportance.slice(0, 5).map((item) => (
              <div key={item.feature} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-900">
                <span className="font-medium text-slate-700 dark:text-slate-200">{item.feature}</span>
                <span className="font-semibold text-slate-900 dark:text-slate-50">{item.value.toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">LIME Analyzer</h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">Local interpretable explanation for the selected decision.</p>
            </div>
            <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2 py-1 text-xs font-semibold text-indigo-700 dark:border-indigo-900 dark:bg-indigo-950/50 dark:text-indigo-300">
              Local
            </span>
          </div>
          <div className="mt-4">
            {selected ? (
              <LimeChart data={localLime} />
            ) : (
              <p className="text-sm text-slate-500 dark:text-slate-400">Select a transaction to view local explanations.</p>
            )}
          </div>
          <div className="mt-4 space-y-2 text-sm text-slate-600 dark:text-slate-300">
            {localLime.slice(0, 5).map((item) => (
              <div key={item.feature} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-900">
                <span className="font-medium text-slate-700 dark:text-slate-200">{item.feature}</span>
                <span className={`font-semibold ${item.value >= 0 ? 'text-emerald-700 dark:text-emerald-300' : 'text-rose-700 dark:text-rose-300'}`}>
                  {item.value.toFixed(4)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Selected decision context</h3>
        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Jumped from Review Queue — {selected ? selected.id : 'none selected'}</p>
        {selected ? (
          <div className="mt-3 grid gap-3 md:grid-cols-3">
            <div className="rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-900">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Confidence</p>
              <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-50">{((selected.confidence || 0) * 100).toFixed(0)}%</p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-900">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Status</p>
              <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-50">{selected.status || selected.decision || 'N/A'}</p>
            </div>
            <div className="rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-900">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Top factor</p>
              <p className="mt-1 text-lg font-semibold text-slate-900 dark:text-slate-50">{selected.topFactor || 'N/A'}</p>
            </div>
          </div>
        ) : null}
      </section>
    </div>
  )
}
