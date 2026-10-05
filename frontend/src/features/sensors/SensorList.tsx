import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import {
  createSensor,
  getDevices,
  updateDeviceSampling,
} from '../../services/api'

import type { DeviceDto } from '../../services/api'

type SamplingState = {
  sampling_interval_seconds: number
  tracking_enabled: boolean
}

export default function SensorList() {
  const [sensors, setSensors] = useState<DeviceDto[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [sensorType, setSensorType] =
    useState<'moisture' | 'light'>('moisture')

  const [displayName, setDisplayName] = useState('')
  const [creating, setCreating] = useState(false)

  const [sampling, setSampling] = useState<
    Record<string, SamplingState>
  >({})

  const [saving, setSaving] = useState<string | null>(null)
  const [saved, setSaved] = useState<string | null>(null)

  async function loadSensors() {
    try {
      setLoading(true)
      setError(null)

      const data = await getDevices(
        undefined,
        'sensor',
      )

      setSensors(data)

      const initialSampling: Record<
        string,
        SamplingState
      > = {}

      for (const sensor of data) {
        initialSampling[sensor.id] = {
          sampling_interval_seconds:
            sensor.sampling_interval_seconds,
          tracking_enabled:
            sensor.tracking_enabled,
        }
      }

      setSampling(initialSampling)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load sensors',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSensors()
  }, [])

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    try {
      setCreating(true)
      setError(null)

      await createSensor({
        type: sensorType,
        display_name:
          displayName.trim() || undefined,
      })

      setDisplayName('')

      await loadSensors()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to create sensor',
      )
    } finally {
      setCreating(false)
    }
  }

  function updateSamplingValue(
    sensorId: string,
    field:
      | 'sampling_interval_seconds'
      | 'tracking_enabled',
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

  async function handleSaveSampling(
    sensorId: string,
  ) {
    const settings = sampling[sensorId]

    if (!settings) {
      return
    }

    try {
      setSaving(sensorId)
      setError(null)
      setSaved(null)

      const result = await updateDeviceSampling(
        sensorId,
        {
          sampling_interval_seconds:
            settings.sampling_interval_seconds,
          tracking_enabled:
            settings.tracking_enabled,
        },
      )

      setSampling((current) => ({
        ...current,
        [sensorId]: {
          sampling_interval_seconds:
            result.sampling_interval_seconds,
          tracking_enabled:
            result.tracking_enabled,
        },
      }))

      setSaved(sensorId)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to save sampling settings',
      )
    } finally {
      setSaving(null)
    }
  }

  return (
    <div className="mt-6 space-y-6">
      <form
        onSubmit={handleSubmit}
        className="rounded-lg border bg-gray-50 p-4"
      >
        <h4 className="font-semibold">
          Add sensor
        </h4>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="text-sm">
            <span className="font-medium">
              Sensor type
            </span>

            <select
              value={sensorType}
              onChange={(event) =>
                setSensorType(
                  event.target.value as
                    | 'moisture'
                    | 'light',
                )
              }
              className="mt-1 block w-full rounded-md border px-3 py-2"
            >
              <option value="moisture">
                Moisture
              </option>

              <option value="light">
                Light
              </option>
            </select>
          </label>

          <label className="text-sm">
            <span className="font-medium">
              Display name
            </span>

            <input
              type="text"
              value={displayName}
              onChange={(event) =>
                setDisplayName(event.target.value)
              }
              placeholder="Optional"
              className="mt-1 block w-full rounded-md border px-3 py-2"
            />
          </label>
        </div>

        <button
          type="submit"
          disabled={creating}
          className="mt-4 rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {creating
            ? 'Creating...'
            : 'Create sensor'}
        </button>
      </form>

      {loading && (
        <p className="text-sm text-gray-500">
          Loading sensors...
        </p>
      )}

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {!loading &&
        !error &&
        sensors.length === 0 && (
          <p className="rounded-md bg-gray-50 p-4 text-sm text-gray-500">
            No sensors found.
          </p>
        )}

      {!loading && sensors.length > 0 && (
        <div className="space-y-3">
          {sensors.map((sensor) => {
            const settings = sampling[sensor.id]

            return (
              <article
                key={sensor.id}
                className="rounded-lg border bg-white p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h4 className="font-semibold">
                      {sensor.display_name}
                    </h4>

                    <p className="mt-1 text-sm text-gray-500">
                      Type: {sensor.device_type}
                    </p>
                  </div>
                </div>

                {settings && (
                  <div className="mt-4 rounded-lg bg-gray-50 p-4">
                    <h5 className="text-lg font-semibold">
                      Sampling settings
                    </h5>

                    <div className="mt-4 flex flex-wrap items-end gap-6">
                      <label className="text-sm">
                        <span className="block font-medium">
                          Interval (seconds)
                        </span>

                        <input
                          type="number"
                          min="5"
                          value={
                            settings.sampling_interval_seconds
                          }
                          onChange={(event) =>
                            updateSamplingValue(
                              sensor.id,
                              'sampling_interval_seconds',
                              Number(
                                event.target.value,
                              ),
                            )
                          }
                          className="mt-1 block w-48 rounded-md border px-3 py-2"
                        />
                      </label>

                      <label className="flex items-center gap-2 text-sm font-medium">
                        <input
                          type="checkbox"
                          checked={
                            settings.tracking_enabled
                          }
                          onChange={(event) =>
                            updateSamplingValue(
                              sensor.id,
                              'tracking_enabled',
                              event.target.checked,
                            )
                          }
                          className="h-5 w-5"
                        />

                        <span>
                          Tracking enabled
                        </span>
                      </label>
                    </div>

                    <button
                      type="button"
                      disabled={
                        saving === sensor.id
                      }
                      onClick={() =>
                        handleSaveSampling(
                          sensor.id,
                        )
                      }
                      className="mt-4 rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
                    >
                      {saving === sensor.id
                        ? 'Saving...'
                        : 'Save sampling settings'}
                    </button>

                    {saved === sensor.id && (
                      <p className="mt-2 text-sm text-green-600">
                        Sampling settings saved.
                      </p>
                    )}
                  </div>
                )}

                <pre className="mt-4 overflow-x-auto rounded-md bg-gray-50 p-3 text-xs text-gray-700">
                  {JSON.stringify(
                    sensor.default_config,
                    null,
                    2,
                  )}
                </pre>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}