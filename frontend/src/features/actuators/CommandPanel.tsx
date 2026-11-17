
import { useEffect, useState } from 'react'

import {
  getDevices,
} from '../../services/api'

import type {
  DeviceDto,
} from '../../services/api'

import {
  executeCommand,
  getActuatorState,
  getCommandHistory,
} from '../../services/actuatorApi'

import type {
  ActuatorStateDto,
  CommandLogDto,
} from '../../services/actuatorApi'

type DeviceFamily = 'simulation' | 'edge'

type CommandPanelProps = {
  family: DeviceFamily
}

const statusStyles = {
  success: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  rejected: 'bg-amber-100 text-amber-800',
}

export default function CommandPanel({
  family,
}: CommandPanelProps) {
  const [devices, setDevices] = useState<DeviceDto[]>([])
  const [actuatorStates, setActuatorStates] = useState<
    Record<string, ActuatorStateDto>
  >({})

  const [selectedDeviceId, setSelectedDeviceId] = useState('')
  const [history, setHistory] = useState<CommandLogDto[]>([])

  const [lightLevel, setLightLevel] = useState(50)

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  async function loadActuators() {
    const data = await getDevices(family, 'actuator')

    const stateResults = await Promise.all(
      data.map(async (device) => {
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

    setDevices(data)
    setActuatorStates(stateMap)

    setSelectedDeviceId((current) => {
      if (data.some((device) => device.id === current)) {
        return current
      }

      return data[0]?.id ?? ''
    })
  }

  async function loadHistory() {
    const data = await getCommandHistory(50)
    setHistory(data)
  }

  async function refreshAll() {
    try {
      setRefreshing(true)
      setError(null)

      await Promise.all([
        loadActuators(),
        loadHistory(),
      ])
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to refresh command data',
      )
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    void refreshAll()
  }, [family])

  const selectedDevice = devices.find(
    (device) => device.id === selectedDeviceId,
  )

  const selectedState = selectedDevice
    ? actuatorStates[selectedDevice.id]
    : undefined

  const allowedCommands = selectedState?.allowed_commands ?? []

  async function handleCommand(
    commandType: string,
    payload: Record<string, unknown> = {},
  ) {
    if (!selectedDevice) {
      return
    }

    try {
      setSubmitting(true)
      setError(null)
      setNotice(null)

      const result = await executeCommand({
        device_id: selectedDevice.id,
        command_type: commandType,
        payload,
      })

      if (result.status === 'success') {
        setNotice(`Command "${commandType}" executed successfully.`)
      } else {
        setNotice(
          `${result.status.toUpperCase()}: ${
            result.error_message || 'Command was not successful.'
          }`,
        )
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Command execution failed',
      )
    } finally {
      await refreshAll()
      setSubmitting(false)
    }
  }

  function formatDate(value: string): string {
    const date = new Date(value)

    if (Number.isNaN(date.getTime())) {
      return value
    }

    return date.toLocaleString()
  }

  return (
    <div className="mt-6 space-y-8">

      {/* Device selection */}
      <section className="rounded-lg border bg-white p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h4 className="font-semibold">
              Actuator control
            </h4>

            <p className="mt-1 text-sm text-gray-500">
              Select an actuator to execute an available command.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void refreshAll()}
            disabled={refreshing || submitting}
            className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {loading && (
          <p className="mt-4 text-sm text-gray-500">
            Loading actuators...
          </p>
        )}

        {!loading && devices.length === 0 && (
          <div className="mt-4 rounded-lg bg-gray-50 p-4 text-sm text-gray-600">
            No actuators found for the {family} device family.
            Provision devices in the Devices section first.
          </div>
        )}

        {devices.length > 0 && (
          <div className="mt-5 space-y-4">
            <div>
              <label
                htmlFor="command-device"
                className="mb-2 block text-sm font-medium"
              >
                Select actuator
              </label>

              <select
                id="command-device"
                value={selectedDeviceId}
                onChange={(event) =>
                  setSelectedDeviceId(event.target.value)
                }
                disabled={submitting}
                className="w-full rounded-md border px-3 py-2 text-sm"
              >
                {devices.map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.display_name} ({device.device_type})
                  </option>
                ))}
              </select>
            </div>

            {selectedDevice && (
              <div className="rounded-lg bg-gray-50 p-4">
                <p className="text-sm text-gray-500">
                  Selected device
                </p>

                <p className="mt-1 font-semibold">
                  {selectedDevice.display_name}
                </p>

                <p className="mt-1 text-sm text-gray-600">
                  Type: {selectedDevice.device_type}
                </p>

                <div className="mt-3">
                  <span className="text-sm font-medium">
                    Current state:{' '}
                  </span>

                  {selectedState ? (
                    <span className="font-semibold capitalize">
                      {selectedState.state}
                    </span>
                  ) : (
                    <span className="text-sm text-gray-500">
                      Unavailable
                    </span>
                  )}
                </div>

                <div className="mt-3">
                  <p className="text-sm font-medium">
                    Allowed commands
                  </p>

                  <div className="mt-2 flex flex-wrap gap-2">
                    {allowedCommands.length > 0 ? (
                      allowedCommands.map((command) => (
                        <span
                          key={command}
                          className="rounded bg-white px-2 py-1 text-xs text-gray-700"
                        >
                          {command}
                        </span>
                      ))
                    ) : (
                      <span className="text-sm text-gray-500">
                        No commands currently available.
                      </span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Command controls */}
      {selectedDevice && selectedState && (
        <section className="rounded-lg border bg-white p-5">
          <h4 className="font-semibold">
            Available controls
          </h4>

          {selectedDevice.device_type === 'water_pump' && (
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => void handleCommand('start_pump')}
                disabled={
                  submitting ||
                  !allowedCommands.includes('start_pump')
                }
                className="rounded-md bg-green-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {submitting ? 'Processing...' : 'Start pump'}
              </button>

              <button
                type="button"
                onClick={() => void handleCommand('stop_pump')}
                disabled={
                  submitting ||
                  !allowedCommands.includes('stop_pump')
                }
                className="rounded-md bg-red-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-red-800 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {submitting ? 'Processing...' : 'Stop pump'}
              </button>
            </div>
          )}

          {selectedDevice.device_type === 'grow_light' && (
            <div className="mt-4 space-y-4">
              <div>
                <div className="flex justify-between text-sm">
                  <label htmlFor="light-level" className="font-medium">
                    Light level
                  </label>

                  <span className="font-semibold">
                    {lightLevel}%
                  </span>
                </div>

                <input
                  id="light-level"
                  type="range"
                  min="0"
                  max="100"
                  step="1"
                  value={lightLevel}
                  onChange={(event) =>
                    setLightLevel(Number(event.target.value))
                  }
                  className="mt-3 w-full"
                />
              </div>

              <button
                type="button"
                onClick={() =>
                  void handleCommand('set_light_level', {
                    level: lightLevel,
                  })
                }
                disabled={
                  submitting ||
                  !allowedCommands.includes('set_light_level')
                }
                className="rounded-md bg-blue-700 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-800 disabled:cursor-not-allowed disabled:opacity-40"
              >
                Set light level
              </button>
            </div>
          )}
        </section>
      )}

      {notice && (
        <div className="rounded-md border border-green-200 bg-green-50 p-3 text-sm text-green-800">
          {notice}
        </div>
      )}

      {error && (
        <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Command history */}
      <section className="rounded-lg border bg-white p-5">
        <div className="mb-4">
          <h4 className="font-semibold">
            Command history
          </h4>

          <p className="mt-1 text-sm text-gray-500">
            Latest 50 command attempts, including successful,
            failed and rejected commands.
          </p>
        </div>

        {history.length === 0 ? (
          <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
            No command history available yet.
          </p>
        ) : (
          <div className="overflow-x-auto rounded-lg border">
            <table className="min-w-full divide-y divide-gray-200 text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold">
                    Time
                  </th>

                  <th className="px-4 py-3 text-left font-semibold">
                    Command
                  </th>

                  <th className="px-4 py-3 text-left font-semibold">
                    Payload
                  </th>

                  <th className="px-4 py-3 text-left font-semibold">
                    Status
                  </th>

                  <th className="px-4 py-3 text-left font-semibold">
                    Message
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-gray-200">
                {history.map((record) => (
                  <tr key={record.id}>
                    <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                      {formatDate(record.created_at)}
                    </td>

                    <td className="px-4 py-3 font-medium">
                      {record.command_type}
                    </td>

                    <td className="px-4 py-3 text-gray-600">
                      {JSON.stringify(record.payload)}
                    </td>

                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-semibold ${
                          statusStyles[record.status]
                        }`}
                      >
                        {record.status}
                      </span>
                    </td>

                    <td className="px-4 py-3 text-gray-600">
                      {record.error_message || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  )
}
