import { useEffect, useState } from 'react'

import { useRealtimeInfo } from '../hooks/useRealtime'
import { reconnectNow } from '../services/realtime'

/**
 * Header badge for the dashboard WebSocket (/api/ws). Status colors always
 * come with a text label. While offline it shows the backoff countdown and
 * lets the operator retry immediately.
 */
export default function ConnectionStatus() {
  const { status, attempt, nextRetryAt } = useRealtimeInfo()
  const [now, setNow] = useState(() => Date.now())

  // Tick once a second only while a retry is scheduled.
  useEffect(() => {
    if (status !== 'down' || nextRetryAt === null) {
      return
    }

    const id = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(id)
  }, [status, nextRetryAt])

  if (status === 'connected') {
    return (
      <div
        className="badge badge-ok px-3 py-1.5 text-sm"
        data-status={status}
        title="Live updates over the dashboard WebSocket"
      >
        <span className="h-2 w-2 rounded-full bg-ok" aria-hidden="true" />
        Live
      </div>
    )
  }

  if (status === 'connecting') {
    return (
      <div
        className="badge badge-warn px-3 py-1.5 text-sm"
        data-status={status}
        title="Connecting to the dashboard WebSocket"
      >
        <span
          className="h-2 w-2 animate-pulse rounded-full bg-warn"
          aria-hidden="true"
        />
        Connecting…{attempt > 0 && ` (attempt ${attempt + 1})`}
      </div>
    )
  }

  const seconds =
    nextRetryAt === null ? null : Math.max(0, Math.ceil((nextRetryAt - now) / 1000))

  return (
    <div
      className="badge badge-error gap-2 px-3 py-1.5 text-sm"
      data-status={status}
      title="Offline: panels poll every 5 s until the connection is back"
      role="status"
    >
      <span className="h-2 w-2 rounded-full bg-error" aria-hidden="true" />
      <span>
        Offline
        {seconds !== null && (
          <span className="font-normal"> · retry in {seconds} s</span>
        )}
      </span>
      <button
        type="button"
        onClick={reconnectNow}
        className="rounded px-1.5 py-0.5 text-xs font-semibold underline hover:bg-red-100"
      >
        Retry now
      </button>
    </div>
  )
}
