export default function LiveTransactionStream({ transactions }) {
  const stream = transactions.slice(0, 18).map((transaction, index) => ({
    ...transaction,
    lane: index % 3,
  }))

  return (
    <article className="overflow-hidden rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50">Live transaction flow</h3>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Incoming activity animates from left to right, with higher-risk items slipping into review.</p>
        </div>
        <span className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-slate-500 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-400">
          Polling
        </span>
      </div>

      <div className="mt-4 space-y-2">
        {[0, 1, 2].map((lane) => (
          <div key={lane} className="relative h-5 overflow-hidden rounded-full border border-slate-100 bg-slate-50 dark:border-slate-800 dark:bg-slate-900">
            <div className="absolute inset-y-0 left-0 flex items-center gap-2 animate-[flow_8s_linear_infinite]">
              {stream.filter((item) => item.lane === lane).map((transaction) => {
                const tone = transaction.status === 'Pending' ? 'bg-amber-400' : transaction.status === 'Escalated' ? 'bg-rose-500' : transaction.status === 'Approved' ? 'bg-emerald-500' : 'bg-slate-400'

                return <span key={transaction.id} className={`h-2.5 w-2.5 rounded-full ${tone} ${transaction.status === 'Pending' ? 'shadow-[0_0_0_4px_rgba(251,191,36,0.12)]' : ''}`} title={transaction.id} />
              })}
            </div>
          </div>
        ))}
      </div>
    </article>
  )
}