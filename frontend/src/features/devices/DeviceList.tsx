import { useEffect, useState } from 'react'

import {
  getDevices,
  provisionDevices,
} from '../../services/api'
import type { DeviceDto } from '../../services/api'

type DeviceFamily = 'simulation' | 'edge'

type DeviceListProps = {
  family: DeviceFamily
}

export default function DeviceList({
  family,
}: DeviceListProps) {
  const [devices, setDevices] = useState<DeviceDto[]>([])
  const [loading, setLoading] = useState(true)
  const [provisioning, setProvisioning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadDevices() {
    try {
      setLoading(true)
      setError(null)

      const data = await getDevices(family)
      setDevices(data)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load devices',
      )
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDevices()
  }, [family])

  async function handleProvision() {
    try {
      setProvisioning(true)
      setError(null)

      const newDevices = await provisionDevices(family)

      setDevices((current) => [
        ...newDevices,
        ...current,
      ])
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to provision devices',
      )
    } finally {
      setProvisioning(false)
    }
  }

  return (
    <div className="mt-6 space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h4 className="font-semibold">
            {family === 'simulation'
              ? 'Simulation devices'
              : 'Edge devices'}
          </h4>

          <p className="mt-1 text-sm text-gray-500">
            Device family: {family}
          </p>
        </div>

        <button
          type="button"
          onClick={handleProvision}
          disabled={provisioning}
          className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
        >
          {provisioning
            ? 'Provisioning...'
            : 'Provision device family'}
        </button>
      </div>

      {loading && (
        <p className="text-sm text-gray-500">
          Loading devices...
        </p>
      )}

      {error && (
        <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {!loading && !error && devices.length === 0 && (
        <p className="rounded-md bg-gray-50 p-4 text-sm text-gray-500">
          No devices found for this family.
        </p>
      )}

      {!loading && devices.length > 0 && (
        <div className="space-y-3">
          {devices.map((device) => (
            <article
              key={device.id}
              className="rounded-lg border bg-white p-4"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h4 className="font-semibold">
                    {device.display_name}
                  </h4>

                  <p className="mt-1 text-sm text-gray-500">
                    Type: {device.device_type}
                  </p>

                  <div className="mt-2 flex flex-wrap gap-2">
                    <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700">
                      Role: {device.role}
                    </span>

                    <span className="rounded-full bg-gray-100 px-2 py-1 text-xs text-gray-700">
                      Family: {device.device_family}
                    </span>
                  </div>
                </div>
              </div>

              <pre className="mt-4 overflow-x-auto rounded-md bg-gray-50 p-3 text-xs text-gray-700">
                {JSON.stringify(
                  device.default_config,
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