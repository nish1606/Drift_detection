import { useEffect, useState } from 'react'

export default function LastUpdated({ lastRefreshed, intervalMs = 1000 }) {
  const [now, setNow] = useState(new Date())

  useEffect(() => {
    const timer = window.setInterval(() => setNow(new Date()), intervalMs)
    return () => window.clearInterval(timer)
  }, [intervalMs])

  const displayTime = lastRefreshed ? new Date(lastRefreshed) : now
  const label = lastRefreshed ? 'Data refreshed at' : 'Last updated'

  return (
    <span className="text-xs text-slate-500 dark:text-slate-400">
      {label} {displayTime.toLocaleTimeString()}
    </span>
  )
}
