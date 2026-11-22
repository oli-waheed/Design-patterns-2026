import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import EmptyState from '../../components/ui/EmptyState'
import { SkeletonList } from '../../components/ui/Skeleton'
import Sparkline from '../../components/ui/Sparkline'
import { useRealtimeEvents, useRealtimeStatus } from '../../hooks/useRealtime'
import {
  createSensor,
  getDevices,
  getSensorReadings,
  readSensorNow,
  updateDeviceSampling,
} from '../../services/api'
import type { DeviceDto, ReadingDto } from '../../services/api'
import type { ReadingCreatedPayload } from '../../services/realtime'

// Phase 5 readings poll. Phase 12: only used while the WebSocket is down.
const READINGS_POLL_MS = 5000

// Readings kept per card for the sparkline.
const TREND_POINTS = 20

type SamplingState = {
  sampling_interval_seconds: number
  tracking_enabled: boolean
}

function formatTime(value: string): string {
  const date = new Date(value)

  return Number.isNaN(date.getTime())
    ? value
    : date.toLocaleTimeString()
}

function formatValue(reading: ReadingDto): string {
  const digits = reading.unit === 'vwc' ? 3 : 0

  return `${reading.value.toFixed(digits)} ${reading.unit}`
}

/** Merge readings into one device's history: unique, oldest first, capped. */
function mergeHistory(
  current: ReadingDto[],
  incoming: ReadingDto[],
): ReadingDto[] {
  const byTime = new Map<string, ReadingDto>()

  for (const reading of [...current, ...incoming]) {
    byTime.set(reading.recorded_at, reading)
  }

  return [...byTime.values()]
    .sort(
      (a, b) =>
        new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime(),
    )
    .slice(-TREND_POINTS)
}

