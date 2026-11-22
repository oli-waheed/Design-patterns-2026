import { useEffect, useState } from 'react'

import EmptyState from '../ui/EmptyState'
import { SkeletonList } from '../ui/Skeleton'
import { useRealtimeEvents, useRealtimeStatus } from '../../hooks/useRealtime'
import {
  getAlerts,
  getLocation,
  getLocations,
  updateAlertStatus,
  type AlertDto,
  type AlertSeverity,
  type AlertStatusFilter,
  type LocationSummaryDto,
  type ZoneDto,
} from '../../services/api'
import type { AlertCreatedPayload } from '../../services/realtime'

// Phase 11 poll. Phase 12: only used while the WebSocket is down.
const POLL_INTERVAL_MS = 5000

type SortOrder = 'newest' | 'severity'

// Status colors never carry meaning alone: each has an icon and a label.
const severityBadge: Record<
  AlertSeverity,
  { className: string; icon: string; rank: number }
> = {
  critical: { className: 'badge-error', icon: '⛔', rank: 0 },
  warning: { className: 'badge-warn', icon: '⚠', rank: 1 },
  info: { className: 'badge-info', icon: 'ℹ', rank: 2 },
}

const eventTypeLabels: Record<string, string> = {
  'threshold.crossed': 'Threshold crossed',
  'command.failed': 'Command failed',
  'state.changed': 'State changed',
}

const statusOptions: { value: AlertStatusFilter; label: string }[] = [
  { value: 'active', label: 'Active' },
  { value: 'all', label: 'All' },
  { value: 'resolved', label: 'Resolved' },
]

function formatDate(value: string): string {
  const date = new Date(value)

  return Number.isNaN(date.getTime()) ? value : date.toLocaleString()
}

function sortAlerts(alerts: AlertDto[], order: SortOrder): AlertDto[] {
  if (order === 'newest') {
    return alerts
  }

  // Most severe first; newest first within a severity (API order is kept).
  return [...alerts].sort(
    (a, b) =>
      (severityBadge[a.severity]?.rank ?? 9) -
      (severityBadge[b.severity]?.rank ?? 9),
  )
}

