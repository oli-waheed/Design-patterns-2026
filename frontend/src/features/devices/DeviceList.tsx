import { useEffect, useState } from 'react'

import {
  assignDeviceToZone,
  getDevices,
  getLocation,
  getLocations,
  provisionDevices,
} from '../../services/api'

import type {
  DeviceDto,
  LocationResponseDto,
  LocationSummaryDto,
} from '../../services/api'

type DeviceFamily = 'simulation' | 'edge'

type DeviceListProps = {
  family: DeviceFamily
}

export default function DeviceList({
  family,
}: DeviceListProps) {
  const [devices, setDevices] = useState<DeviceDto[]>([])
  const [locations, setLocations] = useState<
    LocationResponseDto[]
  >([])

  const [loading, setLoading] = useState(true)
  const [provisioning, setProvisioning] =
    useState(false)
  const [error, setError] = useState<string | null>(
    null,
  )

  const [assigningDeviceId, setAssigningDeviceId] =
    useState<string | null>(null)

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

  async function loadLocations() {
    try {
      const summaries: LocationSummaryDto[] =
        await getLocations()

      const fullLocations =
        await Promise.all(
          summaries.map((location) =>
            getLocation(location.id),
          ),
        )

      setLocations(fullLocations)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load locations',
      )
    }
  }

  useEffect(() => {
    loadDevices()
    loadLocations()
  }, [family])

  async function handleProvision() {
    try {
      setProvisioning(true)
      setError(null)

      const newDevices =
        await provisionDevices(family)

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

  async function handleAssignment(
    deviceId: string,
    value: string,
  ) {
    try {
      setAssigningDeviceId(deviceId)
      setError(null)

      if (!value) {
        await assignDeviceToZone(
          deviceId,
          null,
        )
      } else {
        const [locationId, zoneId] =
          value.split(':')

        if (!locationId || !zoneId) {
          throw new Error(
            'Invalid location or zone selection.',
          )
        }

        await assignDeviceToZone(
          deviceId,
          zoneId,
        )
      }

      await loadDevices()
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to assign device',
      )
    } finally {
      setAssigningDeviceId(null)
    }
  }

  function getAssignmentValue(
    device: DeviceDto,
  ): string {
    if (
      !device.location_id ||
      !device.zone_id
    ) {
      return ''
    }

    return `${device.location_id}:${device.zone_id}`
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

      {!loading &&
        !error &&
        devices.length === 0 && (
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

              <div className="mt-4">
                <label
                  htmlFor={`zone-${device.id}`}
                  className="mb-2 block text-sm font-medium"
                >
                  Location / Zone
                </label>

                <select
                  id={`zone-${device.id}`}
                  value={getAssignmentValue(
                    device,
                  )}
                  onChange={(event) =>
                    handleAssignment(
                      device.id,
                      event.target.value,
                    )
                  }
                  disabled={
                    assigningDeviceId ===
                    device.id
                  }
                  className="w-full rounded-md border px-3 py-2 text-sm"
                >
                  <option value="">
                    Unassigned
                  </option>

                  {locations.map((location) =>
                    location.zones.map((zone) => (
                      <option
                        key={zone.id}
                        value={`${location.location.id}:${zone.id}`}
                      >
                        {location.location.name} —{' '}
                        {zone.name}
                      </option>
                    )),
                  )}
                </select>

                {assigningDeviceId ===
                  device.id && (
                  <p className="mt-1 text-xs text-gray-500">
                    Saving assignment...
                  </p>
                )}
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