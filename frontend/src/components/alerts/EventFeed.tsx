import { useEffect, useState } from 'react'

import {
  getAlerts,
  getLocation,
  getLocations,
  type AlertDto,
  type AlertSeverity,
  type LocationSummaryDto,
  type ZoneDto,
} from '../../services/api'
import { useRealtimeEvents, useRealtimeStatus } from '../../hooks/useRealtime'
import type { AlertCreatedPayload } from '../../services/realtime'

// Phase 11 poll. Phase 12: only used while the WebSocket is down.
const POLL_INTERVAL_MS = 5000

const severityStyles: Record<AlertSeverity, string> = {
  info: 'bg-blue-100 text-blue-700',
  warning: 'bg-amber-100 text-amber-800',
  critical: 'bg-red-100 text-red-700',
}

const eventTypeLabels: Record<string, string> = {
  'threshold.crossed': 'Threshold crossed',
  'command.failed': 'Command failed',
  'state.changed': 'State changed',
}

function formatDate(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleString()
}

export default function EventFeed() {
  const [alerts, setAlerts] = useState<AlertDto[]>([])
  const [locations, setLocations] = useState<LocationSummaryDto[]>([])
  const [zones, setZones] = useState<ZoneDto[]>([])

  const [locationId, setLocationId] = useState('')
  const [zoneId, setZoneId] = useState('')

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)

  // Bumped when an alert.created frame matches the current filter, which
  // re-runs the load effect below.
  const [pushVersion, setPushVersion] = useState(0)

  const realtimeStatus = useRealtimeStatus()
  const live = realtimeStatus === 'connected'

  useRealtimeEvents((event) => {
    if (event.type !== 'alert.created') {
      return
    }

    const alert = event.payload as AlertCreatedPayload

    if (locationId && alert.location_id !== locationId) {
      return
    }

    if (zoneId && alert.zone_id !== zoneId) {
      return
    }

    setPushVersion((current) => current + 1)
  })

  // Load the location list once for the filter.
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

  // Load zones whenever the selected location changes.
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

  // Poll alerts every 5 seconds for the current filter.
  useEffect(() => {
    let cancelled = false

    async function loadAlerts() {
      try {
        const data = await getAlerts({
          status: 'active',
          locationId: locationId || undefined,
          zoneId: zoneId || undefined,
          limit: 50,
        })

        if (!cancelled) {
          setAlerts(data)
          setError(null)
          setLastUpdated(new Date())
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to load alerts',
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadAlerts()

    // Prefer the WebSocket. Poll every 5 s only while it is not connected.
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
  }, [locationId, zoneId, live, pushVersion])

  function handleLocationChange(value: string) {
    setLocationId(value)
    setZoneId('')
  }

  const locationNames = new Map(
    locations.map((location) => [location.id, location.name]),
  )
  const zoneNames = new Map(zones.map((zone) => [zone.id, zone.name]))

  return (
    <div className="mt-6 space-y-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h4 className="font-semibold">Alerts</h4>

          <p className="mt-1 text-sm text-gray-500">
            Active alerts, newest first.{' '}
            {live
              ? 'Live updates over WebSocket.'
              : 'Updating every 5 seconds until the live connection is back.'}
            {lastUpdated && (
              <> Last updated {lastUpdated.toLocaleTimeString()}.</>
            )}
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row">
          <label className="text-sm">
            <span className="mb-1 block font-medium text-gray-700">
              Location
            </span>

            <select
              value={locationId}
              onChange={(event) => handleLocationChange(event.target.value)}
              className="w-full rounded-md border px-3 py-2 text-sm sm:w-48"
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
            <span className="mb-1 block font-medium text-gray-700">
              Zone
            </span>

            <select
              value={zoneId}
              onChange={(event) => setZoneId(event.target.value)}
              disabled={!locationId}
              className="w-full rounded-md border px-3 py-2 text-sm disabled:bg-gray-100 disabled:text-gray-400 sm:w-48"
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
      </div>

      {loading && (
        <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
          Loading alerts...
        </p>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {!loading && !error && alerts.length === 0 && (
        <div className="rounded-lg border border-dashed bg-gray-50 p-6 text-center">
          <p className="font-medium text-gray-700">No active alerts.</p>

          <p className="mt-2 text-sm text-gray-500">
            Low moisture, failed commands, and actuator errors will appear
            here.
          </p>
        </div>
      )}

      {!loading && alerts.length > 0 && (
        <ul className="divide-y divide-gray-200 rounded-lg border bg-white">
          {alerts.map((alert) => (
            <li
              key={alert.id}
              className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex items-start gap-3">
                <span
                  className={`inline-flex shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold capitalize ${
                    severityStyles[alert.severity] ??
                    'bg-gray-100 text-gray-700'
                  }`}
                >
                  {alert.severity}
                </span>

                <div>
                  <p className="text-sm font-medium text-gray-800">
                    {alert.message}
                  </p>

                  <p className="mt-0.5 text-xs text-gray-500">
                    {eventTypeLabels[alert.event_type] ?? alert.event_type}
                    {' · '}
                    {alert.location_id
                      ? (locationNames.get(alert.location_id) ??
                        'Location')
                      : 'Unassigned'}
                    {alert.zone_id && zoneNames.get(alert.zone_id) && (
                      <> · {zoneNames.get(alert.zone_id)}</>
                    )}
                  </p>
                </div>
              </div>

              <time
                dateTime={alert.created_at}
                className="whitespace-nowrap text-xs text-gray-500"
              >
                {formatDate(alert.created_at)}
              </time>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
