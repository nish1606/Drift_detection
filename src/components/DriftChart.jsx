import { CategoryScale, Chart as ChartJS, Filler, Legend, LineElement, LinearScale, PointElement, Tooltip } from 'chart.js'
import { Line } from 'react-chartjs-2'

ChartJS.register(CategoryScale, Filler, Legend, LineElement, LinearScale, PointElement, Tooltip)

function formatDelta(value) {
  const rounded = Math.abs(value) >= 10 ? Math.round(Math.abs(value)) : Math.round(Math.abs(value) * 10) / 10
  return `${rounded}%`
}

export default function DriftChart({ title, subtitle, labels, datasets, selector, onSelectorChange, options, heightClass = 'h-72', trendMode = 'higherIsBetter' }) {
  const firstSeries = datasets[0]?.data ?? []
  const firstValue = Number(firstSeries[0])
  const lastValue = Number(firstSeries[firstSeries.length - 1])
  const relativeChange = Number.isFinite(firstValue) && firstValue !== 0 ? ((lastValue - firstValue) / Math.abs(firstValue)) * 100 : 0
  const changeThreshold = 3
  const isBadTrend = trendMode === 'higherIsBetter' ? relativeChange < -changeThreshold : relativeChange > changeThreshold
  const tone = isBadTrend ? 'text-rose-600 dark:text-rose-300' : 'text-emerald-600 dark:text-emerald-300'
  const arrow = relativeChange === 0 ? '→' : relativeChange > 0 ? '↑' : '↓'

  const chartData = {
    labels,
    datasets: datasets.map((dataset) => ({
      ...dataset,
      borderWidth: 2,
      pointRadius: 1.5,
      pointHoverRadius: 4,
      tension: 0.35,
      fill: false,
    })),
  }

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-950">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-base font-semibold text-slate-900 dark:text-slate-50">{title}</h3>
            <span className={`text-xs font-semibold ${tone}`}>{arrow} {formatDelta(relativeChange)} over 24h</span>
          </div>
          {subtitle ? <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{subtitle}</p> : null}
        </div>
        {selector ? (
          <select
            value={selector.value}
            onChange={(event) => onSelectorChange?.(event.target.value)}
            className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-700 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-200"
          >
            {selector.options.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        ) : null}
      </div>
      <div className={`${heightClass} rounded-xl border border-slate-100 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-900`}>
        <Line
          data={chartData}
          options={{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: datasets.length > 1 },
              tooltip: { mode: 'index', intersect: false },
            },
            interaction: { mode: 'index', intersect: false },
            scales: {
              x: {
                grid: { display: false },
                ticks: { color: '#64748b', maxTicksLimit: 8 },
              },
              y: {
                grid: { color: 'rgba(148, 163, 184, 0.16)' },
                ticks: { color: '#64748b' },
                ...options?.y,
              },
            },
            ...options,
          }}
        />
      </div>
    </section>
  )
}