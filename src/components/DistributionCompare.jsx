export default function DistributionCompare({ title, subtitle, bins, mix, onMixChange, split, onSplitChange }) {
  const splitWeight = Math.max(0, Math.min(1, split / 100))
  const maxValue = Math.max(
    ...bins.flatMap((bin) => {
      const baselineValue = Math.round(bin.reference * (1 - splitWeight) + bin.current * splitWeight)
      const currentValue = Math.round(bin.reference * splitWeight + bin.current * (1 - splitWeight))
      return [baselineValue, currentValue]
    }),
    1,
  )

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50">{title}</h3>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{subtitle}</p>
        </div>
        <div className="flex flex-col gap-2 sm:min-w-[220px]">
          <label className="text-sm font-medium text-slate-600 dark:text-slate-300">
            Baseline share: <span className="font-semibold text-slate-900 dark:text-slate-100">{split}%</span>
            <input type="range" min="0" max="100" value={split} onChange={(event) => onSplitChange(Number(event.target.value))} className="mt-2 h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-slate-900 dark:bg-slate-800" />
          </label>
          <label className="text-sm font-medium text-slate-600 dark:text-slate-300">
            Blend
            <input type="range" min="0" max="100" value={mix} onChange={(event) => onMixChange(Number(event.target.value))} className="mt-2 h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-slate-900 dark:bg-slate-800" />
          </label>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-10 gap-2 rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
        {bins.map((bin) => {
          const baselineValue = Math.round(bin.reference * (1 - splitWeight) + bin.current * splitWeight)
          const currentValue = Math.round(bin.reference * splitWeight + bin.current * (1 - splitWeight))
          const baselineHeight = (baselineValue / maxValue) * 100
          const currentHeight = (currentValue / maxValue) * 100

          return (
            <div key={bin.bin} className="flex h-40 flex-col justify-end gap-1 text-[10px] text-slate-500 dark:text-slate-400">
              <div className="relative flex h-32 items-end justify-center rounded-md">
                <div className="absolute bottom-0 left-1/2 w-4 -translate-x-1/2 rounded-t-md bg-slate-400/35 transition-all duration-300" style={{ height: `${baselineHeight}%`, opacity: (100 - mix) / 100 }} />
                <div className="absolute bottom-0 left-1/2 w-4 -translate-x-1/2 rounded-t-md bg-emerald-500/55 transition-all duration-300" style={{ height: `${currentHeight}%`, opacity: mix / 100 }} />
              </div>
              <span className="text-center">{bin.label}</span>
            </div>
          )
        })}
      </div>

      <div className="mt-3 flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
        <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-slate-400/60" />Baseline slice</span>
        <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-500/70" />Current slice</span>
      </div>
    </article>
  )
}