import { formatLongDateTime } from '../utils/formatters'

export default function PolicyCard({ policy, canEdit, onEdit }) {
  return (
    <article className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50">{policy.name}</h3>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{policy.condition}</p>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
          v{policy.version}
        </span>
      </div>

      <dl className="mt-4 grid gap-2 text-sm text-slate-700 dark:text-slate-300">
        <div className="flex justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-900">
          <dt className="font-medium text-slate-500 dark:text-slate-400">Action</dt>
          <dd className="text-right">{policy.action}</dd>
        </div>
        <div className="flex justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-900">
          <dt className="font-medium text-slate-500 dark:text-slate-400">Escalation</dt>
          <dd className="text-right">{policy.escalation}</dd>
        </div>
        <div className="flex justify-between gap-3 rounded-lg bg-slate-50 px-3 py-2 dark:bg-slate-900">
          <dt className="font-medium text-slate-500 dark:text-slate-400">Last modified</dt>
          <dd className="text-right">{formatLongDateTime(policy.lastModified)}</dd>
        </div>
      </dl>

      <div className="mt-4 flex items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">{policy.modifiedBy}</p>
        <button
          type="button"
          onClick={() => onEdit(policy)}
          className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
            canEdit ? 'bg-slate-900 text-white hover:bg-slate-800 dark:bg-slate-100 dark:text-slate-900 dark:hover:bg-slate-200' : 'border border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300'
          }`}
        >
          {canEdit ? 'Edit' : 'View'}
        </button>
      </div>
    </article>
  )
}