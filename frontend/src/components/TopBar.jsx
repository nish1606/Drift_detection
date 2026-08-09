import { ENVIRONMENT, MODEL_VERSION } from '../appConfig'
import RoleSwitcher from './RoleSwitcher'
import { logout as apiLogout, getRole } from '../mockApi'

function ThemeToggle({ darkMode, onDarkModeChange }) {
  return (
    <button
      type="button"
      onClick={() => onDarkModeChange?.(!darkMode)}
      className={`relative inline-flex h-9 w-16 items-center rounded-full border transition-colors duration-200 ${
        darkMode
          ? 'border-emerald-500/60 bg-slate-900'
          : 'border-slate-200 bg-slate-100'
      }`}
      aria-pressed={darkMode}
      aria-label="Toggle dark mode"
    >
      <span
        className={`inline-flex h-7 w-8 items-center justify-center rounded-full bg-white text-xs font-semibold shadow-sm transition-transform duration-200 ${
          darkMode ? 'translate-x-8 text-slate-900' : 'translate-x-1 text-slate-700'
        }`}
      >
        {darkMode ? '🌙' : '☀️'}
      </span>
    </button>
  )
}

export default function TopBar({ role, onRoleChange, darkMode, onDarkModeChange }) {
  const handleLogout = () => {
    apiLogout()
    onRoleChange?.(null)
  }

  return (
    <header className="flex flex-col gap-3 border-b border-slate-200 bg-white px-5 py-4 transition-colors duration-300 dark:border-slate-800 dark:bg-slate-950 lg:flex-row lg:items-center lg:justify-between">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
          {MODEL_VERSION}
        </span>
        <span className="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300">
          {ENVIRONMENT}
        </span>
        <span className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
          {role}
        </span>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="text-right">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500">Active role</p>
          <p className="text-sm font-medium text-slate-700">Switch visibility and action permissions</p>
        </div>
        <RoleSwitcher role={role} onChange={onRoleChange} />
        <button
          type="button"
          onClick={handleLogout}
          className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          Logout
        </button>
        <ThemeToggle darkMode={darkMode} onDarkModeChange={onDarkModeChange} />
      </div>
    </header>
  )
}
