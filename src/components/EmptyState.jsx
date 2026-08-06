import { IconInboxOff } from '@tabler/icons-react'

export default function EmptyState({ title, description, actionLabel, onAction }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-slate-200 bg-white px-6 py-14 text-center dark:border-slate-800 dark:bg-slate-950">
      <span className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500 dark:bg-slate-900 dark:text-slate-400">
        <IconInboxOff size={22} />
      </span>
      <div className="max-w-md">
        <p className="text-base font-semibold text-slate-900 dark:text-slate-50">{title}</p>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{description}</p>
      </div>
      {actionLabel ? (
        <button type="button" onClick={onAction} className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-2 text-sm font-semibold text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200">
          {actionLabel}
        </button>
      ) : null}
    </div>
  )
}
