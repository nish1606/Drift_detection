import { useMemo, useState } from 'react'
import { IconArrowRight, IconSearch } from '@tabler/icons-react'

export default function CommandPalette({ open, onClose, onRunSearch, onNavigate, loading = false }) {
  const [query, setQuery] = useState('')

  const results = useMemo(() => onRunSearch?.(query) ?? [], [onRunSearch, query])

  if (!open) {
    return null
  }

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/40 px-4 py-10 backdrop-blur-sm">
      <div className="mx-auto w-full max-w-2xl overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-950">
        <div className="flex items-center gap-3 border-b border-slate-200 px-4 py-3 dark:border-slate-800">
          <IconSearch size={18} className="text-slate-400" />
          <input
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Jump to a transaction ID, policy, or screen"
            className="w-full border-0 bg-transparent text-sm text-slate-900 outline-none placeholder:text-slate-400 dark:text-slate-50"
          />
          <button type="button" onClick={onClose} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 dark:border-slate-800 dark:text-slate-300">
            Esc
          </button>
        </div>

        <div className="max-h-[22rem] overflow-y-auto p-2">
          {loading ? <div className="px-3 py-6 text-sm text-slate-500">Loading search index...</div> : null}
          {results.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => {
                onNavigate?.(item)
                onClose?.()
              }}
              className="flex w-full items-center justify-between rounded-xl px-3 py-3 text-left transition hover:bg-slate-50 dark:hover:bg-slate-900"
            >
              <div>
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-50">{item.title}</p>
                <p className="mt-1 text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">{item.kind}</p>
              </div>
              <IconArrowRight size={16} className="text-slate-400" />
            </button>
          ))}
          {!loading && !results.length ? <div className="px-3 py-6 text-sm text-slate-500">No matches yet.</div> : null}
        </div>
      </div>
    </div>
  )
}
