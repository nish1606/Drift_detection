import { useEffect, useState } from 'react'

export default function useScreenReady(trigger, delay = 900) {
  const [ready, setReady] = useState(false)

  useEffect(() => {
    setReady(false)
    const timer = window.setTimeout(() => setReady(true), delay)
    return () => window.clearTimeout(timer)
  }, [delay, trigger])

  return ready
}
