
import { useEffect, useState } from 'react'

import EmptyState from '../../components/ui/EmptyState'
import { SkeletonList } from '../../components/ui/Skeleton'

import {
  assignDeviceToZone,
  getDevices,
  getLocation,
  getLocations,
  provisionDevices,
} from '../../services/api'

import {
  getActuatorState,
} from '../../services/actuatorApi'

import type {
  ActuatorStateDto,
  ActuatorState,
} from '../../services/actuatorApi'

import type {
  DeviceDto,
  LocationResponseDto,
} from '../../services/api'

type DeviceFamily = 'simulation' | 'edge'

type DeviceListProps = {
  family: DeviceFamily
}

const stateStyles: Record<ActuatorState, string> = {
  off: 'bg-slate-100 text-slate-700',
  idle: 'bg-slate-100 text-slate-700',
  running: 'bg-emerald-100 text-emerald-700',
  error: 'bg-red-100 text-red-700',
  maintenance: 'bg-amber-100 text-amber-800',
}

async function fetchDevicesWithStates(family: 'simulation' | 'edge') {
  const devices = await getDevices(family)

  const stateResults = await Promise.all(
    devices
      .filter((device) => device.role === 'actuator')
      .map(async (device) => {
        try {
          return [device.id, await getActuatorState(device.id)] as const
        } catch {
          return null
        }
      }),
  )

  const states: Record<string, ActuatorStateDto> = {}

  stateResults.forEach((result) => {
    if (result) {
      states[result[0]] = result[1]
    }
  })

  return { devices, states }
}

async function fetchFullLocations() {
  const summaries = await getLocations()

  return Promise.all(summaries.map((location) => getLocation(location.id)))
}

export default function DeviceList({
  family,
}: DeviceListProps) {
  const [devices, setDevices] = useState<DeviceDto[]>([])
  const [locations, setLocations] = useState<LocationResponseDto[]>([])
  const [actuatorStates, setActuatorStates] = useState<
    Record<string, ActuatorStateDto>
  >({})

  const [loading, setLoading] = useState(true)
  const [provisioning, setProvisioning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [assigningDeviceId, setAssigningDeviceId] =
    useState<string | null>(null)

  async function loadDevices() {
    try {
      setLoading(true)
      setError(null)

      const data = await getDevices(family)
      setDevices(data)

      const actuators = data.filter(
        (device) => device.role === 'actuator',
      )

      const stateResults = await Promise.all(
        actuators.map(async (device) => {
          try {
            const state = await getActuatorState(device.id)
            return [device.id, state] as const
          } catch {
            return null
          }
        }),
      )

      const stateMap: Record<string, ActuatorStateDto> = {}

      stateResults.forEach((result) => {
        if (result) {
          stateMap[result[0]] = result[1]
        }
      })

      setActuatorStates(stateMap)
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

  // Initial load and family change: state is set only after the requests
  // finish (the button handlers keep using loadDevices).
  useEffect(() => {
    let cancelled = false

    Promise.all([fetchDevicesWithStates(family), fetchFullLocations()])
      .then(([deviceData, locationData]) => {
        if (!cancelled) {
          setDevices(deviceData.devices)
          setActuatorStates(deviceData.states)
          setLocations(locationData)
          setError(null)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load devices')
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
  }, [family])

  async function handleProvision() {
    try {
      setProvisioning(true)
      setError(null)

      await provisionDevices(family)
      await loadDevices()
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
        await assignDeviceToZone(deviceId, null)
      } else {
        const [locationId, zoneId] = value.split(':')

        if (!locationId || !zoneId) {
          throw new Error(
            'Invalid location or zone selection.',
          )
        }

        await assignDeviceToZone(deviceId, zoneId)
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

  function getAssignmentValue(device: DeviceDto): string {
    if (!device.location_id || !device.zone_id) {
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

          <p className="mt-1 text-sm text-slate-500">
            Device family: {family}
          </p>
        </div>

        <button
          type="button"
          onClick={handleProvision}
          disabled={provisioning}
          className="btn btn-primary"
        >
          {provisioning
            ? 'Provisioning...'
            : 'Provision device family'}
        </button>
      </div>

      {loading && (
        <SkeletonList rows={3} label="Loading devices…" rowClassName="h-16" />
      )}

      {error && (
        <p className="alert-error">
          {error}
        </p>
      )}

      {!loading && !error && devices.length === 0 && (
        <EmptyState title="No devices in this family">
          Use “Provision” to create a demo device set.
        </EmptyState>
      )}

      {!loading && devices.length > 0 && (
        <div className="space-y-3">
          {devices.map((device) => {
            const actuatorState =
              actuatorStates[device.id]

            return (
              <article
                key={device.id}
                className="panel p-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <h4 className="font-semibold">
                      {device.display_name}
                    </h4>

                    <p className="mt-1 text-sm text-slate-500">
                      Type: {device.device_type}
                    </p>

                    <div className="mt-2 flex flex-wrap gap-2">
                      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700">
                        Role: {device.role}
                      </span>

                      <span className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-700">
                        Family: {device.device_family}
                      </span>
                    </div>
                  </div>
                </div>

                {device.role === 'actuator' && (
                  <div className="mt-4 rounded-md bg-slate-50 p-3">
                    <p className="text-sm font-medium text-slate-700">
                      Actuator state
                    </p>

                    {actuatorState ? (
                      <>
                        <span
                          className={`mt-2 inline-block rounded-full px-3 py-1 text-xs font-semibold capitalize ${
                            stateStyles[actuatorState.state]
                          }`}
                        >
                          {actuatorState.state}
                        </span>

                        <div className="mt-3">
                          <p className="text-xs font-medium text-slate-600">
                            Allowed commands
                          </p>

                          <div className="mt-1 flex flex-wrap gap-2">
                            {actuatorState.allowed_commands.map(
                              (command) => (
                                <span
                                  key={command}
                                  className="rounded bg-white px-2 py-1 text-xs text-slate-700"
                                >
                                  {command}
                                </span>
                              ),
                            )}
                          </div>
                        </div>
                      </>
                    ) : (
                      <p className="mt-2 text-xs text-slate-500">
                        State information unavailable.
                      </p>
                    )}
                  </div>
                )}

                <div className="mt-4">
                  <label
                    htmlFor={`zone-${device.id}`}
                    className="field-label"
                  >
                    Location / Zone
                  </label>

                  <select
                    id={`zone-${device.id}`}
                    value={getAssignmentValue(device)}
                    onChange={(event) =>
                      handleAssignment(
                        device.id,
                        event.target.value,
                      )
                    }
                    disabled={assigningDeviceId === device.id}
                    className="field w-full"
                  >
                    <option value="">Unassigned</option>

                    {locations.map((location) =>
                      location.zones.map((zone) => (
                        <option
                          key={zone.id}
                          value={`${location.location.id}:${zone.id}`}
                        >
                          {location.location.name} — {zone.name}
                        </option>
                      )),
                    )}
                  </select>
                </div>

                <pre className="panel-muted mt-4 overflow-x-auto p-3 text-xs text-slate-700">
                  {JSON.stringify(
                    device.default_config,
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
