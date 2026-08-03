import { IconCheck, IconInfoCircle, IconX } from '@tabler/icons-react'

const toneClasses = {
  success: 'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/60 dark:text-emerald-200',
  warning: 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/60 dark:text-amber-200',
  info: 'border-slate-200 bg-white text-slate-800 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-100',
}

export default function ToastStack({ toasts, onDismiss }) {
  return (
    <div className="fixed bottom-4 right-4 z-50 flex w-[24rem] max-w-[calc(100vw-2rem)] flex-col gap-3">
      {toasts.map((toast) => (
        <article key={toast.id} className={`rounded-2xl border p-4 shadow-sm ${toneClasses[toast.tone] ?? toneClasses.info}`}>
          <div className="flex items-start gap-3">
            <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/70 dark:bg-slate-900">
              {toast.tone === 'success' ? <IconCheck size={16} /> : <IconInfoCircle size={16} />}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold">{toast.title}</p>
              {toast.message ? <p className="mt-1 text-sm opacity-90">{toast.message}</p> : null}
            </div>
            <button type="button" onClick={() => onDismiss(toast.id)} className="rounded-full p-1 text-current/70 hover:bg-black/5 dark:hover:bg-white/10">
              <IconX size={16} />
            </button>
          </div>
        </article>
      ))}
    </div>
  )
}