export default function SensorList() {
  const [sensors, setSensors] = useState<DeviceDto[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [reloadKey, setReloadKey] = useState(0)

  const [sensorType, setSensorType] =
    useState<'moisture' | 'light'>('moisture')
  const [displayName, setDisplayName] = useState('')
  const [creating, setCreating] = useState(false)

  const [sampling, setSampling] = useState<Record<string, SamplingState>>({})
  const [saving, setSaving] = useState<string | null>(null)
  const [saved, setSaved] = useState<string | null>(null)

  // Recent readings per device, oldest first (last one = latest value).
  const [history, setHistory] = useState<Record<string, ReadingDto[]>>({})
  const [reading, setReading] = useState<string | null>(null)

  const realtimeStatus = useRealtimeStatus()
  const live = realtimeStatus === 'connected'

  function addReadings(deviceId: string, readings: ReadingDto[]) {
    setHistory((current) => ({
      ...current,
      [deviceId]: mergeHistory(current[deviceId] ?? [], readings),
    }))
  }

  // Load sensors (again after creating one).
  useEffect(() => {
    let cancelled = false

    getDevices(undefined, 'sensor')
      .then((data) => {
        if (cancelled) {
          return
        }

        setSensors(data)
        setSampling(
          Object.fromEntries(
            data.map((sensor) => [
              sensor.id,
              {
                sampling_interval_seconds: sensor.sampling_interval_seconds,
                tracking_enabled: sensor.tracking_enabled,
              },
            ]),
          ),
        )
        setError(null)
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load sensors')
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
  }, [reloadKey])

  // Live updates: apply reading.created frames in place.
  useRealtimeEvents((event) => {
    if (event.type !== 'reading.created') {
      return
    }

    const payload = event.payload as ReadingCreatedPayload

    addReadings(payload.device_id, [
      {
        device_id: payload.device_id,
        value: payload.value,
        unit: payload.unit,
        source: payload.source,
        recorded_at: payload.recorded_at,
      },
    ])
  })

  const sensorIds = sensors.map((sensor) => sensor.id).join(',')

  // Recent stored readings for every card. While the socket is connected
  // this runs once; while it is down it repeats every 5 s (Phase 5 poll as
  // the documented fallback).
  useEffect(() => {
    const ids = sensorIds ? sensorIds.split(',') : []

    if (ids.length === 0) {
      return
    }

    let cancelled = false

    async function loadRecent() {
      const results = await Promise.all(
        ids.map((id) =>
          getSensorReadings(id, TREND_POINTS)
            .then((rows) => [id, rows] as const)
            .catch(() => [id, [] as ReadingDto[]] as const),
        ),
      )

      if (!cancelled) {
        results.forEach(([id, rows]) => addReadings(id, rows))
      }
    }

    void loadRecent()

    if (live) {
      return () => {
        cancelled = true
      }
    }

    const intervalId = window.setInterval(loadRecent, READINGS_POLL_MS)

    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [sensorIds, live])

  async function handleReadNow(sensorId: string) {
    try {
      setReading(sensorId)
      setError(null)

      const result = await readSensorNow(sensorId)
      addReadings(sensorId, [result])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to read sensor')
    } finally {
      setReading(null)
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    try {
      setCreating(true)
      setError(null)

      await createSensor({
        type: sensorType,
        display_name: displayName.trim() || undefined,
      })

      setDisplayName('')
      setReloadKey((current) => current + 1)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create sensor')
    } finally {
      setCreating(false)
    }
  }

  function updateSamplingValue(
    sensorId: string,
    field: keyof SamplingState,
    value: number | boolean,
  ) {
    setSampling((current) => ({
      ...current,
      [sensorId]: {
        ...current[sensorId],
        [field]: value,
      },
    }))

    setSaved(null)
  }

  async function handleSaveSampling(sensorId: string) {
    const settings = sampling[sensorId]

    if (!settings) {
      return
    }

    try {
      setSaving(sensorId)
      setError(null)
      setSaved(null)

      const result = await updateDeviceSampling(sensorId, settings)

      setSampling((current) => ({
        ...current,
        [sensorId]: {
          sampling_interval_seconds: result.sampling_interval_seconds,
          tracking_enabled: result.tracking_enabled,
        },
      }))
      setSensors((current) =>
        current.map((sensor) =>
          sensor.id === sensorId
            ? { ...sensor, tracking_enabled: result.tracking_enabled }
            : sensor,
        ),
      )

      setSaved(sensorId)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to save sampling settings',
      )
    } finally {
      setSaving(null)
    }
  }

  return (
    <div className="mt-6 space-y-6">
      <form
        onSubmit={handleSubmit}
        className="panel-muted flex flex-col gap-3 p-4 sm:flex-row sm:items-end"
      >
        <label className="text-sm sm:w-40">
          <span className="field-label">Sensor type</span>
          <select
            value={sensorType}
            onChange={(event) =>
              setSensorType(event.target.value as 'moisture' | 'light')
            }
            className="field w-full"
          >
            <option value="moisture">Moisture</option>
            <option value="light">Light</option>
          </select>
        </label>

        <label className="flex-1 text-sm">
          <span className="field-label">Display name</span>
          <input
            type="text"
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            placeholder="Optional"
            className="field w-full"
          />
        </label>

        <button type="submit" disabled={creating} className="btn btn-primary">
          {creating ? 'Creating…' : 'Add sensor'}
        </button>
      </form>

      {error && <p className="alert-error">{error}</p>}

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <SkeletonList rows={1} label="Loading sensors…" rowClassName="h-56" />
          <SkeletonList rows={1} label="Loading sensors…" rowClassName="h-56" />
          <SkeletonList rows={1} label="Loading sensors…" rowClassName="h-56" />
        </div>
      ) : sensors.length === 0 ? (
        <EmptyState title="No sensors yet">
          Add a sensor above, or provision a device family under Devices.
        </EmptyState>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {sensors.map((sensor) => {
            const settings = sampling[sensor.id]
            const readings = history[sensor.id] ?? []
            const latest = readings[readings.length - 1]

            return (
              <article
                key={sensor.id}
                className="panel flex min-w-0 flex-col p-4"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h4 className="subsection-title truncate">
                      {sensor.display_name}
                    </h4>
                    <p className="mt-0.5 text-xs text-slate-500">
                      {sensor.device_type.replace('_', ' ')} ·{' '}
                      {String(sensor.default_config.protocol ?? 'simulation')}
                    </p>
                  </div>

                  <button
                    type="button"
                    onClick={() => handleReadNow(sensor.id)}
                    disabled={reading === sensor.id}
                    className="btn btn-secondary btn-sm shrink-0"
                  >
                    {reading === sensor.id ? 'Reading…' : 'Read now'}
                  </button>
                </div>

                <div
                  className="panel-muted mt-4 px-4 py-3"
                  data-testid={`latest-reading-${sensor.id}`}
                >
                  {latest ? (
                    <div className="flex items-end justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-2xl font-semibold tabular-nums text-slate-900">
                          {formatValue(latest)}
                        </p>
                        <p className="mt-0.5 text-xs text-slate-500">
                          {formatTime(latest.recorded_at)} · {latest.source}
                        </p>
                      </div>

                      <Sparkline
                        values={readings.map((item) => item.value)}
                        label={`Last ${readings.length} readings of ${sensor.display_name}`}
                      />
                    </div>
                  ) : (
                    <p className="text-sm text-slate-500">No readings yet.</p>
                  )}

                  <p className="mt-2 text-xs">
                    {!sensor.tracking_enabled ? (
                      <span className="badge badge-neutral">Tracking off</span>
                    ) : live ? (
                      <span className="badge badge-ok">Live</span>
                    ) : (
                      <span className="badge badge-warn">Polling every 5 s</span>
                    )}
                  </p>
                </div>

                {settings && (
                  <div className="mt-4 space-y-3">
                    <div className="flex flex-wrap items-end gap-4">
                      <label className="text-sm">
                        <span className="field-label">Interval (s)</span>
                        <input
                          type="number"
                          min="5"
                          value={settings.sampling_interval_seconds}
                          onChange={(event) =>
                            updateSamplingValue(
                              sensor.id,
                              'sampling_interval_seconds',
                              Number(event.target.value),
                            )
                          }
                          className="field w-28"
                        />
                      </label>

                      <label className="flex items-center gap-2 pb-2 text-sm font-medium text-slate-700">
                        <input
                          type="checkbox"
                          checked={settings.tracking_enabled}
                          onChange={(event) =>
                            updateSamplingValue(
                              sensor.id,
                              'tracking_enabled',
                              event.target.checked,
                            )
                          }
                          className="h-4 w-4 rounded border-slate-300"
                        />
                        Tracking
                      </label>
                    </div>

                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        disabled={saving === sensor.id}
                        onClick={() => handleSaveSampling(sensor.id)}
                        className="btn btn-secondary btn-sm"
                      >
                        {saving === sensor.id ? 'Saving…' : 'Save sampling'}
                      </button>

                      {saved === sensor.id && (
                        <span className="text-sm text-ok-ink">Saved.</span>
                      )}
                    </div>
                  </div>
                )}

                <details className="mt-4 text-xs text-slate-500">
                  <summary className="cursor-pointer select-none hover:text-slate-700">
                    Device configuration
                  </summary>
                  <pre className="panel-muted mt-2 overflow-x-auto p-3 text-slate-700">
                    {JSON.stringify(sensor.default_config, null, 2)}
                  </pre>
                </details>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
