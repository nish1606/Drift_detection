import { IconBell, IconArrowRight } from '@tabler/icons-react'

export default function NotificationsMenu({ open, items, unreadIds = [], onClose, onSelect }) {
  if (!open) {
    return null
  }

  return (
    <div className="absolute right-0 top-11 z-50 w-[22rem] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <IconBell size={16} className="text-slate-500" />
          <p className="text-sm font-semibold text-slate-900 dark:text-slate-50">Governance alerts</p>
        </div>
        <button type="button" onClick={onClose} className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
          Close
        </button>
      </div>

      <div className="max-h-[24rem] overflow-y-auto p-2">
        {items.slice(0, 5).map((item) => {
          const unread = unreadIds.includes(item.id)
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect?.(item)}
              className="flex w-full items-start gap-3 rounded-xl px-3 py-3 text-left transition hover:bg-slate-50 dark:hover:bg-slate-900"
            >
              <span className={`mt-1 h-2.5 w-2.5 rounded-full ${unread ? 'bg-amber-500' : 'bg-slate-300 dark:bg-slate-600'}`} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-semibold text-slate-900 dark:text-slate-50">{item.action}</p>
                <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{item.reason}</p>
              </div>
              <IconArrowRight size={16} className="mt-1 text-slate-400" />
            </button>
          )
        })}
      </div>
    </div>
  )
}
