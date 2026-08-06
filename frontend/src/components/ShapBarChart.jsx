import { BarElement, CategoryScale, Chart as ChartJS, LinearScale, Tooltip } from 'chart.js'
import { Bar } from 'react-chartjs-2'

ChartJS.register(BarElement, CategoryScale, LinearScale, Tooltip)

export default function ShapBarChart({ values }) {
  const data = {
    labels: values.map((item) => item.feature),
    datasets: [
      {
        label: 'SHAP contribution',
        data: values.map((item) => item.value),
        backgroundColor: values.map((item) => (item.value >= 0 ? 'rgba(16, 185, 129, 0.8)' : 'rgba(244, 63, 94, 0.8)')),
        borderRadius: 8,
      },
    ],
  }

  return (
    <div className="h-72 rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-800 dark:bg-slate-950">
      <Bar
        data={data}
        options={{
          indexAxis: 'y',
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (context) => `${context.parsed.x.toFixed(3)}`,
              },
            },
          },
          scales: {
            x: {
              grid: { color: 'rgba(148, 163, 184, 0.18)' },
              ticks: { color: '#64748b' },
            },
            y: {
              grid: { display: false },
                ticks: { color: '#334155' },
            },
          },
        }}
      />
    </div>
  )
}