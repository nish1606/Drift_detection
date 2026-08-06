import { IconTimeline } from '@tabler/icons-react'

export default function ModelVersionTimeline({ steps }) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-center gap-2">
        <IconTimeline size={18} className="text-slate-500" />
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-50">Model version timeline</h3>
      </div>
      <div className="mt-4 flex flex-wrap items-stretch gap-2">
        {steps.map((step) => (
          <div
            key={step.version}
            title={`${step.version} deployed ${new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(step.deployedAt))} by ${step.deployedBy}`}
            className={`min-w-[9rem] flex-1 rounded-xl border px-3 py-3 transition ${step.active ? 'border-emerald-200 bg-emerald-50 text-emerald-900 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100' : 'border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300'}`}
          >
            <p className="text-sm font-semibold">{step.version}</p>
            <p className="mt-1 text-xs text-current/70">{step.active ? 'Live' : 'Previous'}</p>
          </div>
        ))}
      </div>
    </article>
  )
}