export default function EventFeed() {
  const [alerts, setAlerts] = useState<AlertDto[]>([])
  const [locations, setLocations] = useState<LocationSummaryDto[]>([])
  const [zones, setZones] = useState<ZoneDto[]>([])

  const [statusFilter, setStatusFilter] = useState<AlertStatusFilter>('active')
  const [sortOrder, setSortOrder] = useState<SortOrder>('newest')
  const [locationId, setLocationId] = useState('')
  const [zoneId, setZoneId] = useState('')

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const [updatingId, setUpdatingId] = useState<string | null>(null)

  // Bumped by alert.created frames and by resolve/reopen, which re-runs the
  // load effect below.
  const [reloadVersion, setReloadVersion] = useState(0)

  const realtimeStatus = useRealtimeStatus()
  const live = realtimeStatus === 'connected'

  useRealtimeEvents((event) => {
    if (event.type !== 'alert.created' || statusFilter === 'resolved') {
      return
    }

    const alert = event.payload as AlertCreatedPayload

    if (locationId && alert.location_id !== locationId) {
      return
    }

    if (zoneId && alert.zone_id !== zoneId) {
      return
    }

    setReloadVersion((current) => current + 1)
  })

  // Locations for the filter.
  useEffect(() => {
    let cancelled = false

    getLocations()
      .then((data) => {
        if (!cancelled) {
          setLocations(data)
        }
      })
      .catch(() => {
        // The feed still works without the filter options.
      })

    return () => {
      cancelled = true
    }
  }, [])

  // Zones of the selected location.
  useEffect(() => {
    let cancelled = false

    const request = locationId
      ? getLocation(locationId).then((data) => data.zones)
      : Promise.resolve<ZoneDto[]>([])

    request
      .then((data) => {
        if (!cancelled) {
          setZones(data)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setZones([])
        }
      })

    return () => {
      cancelled = true
    }
  }, [locationId])

  // Alerts for the current filter. Prefers the WebSocket; polls every 5 s
  // only while it is not connected.
  useEffect(() => {
    let cancelled = false

    async function loadAlerts() {
      try {
        const data = await getAlerts({
          status: statusFilter,
          locationId: locationId || undefined,
          zoneId: zoneId || undefined,
          limit: 100,
        })

        if (!cancelled) {
          setAlerts(data)
          setError(null)
          setLastUpdated(new Date())
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load alerts')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadAlerts()

    if (live) {
      return () => {
        cancelled = true
      }
    }

    const intervalId = window.setInterval(loadAlerts, POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [statusFilter, locationId, zoneId, live, reloadVersion])

  async function changeStatus(alert: AlertDto, status: 'active' | 'resolved') {
    try {
      setUpdatingId(alert.id)
      setError(null)
      await updateAlertStatus(alert.id, status)
      setReloadVersion((current) => current + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update alert')
    } finally {
      setUpdatingId(null)
    }
  }

  const locationNames = new Map(
    locations.map((location) => [location.id, location.name]),
  )
  const zoneNames = new Map(zones.map((zone) => [zone.id, zone.name]))
  const visibleAlerts = sortAlerts(alerts, sortOrder)

  const emptyTitle =
    statusFilter === 'active'
      ? 'No active alerts'
      : statusFilter === 'resolved'
        ? 'No resolved alerts'
        : 'No alerts'

  return (
    <div className="mt-6 space-y-4">
      <div className="flex flex-col gap-1">
        <h4 className="subsection-title">Alerts</h4>
        <p className="text-muted">
          {live
            ? 'Live updates over WebSocket.'
            : 'Updating every 5 seconds until the live connection is back.'}
          {lastUpdated && <> Last updated {lastUpdated.toLocaleTimeString()}.</>}
        </p>
      </div>

      {/* Filters in one row above the list. */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <div className="text-sm">
          <span className="field-label">Status</span>
          <div
            role="group"
            aria-label="Alert status"
            className="inline-flex w-full rounded-md border border-slate-300 bg-white p-0.5"
          >
            {statusOptions.map((option) => (
              <button
                key={option.value}
                type="button"
                aria-pressed={statusFilter === option.value}
                onClick={() => setStatusFilter(option.value)}
                className={`flex-1 rounded px-3 py-1.5 font-medium ${
                  statusFilter === option.value
                    ? 'bg-slate-900 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </div>

        <label className="text-sm">
          <span className="field-label">Sort</span>
          <select
            value={sortOrder}
            onChange={(event) => setSortOrder(event.target.value as SortOrder)}
            className="field w-full"
          >
            <option value="newest">Newest first</option>
            <option value="severity">Most severe first</option>
          </select>
        </label>

        <label className="text-sm">
          <span className="field-label">Location</span>
          <select
            value={locationId}
            onChange={(event) => {
              setLocationId(event.target.value)
              setZoneId('')
            }}
            className="field w-full"
          >
            <option value="">All locations</option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
        </label>

        <label className="text-sm">
          <span className="field-label">Zone</span>
          <select
            value={zoneId}
            onChange={(event) => setZoneId(event.target.value)}
            disabled={!locationId}
            className="field w-full"
          >
            <option value="">All zones</option>
            {zones.map((zone) => (
              <option key={zone.id} value={zone.id}>
                {zone.name}
              </option>
            ))}
          </select>
        </label>
      </div>

      {error && <p className="alert-error">{error}</p>}

      {loading ? (
        <SkeletonList rows={3} label="Loading alerts…" rowClassName="h-14" />
      ) : visibleAlerts.length === 0 ? (
        <EmptyState title={emptyTitle}>
          Low moisture, failed commands and actuator errors appear here.
        </EmptyState>
      ) : (
        <ul
          className="panel max-h-96 divide-y divide-slate-100 overflow-y-auto"
          aria-label="Alerts"
        >
          {visibleAlerts.map((alert) => {
            const badge = severityBadge[alert.severity] ?? severityBadge.info
            const resolved = alert.status === 'resolved'

            return (
              <li
                key={alert.id}
                className={`flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between ${
                  resolved ? 'bg-slate-50/60' : ''
                }`}
              >
                <div className="flex min-w-0 items-start gap-3">
                  <span className={`badge capitalize ${badge.className}`}>
                    <span aria-hidden="true">{badge.icon}</span>
                    {alert.severity}
                  </span>

                  <div className="min-w-0">
                    <p
                      className={`text-sm font-medium ${
                        resolved ? 'text-slate-500 line-through' : 'text-slate-800'
                      }`}
                    >
                      {alert.message}
                    </p>

                    <p className="mt-0.5 text-xs text-slate-500">
                      {eventTypeLabels[alert.event_type] ?? alert.event_type}
                      {' · '}
                      {alert.location_id
                        ? (locationNames.get(alert.location_id) ?? 'Location')
                        : 'Unassigned'}
                      {alert.zone_id && zoneNames.get(alert.zone_id) && (
                        <> · {zoneNames.get(alert.zone_id)}</>
                      )}
                      {resolved && <> · Resolved</>}
                    </p>
                  </div>
                </div>

                <div className="flex items-center justify-between gap-3 sm:justify-end">
                  <time
                    dateTime={alert.created_at}
                    className="whitespace-nowrap text-xs text-slate-500"
                  >
                    {formatDate(alert.created_at)}
                  </time>

                  <button
                    type="button"
                    disabled={updatingId === alert.id}
                    onClick={() =>
                      changeStatus(alert, resolved ? 'active' : 'resolved')
                    }
                    className="btn btn-secondary btn-sm"
                  >
                    {updatingId === alert.id
                      ? 'Saving…'
                      : resolved
                        ? 'Reopen'
                        : 'Resolve'}
                  </button>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
