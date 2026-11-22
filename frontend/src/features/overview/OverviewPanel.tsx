
import { useCallback, useEffect, useRef, useState } from 'react'
import {
  getLocations,
  getLocationOverview,
  type LocationSummaryDto,
  type OverviewResponseDto,
} from '../../services/api'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonList } from '../../components/ui/Skeleton'
import { useRealtimeEvents, useRealtimeStatus } from '../../hooks/useRealtime'

// The overview counts as stale when it is older than this and no live
// frame has refreshed it.
const STALE_AFTER_MS = 60 * 1000

function formatAge(ms: number): string {
  const seconds = Math.max(0, Math.round(ms / 1000))

  if (seconds < 60) {
    return `${seconds} s ago`
  }

  const minutes = Math.round(seconds / 60)

  return minutes < 60 ? `${minutes} min ago` : `${Math.round(minutes / 60)} h ago`
}

export default function OverviewPanel() {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([])
  const [locationId, setLocationId] = useState('')
  const [overview, setOverview] = useState<OverviewResponseDto | null>(null)
  const [loadingLocations, setLoadingLocations] = useState(true)
  const [loading, setLoading] = useState(false)
  const [updatedAt, setUpdatedAt] = useState<number | null>(null)
  const [now, setNow] = useState(() => Date.now())

  const live = useRealtimeStatus() === 'connected'

  // Tick so "updated … ago" and the stale badge stay current.
  useEffect(() => {
    const id = window.setInterval(() => setNow(Date.now()), 5000)
    return () => window.clearInterval(id)
  }, [])
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadLocations() {
      try {
        setError('')
        const data = await getLocations()

        if (cancelled) return

        setLocations(data)
        setLocationId(data[0]?.id ?? '')
        setLoading(Boolean(data[0]))
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'Failed to load locations.',
          )
        }
      } finally {
        if (!cancelled) setLoadingLocations(false)
      }
    }

    void loadLocations()

    return () => {
      cancelled = true
    }
  }, [])

  const loadOverview = useCallback(
    async (selectedLocationId: string) => {
      if (!selectedLocationId) {
        setOverview(null)
        return
      }

      try {
        setLoading(true)
        setError('')

        const data = await getLocationOverview(selectedLocationId)
        setOverview(data)
        setUpdatedAt(Date.now())
        setNow(Date.now())
      } catch (err) {
        setOverview(null)
        setError(
          err instanceof Error
            ? err.message
            : 'Failed to load overview.',
        )
      } finally {
        setLoading(false)
      }
    },
    [],
  )

  // Load when the selected location changes. State is set only after the
  // request finishes; the select handler sets the loading flag.
  useEffect(() => {
    if (!locationId) {
      return
    }

    let cancelled = false

    getLocationOverview(locationId)
      .then((data) => {
        if (!cancelled) {
          setOverview(data)
          setUpdatedAt(Date.now())
          setNow(Date.now())
          setError('')
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setOverview(null)
          setError(
            err instanceof Error ? err.message : 'Failed to load overview.',
          )
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [locationId])

  function selectLocation(id: string) {
    setLocationId(id)
    setOverview(null)
    setLoading(Boolean(id))
  }

  // Live zone updates: when a reading.created or alert.created frame names
  // one of this overview's zones, quietly re-fetch the overview (at most
  // once per second) so its devices and latest readings stay current.
  const refreshTimer = useRef<number | null>(null)

  useEffect(
    () => () => {
      if (refreshTimer.current !== null) {
        window.clearTimeout(refreshTimer.current)
      }
    },
    [],
  )

  useRealtimeEvents((event) => {
    if (
      event.type !== 'reading.created' &&
      event.type !== 'alert.created'
    ) {
      return
    }

    const zoneId = (event.payload as { zone_id?: string | null }).zone_id

    if (
      !zoneId ||
      !overview ||
      !overview.zones.some((zone) => zone.id === zoneId) ||
      refreshTimer.current !== null
    ) {
      return
    }

    const currentLocationId = overview.location.id

    refreshTimer.current = window.setTimeout(() => {
      refreshTimer.current = null

      getLocationOverview(currentLocationId)
        .then((data) => {
          setOverview((current) =>
            current?.location.id === data.location.id ? data : current,
          )
          setUpdatedAt(Date.now())
          setNow(Date.now())
        })
        .catch(() => {
          // Keep the last overview; the Refresh button still works.
        })
    }, 1000)
  })

  function handleRefresh() {
    void loadOverview(locationId)
  }

  return (
    <section className="mt-6 space-y-5">
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-60 flex-1">
          <label
            htmlFor="overview-location"
            className="field-label"
          >
            Location
          </label>

          <select
            id="overview-location"
            value={locationId}
            onChange={(event) => selectLocation(event.target.value)}
            disabled={
              loadingLocations || locations.length === 0 || loading
            }
            className="field w-full"
          >
            <option value="">Select a location</option>

            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>
        </div>

        <button
          type="button"
          onClick={handleRefresh}
          disabled={!locationId || loading}
          className="btn btn-secondary"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {(loadingLocations || (loading && !overview)) && (
        <SkeletonList rows={3} label="Loading overview…" rowClassName="h-20" />
      )}

      {error && (
        <div
          role="alert"
          className="alert-error"
        >
          {error}
        </div>
      )}

      {!loadingLocations && locations.length === 0 && (
        <EmptyState title="No locations yet">
          Create a location under Configuration to see its overview.
        </EmptyState>
      )}

      {overview && (
        <div className="space-y-5">
          <div className="panel p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h4 className="section-title">{overview.location.name}</h4>

              {updatedAt !== null &&
                (now - updatedAt > STALE_AFTER_MS ? (
                  <span className="badge badge-warn" title="Press Refresh to reload">
                    <span aria-hidden="true">⚠</span>
                    Stale · updated {formatAge(now - updatedAt)}
                  </span>
                ) : (
                  <span className="badge badge-ok">
                    <span aria-hidden="true">●</span>
                    {live ? 'Live' : 'Fresh'} · updated {formatAge(now - updatedAt)}
                  </span>
                ))}
            </div>

            <p className="mt-1 break-all text-xs text-slate-500">
              {overview.location.id}
            </p>

            <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
              <div>
                <dt className="text-sm text-slate-500">Sensors</dt>
                <dd className="text-2xl font-semibold">
                  {overview.device_counts.sensor}
                </dd>
              </div>

              <div>
                <dt className="text-sm text-slate-500">Actuators</dt>
                <dd className="text-2xl font-semibold">
                  {overview.device_counts.actuator}
                </dd>
              </div>

              <div>
                <dt className="text-sm text-slate-500">Zones</dt>
                <dd className="text-2xl font-semibold">
                  {overview.zones.length}
                </dd>
              </div>
            </dl>
          </div>

          <div className="panel p-4">
            <h4 className="font-semibold">Automation</h4>

            <p className="mt-2 text-sm">
              Strategy:{' '}
              <span className="font-medium">
                {overview.strategy_key ?? 'No strategy saved'}
              </span>
            </p>

            {overview.last_recommendation == null ? (
              <p className="mt-2 text-sm text-slate-500">
                No recommendation available.
              </p>
            ) : (
              <pre className="mt-3 overflow-x-auto rounded-lg bg-slate-50 p-3 text-xs">
                {JSON.stringify(
                  overview.last_recommendation,
                  null,
                  2,
                )}
              </pre>
            )}
          </div>

          <div className="space-y-4">
            <h4 className="font-semibold">Zones and devices</h4>

            {overview.zones.map((zone) => (
              <article
                key={zone.id}
                className="panel p-4"
              >
                <h5 className="font-semibold">{zone.name}</h5>

                <p className="mt-1 text-sm text-slate-600">
                  Moisture thresholds:{' '}
                  {zone.moisture_threshold_low} –{' '}
                  {zone.moisture_threshold_high}
                </p>

                {zone.devices.length === 0 ? (
                  <p className="mt-3 text-sm text-slate-500">
                    No devices assigned to this zone.
                  </p>
                ) : (
                  <div className="mt-4 space-y-3">
                    {zone.devices.map((device) => {
                      const reading = zone.latest_readings.find(
                        (item) => item.device_id === device.id,
                      )

                      return (
                        <div
                          key={device.id}
                          className="rounded-lg bg-slate-50 p-3"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-medium">
                              {device.display_name || device.device_type}
                            </p>

                            <span className="rounded-full bg-white px-2 py-1 text-xs">
                              {device.role}
                            </span>
                          </div>

                          <p className="mt-1 text-xs text-slate-500">
                            {device.device_type}
                          </p>

                          {reading ? (
                            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                              <div>
                                <dt className="text-slate-500">
                                  Latest reading
                                </dt>
                                <dd className="font-medium">
                                  {reading.value} {reading.unit}
                                </dd>
                              </div>

                              <div>
                                <dt className="text-slate-500">
                                  Recorded at
                                </dt>
                                <dd>
                                  {new Date(
                                    reading.recorded_at,
                                  ).toLocaleString()}
                                </dd>
                              </div>

                              <div>
                                <dt className="text-slate-500">
                                  Tracking
                                </dt>
                                <dd>
                                  {reading.tracking_enabled
                                    ? 'Enabled'
                                    : 'Disabled'}
                                </dd>
                              </div>

                              <div>
                                <dt className="text-slate-500">
                                  Sampling interval
                                </dt>
                                <dd>
                                  {reading.sampling_interval_seconds}{' '}
                                  seconds
                                </dd>
                              </div>
                            </dl>
                          ) : (
                            <p className="mt-3 text-sm text-slate-500">
                              No reading available.
                            </p>
                          )}
                        </div>
                      )
                    })}
                  </div>
                )}
              </article>
            ))}
          </div>
        </div>
      )}
    </section>
  )
}
