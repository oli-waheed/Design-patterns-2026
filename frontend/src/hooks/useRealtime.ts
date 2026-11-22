import { useEffect, useRef, useSyncExternalStore } from 'react'

import {
  getRealtimeStatus,
  subscribeRealtime,
  subscribeRealtimeStatus,
  type RealtimeEvent,
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
