export default function StoryTimeline({ entries }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
      <div>
        <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50">What changed today</h3>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">A readable timeline that turns drift and governance logs into a simple story.</p>
      </div>
      <div className="mt-4 space-y-3">
        {entries.map((entry) => (
          <details key={`${entry.timestamp}-${entry.title}`} className="group rounded-xl border border-slate-100 bg-slate-50 p-3 open:bg-white dark:border-slate-800 dark:bg-slate-900 dark:open:bg-slate-950">
            <summary className="cursor-pointer list-none">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-medium text-slate-900 dark:text-slate-50">{entry.title}</p>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{entry.timestamp}</p>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${entry.tone === 'Alert' ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300' : entry.tone === 'Watch' ? 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300' : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300'}`}>
                  {entry.tone}
                </span>
              </div>
            </summary>
            <p className="mt-3 text-sm leading-6 text-slate-600 dark:text-slate-300">{entry.detail}</p>
          </details>
        ))}
      </div>
    </article>
  )
}