import { useEffect, useRef, useState } from 'react'

export default function MetricCard({ label, value, sublabel, tone = 'neutral', animate = true, suffix = '' }) {
  const [displayValue, setDisplayValue] = useState(value)
  const currentValueRef = useRef(value)

  useEffect(() => {
    if (typeof value !== 'number' || !animate) {
      setDisplayValue(value)
      currentValueRef.current = value
      return
    }

    let frame = 0
    const start = typeof currentValueRef.current === 'number' ? currentValueRef.current : value
    const target = value
    const startTime = performance.now()

    const tick = (now) => {
      const progress = Math.min(1, (now - startTime) / 280)
      const nextValue = Math.round((start + (target - start) * progress) * 100) / 100
      currentValueRef.current = nextValue
      setDisplayValue(nextValue)
      if (progress < 1) {
        frame = window.requestAnimationFrame(tick)
      }
    }

    frame = window.requestAnimationFrame(tick)
    return () => window.cancelAnimationFrame(frame)
  }, [animate, value])

  const toneClasses = {
    neutral: 'border-slate-200 bg-white text-slate-900 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-50',
    success: 'border-emerald-200 bg-emerald-50 text-emerald-950 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-100',
    warning: 'border-amber-200 bg-amber-50 text-amber-950 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-100',
    danger: 'border-rose-200 bg-rose-50 text-rose-950 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-100',
  }

  return (
    <article className={`rounded-xl border p-4 ${toneClasses[tone] ?? toneClasses.neutral}`}>
      <p className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">{label}</p>
      <div className="mt-3 flex items-end justify-between gap-3">
        <strong className="text-2xl font-semibold tracking-tight">
          {typeof displayValue === 'number' ? displayValue.toLocaleString() : displayValue}
          {suffix}
        </strong>
      </div>
      {sublabel ? <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{sublabel}</p> : null}
    </article>
  )
}