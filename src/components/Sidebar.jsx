import { NavLink } from 'react-router-dom'
import { NAV_ITEMS } from '../appConfig'

export default function Sidebar({ role }) {
  const visibleItems = NAV_ITEMS.filter((item) => (item.visibleRoles ?? item.roles).includes(role))

  return (
    <aside className="flex h-full flex-col border-r border-slate-200 bg-white px-4 py-5 transition-colors duration-300 dark:border-slate-800 dark:bg-slate-950">
      <div className="mb-6">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Fraud governance</p>
        <h1 className="mt-2 text-lg font-semibold tracking-tight text-slate-900 dark:text-slate-50">Autonomous decision dashboard</h1>
      </div>

      <nav className="flex flex-1 flex-col gap-1">
        {visibleItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `rounded-xl px-3 py-2 text-sm font-medium transition ${
                isActive ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-900'
              }`
            }
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
        <p className="font-semibold text-slate-900 dark:text-slate-50">Access profile</p>
        <p className="mt-1">
          {role === 'Analyst' && 'Review queue and overview only.'}
          {role === 'Risk Engineer' && 'Monitoring access with review queue and read-only policy access.'}
          {role === 'Compliance' && 'Full governance, audit, and policy control.'}
        </p>
      </div>
    </aside>
  )
}