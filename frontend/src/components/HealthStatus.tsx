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
      <div className="rounded-lg bg-red-100 px-4 py-2 text-sm text-red-800">
        - System unavailable
      </div>
    )
  }

  if (!health) {
    return (
      <div className="rounded-lg bg-gray-100 px-4 py-2 text-sm text-gray-700">
        - Checking system...
      </div>
    )
  }

  const isHealthy = health.status === 'ok' && health.db === 'ok'

  return (
    <div
      className={`rounded-lg px-4 py-2 text-sm ${
        isHealthy
          ? 'bg-green-100 text-green-800'
          : 'bg-yellow-100 text-yellow-800'
      }`}
    >
      - {isHealthy ? 'System healthy' : 'System degraded'}
    </div>
  )
}