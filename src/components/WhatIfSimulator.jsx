import { useMemo, useState } from 'react'

function scoreFromInputs(inputs) {
  const base = 0.08
  const device = inputs.newDevices * 0.62
  const amount = Math.max(0, (inputs.avgAmount - 1500) / 4000) * 0.28
  const geos = inputs.geoMismatch * 0.42
  return Math.min(0.85, Number((base + device + amount + geos).toFixed(3)))
}

export default function WhatIfSimulator() {
  const [inputs, setInputs] = useState({ newDevices: 24, avgAmount: 2400, geoMismatch: 18 })

  const score = useMemo(
    () =>
      scoreFromInputs({
        newDevices: inputs.newDevices / 100,
        avgAmount: inputs.avgAmount,
        geoMismatch: inputs.geoMismatch / 100,
      }),
    [inputs],
  )

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
      <div>
        <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50">What-if drift simulator</h3>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Drag the sliders to see how sensitive the detectors are before changing production thresholds.</p>
      </div>

      <div className="mt-4 grid gap-4">
        <SimSlider label="% new devices" value={inputs.newDevices} max={100} onChange={(value) => setInputs((current) => ({ ...current, newDevices: value }))} />
        <SimSlider label="Avg transaction amount" value={inputs.avgAmount} max={6000} step={50} suffix="USD" onChange={(value) => setInputs((current) => ({ ...current, avgAmount: value }))} />
        <SimSlider label="Geo mismatch rate" value={inputs.geoMismatch} max={100} onChange={(value) => setInputs((current) => ({ ...current, geoMismatch: value }))} />
      </div>

      <div className="mt-4 rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">Projected PSI</p>
        <strong className="mt-1 block text-3xl font-semibold text-slate-900 dark:text-slate-50">{score.toFixed(3)}</strong>
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">Higher new-device and geo mismatch rates push the risk signal upward.</p>
      </div>
    </article>
  )
}

function SimSlider({ label, value, max, step = 1, suffix, onChange }) {
  return (
    <label className="grid gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
      <span className="flex items-center justify-between gap-3">
        {label}
        <span className="text-slate-500 dark:text-slate-400">
          {value}
          {suffix ? ` ${suffix}` : ''}
        </span>
      </span>
      <input type="range" min="0" max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} className="h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-slate-900 dark:bg-slate-800" />
    </label>
  )
}