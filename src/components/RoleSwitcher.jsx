import { ROLES } from '../appConfig'

export default function RoleSwitcher({ role, onChange }) {
  return (
    <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-1 dark:border-slate-800 dark:bg-slate-900">
      {ROLES.map((candidate) => {
        const active = candidate === role

        return (
          <button
            key={candidate}
            type="button"
            onClick={() => onChange(candidate)}
            className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
              active ? 'bg-slate-900 text-white dark:bg-slate-100 dark:text-slate-900' : 'text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800'
            }`}
          >
            {candidate}
          </button>
        )
      })}
    </div>
  )
}