import { useState, useEffect } from 'react'
import api from '../utils/api'

export default function FairnessMonitoring() {
  const [metrics, setMetrics] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/monitoring/fairness').then(r => { setMetrics(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-6">Loading fairness metrics...</div>

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Fairness Monitoring</h1>
      <div className="bg-white rounded shadow p-4">
        <table className="w-full text-left">
          <thead><tr><th>Segment</th><th>Approval Rate</th><th>False Positive Rate</th><th>Delta</th></tr></thead>
          <tbody>
            {metrics.map((row, i) => (
              <tr key={i} className="border-t">
                <td className="p-2">{row.segment}</td>
                <td className="p-2">{(row.approval_rate * 100).toFixed(1)}%</td>
                <td className="p-2">{(row.false_positive_rate * 100).toFixed(1)}%</td>
                <td className="p-2">{row.delta.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
