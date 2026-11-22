import { useRealtimeStatus } from '../hooks/useRealtime'

const styles = {
  connected: {
    label: 'Live',
    className: 'bg-green-100 text-green-800',
    dot: 'bg-green-500',
  },
  connecting: {
    label: 'Connecting…',
    className: 'bg-yellow-100 text-yellow-800',
    dot: 'bg-yellow-500 animate-pulse',
  },
  down: {
    label: 'Offline – retrying',
    className: 'bg-red-100 text-red-800',
    dot: 'bg-red-500',
  },
} as const

export default function ConnectionStatus() {
  const status = useRealtimeStatus()
  const style = styles[status]

  return (
    <div
      className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm ${style.className}`}
      title="Dashboard WebSocket (/api/ws). While offline, panels fall back to polling."
      data-status={status}
    >
      <span className={`h-2 w-2 rounded-full ${style.dot}`} />
      {style.label}
    </div>
  )
}
