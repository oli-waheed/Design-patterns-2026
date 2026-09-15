import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'

import {
  createSensor,
  getSensors,
} from '../../services/api'
import type { Sensor } from '../../services/api'

export default function SensorList() {
  const [sensors, setSensors] = useState<Sensor[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [sensorType, setSensorType] =
    useState<'moisture' | 'light'>('moisture')

  const [displayName, setDisplayName] = useState('')
  const [creating, setCreating] = useState(false)

  async function loadSensors() {
    try {
      setLoading(true)
      setError(null)

      const data = await getSensors()
      setSensors(data)
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

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    try {
      setCreating(true)
      setError(null)

      const sensor = await createSensor({
        type: sensorType,
        display_name: displayName.trim() || undefined,
      })

      setSensors((current) => [sensor, ...current])
      setDisplayName('')
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

  return (
    <div className="mt-6 space-y-6">
      <form
        onSubmit={handleSubmit}
        className="rounded-lg border bg-gray-50 p-4"
      >
        <h4 className="font-semibold">Add sensor</h4>

        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <label className="text-sm">
            <span className="font-medium">Sensor type</span>

            <select
              value={sensorType}
              onChange={(event) =>
                setSensorType(
                  event.target.value as 'moisture' | 'light',
                )
              }
              className="mt-1 block w-full rounded-md border px-3 py-2"
            >
              <option value="moisture">Moisture</option>
              <option value="light">Light</option>
            </select>
          </label>

          <label className="text-sm">
            <span className="font-medium">Display name</span>

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
          {creating ? 'Creating...' : 'Create sensor'}
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

      {!loading && !error && sensors.length === 0 && (
        <p className="rounded-md bg-gray-50 p-4 text-sm text-gray-500">
          No sensors found.
        </p>
      )}

      {!loading && sensors.length > 0 && (
        <div className="space-y-3">
          {sensors.map((sensor) => (
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

              <pre className="mt-4 overflow-x-auto rounded-md bg-gray-50 p-3 text-xs text-gray-700">
                {JSON.stringify(
                  sensor.default_config,
                  null,
                  2,
                )}
              </pre>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}