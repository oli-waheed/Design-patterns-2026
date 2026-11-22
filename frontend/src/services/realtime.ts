// Phase 11 stub for realtime updates.
//
// In this phase the event feed polls GET /api/alerts every 5 seconds.
// Phase 12 replaces the body of subscribeRealtime with the dashboard
// WebSocket, which is subscribed to the same backend EventBus
// (for example AlertCreated), so components do not need to change.

export type RealtimeEvent = {
  type: string
  payload: unknown
}

export type RealtimeHandler = (event: RealtimeEvent) => void

export function subscribeRealtime(
  handler: RealtimeHandler,
): () => void {
  // No-op until Phase 12. The handler is intentionally unused.
  void handler

  return () => {
    // Nothing to unsubscribe from yet.
  }
}
