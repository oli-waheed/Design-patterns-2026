import { useEffect, useRef, useSyncExternalStore } from 'react'

import {
  getRealtimeInfo,
  getRealtimeStatus,
  subscribeRealtimeInfo,
  subscribeRealtime,
  subscribeRealtimeStatus,
  type RealtimeEvent,
  type RealtimeInfo,
  type RealtimeStatus,
} from '../services/realtime'

/** Current dashboard WebSocket status; re-renders when it changes. */
export function useRealtimeStatus(): RealtimeStatus {
  return useSyncExternalStore(
    subscribeRealtimeStatus,
    getRealtimeStatus,
    getRealtimeStatus,
  )
}

/** Status plus reconnect attempt and next retry time (header badge). */
export function useRealtimeInfo(): RealtimeInfo {
  return useSyncExternalStore(
    subscribeRealtimeInfo,
    getRealtimeInfo,
    getRealtimeInfo,
  )
}

/** Calls the latest handler for every WebSocket frame. */
export function useRealtimeEvents(
  handler: (event: RealtimeEvent) => void,
): void {
  const handlerRef = useRef(handler)

  useEffect(() => {
    handlerRef.current = handler
  })

  useEffect(
    () => subscribeRealtime((event) => handlerRef.current(event)),
    [],
  )
}
