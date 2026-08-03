export default function DistributionCompare({ title, subtitle, bins, mix, onMixChange }) {
  const maxValue = Math.max(...bins.flatMap((bin) => [bin.reference, bin.current]), 1)

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50">{title}</h3>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{subtitle}</p>
        </div>
        <label className="text-sm font-medium text-slate-600 dark:text-slate-300">
          Blend
          <input type="range" min="0" max="100" value={mix} onChange={(event) => onMixChange(Number(event.target.value))} className="mt-2 h-2 w-full cursor-pointer appearance-none rounded-full bg-slate-200 accent-slate-900 dark:bg-slate-800" />
        </label>
      </div>

      <div className="mt-4 grid grid-cols-10 gap-2 rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-900">
        {bins.map((bin) => {
          const referenceHeight = (bin.reference / maxValue) * 100
          const currentHeight = (bin.current / maxValue) * 100

          return (
            <div key={bin.bin} className="flex h-40 flex-col justify-end gap-1 text-[10px] text-slate-500 dark:text-slate-400">
              <div className="relative flex h-32 items-end justify-center rounded-md">
                <div className="absolute bottom-0 left-1/2 w-4 -translate-x-1/2 rounded-t-md bg-slate-400/35 transition-all duration-300" style={{ height: `${referenceHeight}%`, opacity: (100 - mix) / 100 }} />
                <div className="absolute bottom-0 left-1/2 w-4 -translate-x-1/2 rounded-t-md bg-emerald-500/55 transition-all duration-300" style={{ height: `${currentHeight}%`, opacity: mix / 100 }} />
              </div>
              <span className="text-center">{bin.label}</span>
            </div>
          )
        })}
      </div>

      <div className="mt-3 flex items-center gap-4 text-xs text-slate-500 dark:text-slate-400">
        <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-slate-400/60" />Reference</span>
        <span className="inline-flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-emerald-500/70" />Current</span>
      </div>
    </article>
  )
}