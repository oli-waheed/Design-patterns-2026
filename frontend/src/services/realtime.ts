// Phase 12 dashboard WebSocket client.
//
// One shared connection to WS /api/ws, opened when the first component
// subscribes. The backend forwards EventBus events as
// { type, payload } frames: reading.created, actuator.state_changed and
// alert.created. Components that poll (sensor cards, event feed) poll
// only while the status is not "connected"; polling is the fallback.

import { API_BASE_URL } from './api'

export type RealtimeEvent = {
  type: string
  payload: unknown
}

export type RealtimeStatus = 'connected' | 'connecting' | 'down'

export type ReadingCreatedPayload = {
  device_id: string
  value: number
  unit: string
  source: string
  recorded_at: string
  location_id: string | null
  zone_id: string | null
}

export type ActuatorStateChangedPayload = {
  device_id: string
  previous_state: string
  state: string
  location_id: string | null
  zone_id: string | null
}

export type AlertCreatedPayload = {
  id: string
  severity: 'info' | 'warning' | 'critical'
  message: string
  event_type: string
  status: 'active' | 'resolved'
  created_at: string
  device_id: string | null
  location_id: string | null
  zone_id: string | null
}

type EventHandler = (event: RealtimeEvent) => void
type StatusListener = (status: RealtimeStatus) => void

const MIN_RETRY_MS = 1000
const MAX_RETRY_MS = 15000

/** Snapshot for the header indicator. Replaced (never mutated) on change. */
export type RealtimeInfo = {
  status: RealtimeStatus
  /** Failed attempts since the last successful connection. */
  attempt: number
  /** When the next reconnect is scheduled (ms since epoch), if any. */
  nextRetryAt: number | null
}

const eventHandlers = new Set<EventHandler>()
const statusListeners = new Set<StatusListener>()

let socket: WebSocket | null = null
let status: RealtimeStatus = 'down'
let attempt = 0
let retryTimer: number | null = null
let info: RealtimeInfo = { status, attempt, nextRetryAt: null }
const infoListeners = new Set<() => void>()

function publishInfo(nextRetryAt: number | null) {
  info = { status, attempt, nextRetryAt }
  infoListeners.forEach((listener) => listener())
}

export function getWebSocketUrl(): string {
  const url = new URL('/api/ws', API_BASE_URL)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return url.toString()
}

function setStatus(next: RealtimeStatus) {
  if (status === next) {
    return
  }

  status = next
  statusListeners.forEach((listener) => listener(next))
  publishInfo(next === 'down' ? info.nextRetryAt : null)
}

function hasSubscribers() {
  return eventHandlers.size > 0 || statusListeners.size > 0
}

function scheduleReconnect() {
  if (retryTimer !== null || !hasSubscribers()) {
    return
  }

  // Exponential backoff: 1 s, 2 s, 4 s, 8 s, then 15 s between attempts.
  const delay = Math.min(MIN_RETRY_MS * 2 ** attempt, MAX_RETRY_MS)
  attempt += 1

  retryTimer = window.setTimeout(() => {
    retryTimer = null
    connect()
  }, delay)

  publishInfo(Date.now() + delay)
}

/** Try now instead of waiting for the backoff timer. */
export function reconnectNow() {
  if (retryTimer !== null) {
    window.clearTimeout(retryTimer)
    retryTimer = null
  }

  connect()
}

function connect() {
  if (socket !== null || !hasSubscribers()) {
    return
  }

  setStatus('connecting')

  let ws: WebSocket

  try {
    ws = new WebSocket(getWebSocketUrl())
  } catch {
    setStatus('down')
    scheduleReconnect()
    return
  }

  socket = ws

  ws.onopen = () => {
    attempt = 0
    setStatus('connected')
  }

  ws.onmessage = (message) => {
    let event: RealtimeEvent

    try {
      event = JSON.parse(String(message.data)) as RealtimeEvent
    } catch {
      return
    }

    if (typeof event?.type !== 'string') {
      return
    }

    eventHandlers.forEach((handler) => handler(event))
  }

  ws.onclose = () => {
    if (socket === ws) {
      socket = null
    }

    setStatus('down')
    scheduleReconnect()
  }

  ws.onerror = () => {
    // onclose follows and handles the retry.
    ws.close()
  }
}

function disconnectIfUnused() {
  if (hasSubscribers()) {
    return
  }

  if (retryTimer !== null) {
    window.clearTimeout(retryTimer)
    retryTimer = null
  }

  const current = socket
  socket = null
  current?.close()
  setStatus('down')
}

export function subscribeRealtime(
  onEvent: (event: RealtimeEvent) => void,
): () => void {
  eventHandlers.add(onEvent)
  connect()

  return () => {
    eventHandlers.delete(onEvent)
    disconnectIfUnused()
  }
}

export function subscribeRealtimeStatus(
  listener: StatusListener,
): () => void {
  statusListeners.add(listener)
  connect()

  return () => {
    statusListeners.delete(listener)
    disconnectIfUnused()
  }
}

/** For useSyncExternalStore: status plus retry details. */
export function subscribeRealtimeInfo(listener: () => void): () => void {
  infoListeners.add(listener)
  const unsubscribeStatus = subscribeRealtimeStatus(() => {})

  return () => {
    infoListeners.delete(listener)
    unsubscribeStatus()
  }
}

export function getRealtimeInfo(): RealtimeInfo {
  return info
}

export function getRealtimeStatus(): RealtimeStatus {
  return status
}
