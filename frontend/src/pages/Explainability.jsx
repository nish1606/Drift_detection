import { useState, useEffect } from 'react'
import api from '../utils/api'

export default function Explainability() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.get('/explainability/global').then(r => { setData(r.data); setLoading(false) }).catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-6">Loading explainability data...</div>

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Explainability</h1>
      <div className="bg-white rounded shadow p-4">
        <table className="w-full text-left">
          <thead><tr><th>Feature</th><th>Importance</th></tr></thead>
          <tbody>
            {data.map((row, i) => (
              <tr key={i} className="border-t">
                <td className="p-2">{row.feature}</td>
                <td className="p-2">{row.importance.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
