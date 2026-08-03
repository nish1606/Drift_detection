import { useEffect, useRef, useState } from 'react'

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

function getTone(score) {
  if (score >= 78) return 'var(--health-good)'
  if (score >= 58) return 'var(--health-watch)'
  return 'var(--health-alert)'
}

export default function ModelHealthGauge({ score, summary }) {
  const [displayScore, setDisplayScore] = useState(score)
  const currentScoreRef = useRef(score)

  useEffect(() => {
    let frame = 0
    const start = currentScoreRef.current
    const target = score
    const duration = 320
    const startTime = performance.now()

    const tick = (now) => {
      const progress = clamp((now - startTime) / duration, 0, 1)
      const next = start + (target - start) * progress
      currentScoreRef.current = next
      setDisplayScore(Math.round(next))

      if (progress < 1) {
        frame = window.requestAnimationFrame(tick)
      }
    }

    frame = window.requestAnimationFrame(tick)

    return () => window.cancelAnimationFrame(frame)
  }, [score])

  const tone = getTone(displayScore)

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="max-w-2xl space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-slate-500 dark:text-slate-400">Model health</p>
          <h2 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">Single score for confidence, drift, and fairness</h2>
          <p className="text-sm leading-6 text-slate-600 dark:text-slate-300">{summary?.healthSummary ?? summary}</p>
        </div>

        <div className="flex items-center gap-5">
          <div
            className="relative flex h-36 w-36 items-center justify-center rounded-full"
            style={{ background: `conic-gradient(${tone} ${displayScore}%, rgba(148, 163, 184, 0.18) 0)` }}
          >
            <div className="flex h-[8.25rem] w-[8.25rem] flex-col items-center justify-center rounded-full border border-slate-200 bg-white text-center dark:border-slate-800 dark:bg-slate-950">
              <span className="text-xs font-semibold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Health</span>
              <strong className="text-4xl font-semibold tracking-tight text-slate-900 dark:text-slate-50">{displayScore}</strong>
              <span className="text-xs text-slate-500 dark:text-slate-400">0 - 100</span>
            </div>
          </div>

          <div className="grid gap-2 text-sm text-slate-600 dark:text-slate-300">
            <HealthChip label="Confidence" value={`${summary?.confidence ?? 0}%`} tone={summary?.confidenceTone ?? 'emerald'} />
            <HealthChip label="Drift" value={`${summary?.drift ?? 0}%`} tone={summary?.driftTone ?? 'amber'} />
            <HealthChip label="Fairness" value={`${summary?.fairness ?? 0}%`} tone={summary?.fairnessTone ?? 'slate'} />
          </div>
        </div>
      </div>
    </article>
  )
}

function HealthChip({ label, value, tone }) {
  const styles = {
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/50 dark:text-emerald-300',
    amber: 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-300',
    rose: 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-300',
    slate: 'border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300',
  }

  return (
    <div className={`rounded-xl border px-3 py-2 ${styles[tone]}`}>
      <div className="text-xs font-semibold uppercase tracking-[0.2em]">{label}</div>
      <div className="mt-1 text-sm font-semibold">{value}</div>
    </div>
  )
}