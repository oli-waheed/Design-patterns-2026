
import { useCallback, useEffect, useState } from 'react'
import {
  getLocations,
  getLocationOverview,
  type LocationSummaryDto,
  type OverviewResponseDto,
} from '../../services/api'

export default function OverviewPanel() {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([])
  const [locationId, setLocationId] = useState('')
  const [overview, setOverview] = useState<OverviewResponseDto | null>(null)
  const [loadingLocations, setLoadingLocations] = useState(true)
  const [loading, setLoading] = useState(false)
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

  useEffect(() => {
    if (locationId) {
      void loadOverview(locationId)
    } else {
      setOverview(null)
    }
  }, [locationId, loadOverview])

  function handleRefresh() {
    void loadOverview(locationId)
  }

  return (
    <section className="mt-6 space-y-5">
      <div className="flex flex-wrap items-end gap-3">
        <div className="min-w-60 flex-1">
          <label
            htmlFor="overview-location"
            className="mb-2 block text-sm font-medium"
          >
            Location
          </label>

          <select
            id="overview-location"
            value={locationId}
            onChange={(event) => setLocationId(event.target.value)}
            disabled={
              loadingLocations || locations.length === 0 || loading
            }
            className="w-full rounded-lg border px-3 py-2"
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
          className="rounded-lg border px-4 py-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {loadingLocations && (
        <p className="text-sm text-gray-500">Loading locations...</p>
      )}

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {loading && !overview && (
        <p className="text-sm text-gray-500">Loading overview...</p>
      )}

      {!loadingLocations && locations.length === 0 && (
        <p className="rounded-lg border p-4 text-sm text-gray-600">
          Create a location before viewing its overview.
        </p>
      )}

      {overview && (
        <div className="space-y-5">
          <div className="rounded-lg border p-4">
            <h4 className="text-lg font-semibold">
              {overview.location.name}
            </h4>

            <p className="mt-1 break-all text-xs text-gray-500">
              {overview.location.id}
            </p>

            <dl className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-3">
              <div>
                <dt className="text-sm text-gray-500">Sensors</dt>
                <dd className="text-2xl font-semibold">
                  {overview.device_counts.sensor}
                </dd>
              </div>

              <div>
                <dt className="text-sm text-gray-500">Actuators</dt>
                <dd className="text-2xl font-semibold">
                  {overview.device_counts.actuator}
                </dd>
              </div>

              <div>
                <dt className="text-sm text-gray-500">Zones</dt>
                <dd className="text-2xl font-semibold">
                  {overview.zones.length}
                </dd>
              </div>
            </dl>
          </div>

          <div className="rounded-lg border p-4">
            <h4 className="font-semibold">Automation</h4>

            <p className="mt-2 text-sm">
              Strategy:{' '}
              <span className="font-medium">
                {overview.strategy_key ?? 'No strategy saved'}
              </span>
            </p>

            {overview.last_recommendation == null ? (
              <p className="mt-2 text-sm text-gray-500">
                No recommendation available.
              </p>
            ) : (
              <pre className="mt-3 overflow-x-auto rounded-lg bg-gray-50 p-3 text-xs">
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
                className="rounded-lg border p-4"
              >
                <h5 className="font-semibold">{zone.name}</h5>

                <p className="mt-1 text-sm text-gray-600">
                  Moisture thresholds:{' '}
                  {zone.moisture_threshold_low} –{' '}
                  {zone.moisture_threshold_high}
                </p>

                {zone.devices.length === 0 ? (
                  <p className="mt-3 text-sm text-gray-500">
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
                          className="rounded-lg bg-gray-50 p-3"
                        >
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <p className="font-medium">
                              {device.display_name || device.device_type}
                            </p>

                            <span className="rounded-full bg-white px-2 py-1 text-xs">
                              {device.role}
                            </span>
                          </div>

                          <p className="mt-1 text-xs text-gray-500">
                            {device.device_type}
                          </p>

                          {reading ? (
                            <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
                              <div>
                                <dt className="text-gray-500">
                                  Latest reading
                                </dt>
                                <dd className="font-medium">
                                  {reading.value} {reading.unit}
                                </dd>
                              </div>

                              <div>
                                <dt className="text-gray-500">
                                  Recorded at
                                </dt>
                                <dd>
                                  {new Date(
                                    reading.recorded_at,
                                  ).toLocaleString()}
                                </dd>
                              </div>

                              <div>
                                <dt className="text-gray-500">
                                  Tracking
                                </dt>
                                <dd>
                                  {reading.tracking_enabled
                                    ? 'Enabled'
                                    : 'Disabled'}
                                </dd>
                              </div>

                              <div>
                                <dt className="text-gray-500">
                                  Sampling interval
                                </dt>
                                <dd>
                                  {reading.sampling_interval_seconds}{' '}
                                  seconds
                                </dd>
                              </div>
                            </dl>
                          ) : (
                            <p className="mt-3 text-sm text-gray-500">
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
