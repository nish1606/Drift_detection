import { IconChevronRight, IconLayoutDashboard } from '@tabler/icons-react'

export default function PageHeader({ title, description, breadcrumbs = [], icon: Icon = IconLayoutDashboard, action }) {
  return (
    <section className="mb-5 flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950 lg:flex-row lg:items-end lg:justify-between">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">
          {breadcrumbs.map((crumb, index) => (
            <span key={`${crumb}-${index}`} className="inline-flex items-center gap-2">
              {index > 0 ? <IconChevronRight size={12} /> : null}
              <span>{crumb}</span>
            </span>
          ))}
        </div>
        <div className="mt-3 flex items-center gap-3">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
            <Icon size={20} />
          </span>
          <div className="min-w-0">
            <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">{title}</h1>
            {description ? <p className="mt-1 max-w-3xl text-sm leading-6 text-slate-600 dark:text-slate-300">{description}</p> : null}
          </div>
        </div>
      </div>
      {action ? <div>{action}</div> : null}
    </section>
  )
}
