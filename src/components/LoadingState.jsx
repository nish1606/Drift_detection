export default function LoadingState({ variant = 'card' }) {
  if (variant === 'table') {
    return (
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
        <div className="h-12 border-b border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-900" />
        <div className="animate-pulse p-4">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="mb-3 h-10 rounded-lg bg-slate-100 last:mb-0 dark:bg-slate-800" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="animate-pulse rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
      <div className="h-5 w-40 rounded bg-slate-100 dark:bg-slate-800" />
      <div className="mt-4 h-48 rounded-xl bg-slate-100 dark:bg-slate-800" />
    </div>
  )
}
