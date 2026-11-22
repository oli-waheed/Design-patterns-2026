import { useEffect, useState } from 'react'
import { getHealth, type HealthResponse } from '../services/api'

export default function HealthStatus() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [error, setError] = useState(false)

  useEffect(() => {
    getHealth()
      .then((data) => {
        setHealth(data)
        setError(false)
      })
      .catch(() => {
        setError(true)
      })
  }, [])

  if (error) {
    return (
      <div className="badge badge-error px-3 py-1.5 text-sm">
        <span aria-hidden="true">⛔</span>
        API unavailable
      </div>
    )
  }

  if (!health) {
    return (
      <div className="badge badge-neutral px-3 py-1.5 text-sm">
        Checking API…
      </div>
    )
  }

  const isHealthy = health.status === 'ok' && health.db === 'ok'

  return (
    <div
      className={`badge px-3 py-1.5 text-sm ${
        isHealthy ? 'badge-ok' : 'badge-warn'
      }`}
    >
      <span aria-hidden="true">{isHealthy ? '✓' : '⚠'}</span>
      {isHealthy ? 'API healthy' : 'API degraded'}
    </div>
  )
}