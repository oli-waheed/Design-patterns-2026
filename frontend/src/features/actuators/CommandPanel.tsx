
import { useCallback, useEffect, useState } from 'react'

import ConfirmDialog from '../../components/ui/ConfirmDialog'
import EmptyState from '../../components/ui/EmptyState'
import { SkeletonList } from '../../components/ui/Skeleton'
import { useRealtimeEvents } from '../../hooks/useRealtime'

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

/** Actuators of one family with their current states (no React state). */
async function fetchActuators(family: string) {
  const data = await getDevices(family as 'simulation' | 'edge', 'actuator')

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

  return { data, stateMap }
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
  const [confirmStart, setConfirmStart] = useState(false)

  function applyActuators(
    data: DeviceDto[],
    stateMap: Record<string, ActuatorStateDto>,
  ) {
    setDevices(data)
    setActuatorStates(stateMap)

    setSelectedDeviceId((current) => {
      if (data.some((device) => device.id === current)) {
        return current
      }

      return data[0]?.id ?? ''
    })
  }

  async function loadActuators() {
    const { data, stateMap } = await fetchActuators(family)
    applyActuators(data, stateMap)
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

  // Initial load (and when the device family changes). The loaders set
  // state only after their requests finish, so the effect does not
  // re-render synchronously.
  useEffect(() => {
    let cancelled = false

    Promise.all([fetchActuators(family), getCommandHistory(50)])
      .then(([actuators, commandHistory]) => {
        if (!cancelled) {
          applyActuators(actuators.data, actuators.stateMap)
          setHistory(commandHistory)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to load actuators',
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
  }, [family])

  // Live: refresh states and history when an actuator changes state,
  // whether from this panel, another browser, or the API.
  useRealtimeEvents((event) => {
    if (event.type !== 'actuator.state_changed') {
      return
    }

    const deviceId = (event.payload as { device_id?: string }).device_id

    if (devices.some((device) => device.id === deviceId)) {
      void refreshAll()
    }
  })

  const selectedDevice = devices.find(
    (device) => device.id === selectedDeviceId,
  )

  const selectedState = selectedDevice
    ? actuatorStates[selectedDevice.id]
    : undefined

  const allowedCommands = selectedState?.allowed_commands ?? []

  const closeConfirm = useCallback(() => setConfirmStart(false), [])

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
      <section className="panel p-5">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h4 className="font-semibold">
              Actuator control
            </h4>

            <p className="mt-1 text-sm text-slate-500">
              Select an actuator to execute an available command.
            </p>
          </div>

          <button
            type="button"
            onClick={() => void refreshAll()}
            disabled={refreshing || submitting}
            className="btn btn-secondary"
          >
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {loading && (
          <div className="mt-4">
            <SkeletonList rows={2} label="Loading actuators…" rowClassName="h-12" />
          </div>
        )}

        {!loading && devices.length === 0 && (
          <div className="mt-4">
            <EmptyState title={`No ${family} actuators`}>
              Provision devices in the Devices section first.
            </EmptyState>
          </div>
        )}

        {devices.length > 0 && (
          <div className="mt-5 space-y-4">
            <div>
              <label
                htmlFor="command-device"
                className="field-label"
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
                className="field w-full"
              >
                {devices.map((device) => (
                  <option key={device.id} value={device.id}>
                    {device.display_name} ({device.device_type})
                  </option>
                ))}
              </select>
            </div>

            {selectedDevice && (
              <div className="rounded-lg bg-slate-50 p-4">
                <p className="text-sm text-slate-500">
                  Selected device
                </p>

                <p className="mt-1 font-semibold">
                  {selectedDevice.display_name}
                </p>

                <p className="mt-1 text-sm text-slate-600">
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
                    <span className="text-sm text-slate-500">
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
                          className="rounded bg-white px-2 py-1 text-xs text-slate-700"
                        >
                          {command}
                        </span>
                      ))
                    ) : (
                      <span className="text-sm text-slate-500">
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
        <section className="panel p-5">
          <h4 className="font-semibold">
            Available controls
          </h4>

          {selectedDevice.device_type === 'water_pump' && (
            <div className="mt-4 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={() => setConfirmStart(true)}
                disabled={
                  submitting ||
                  !allowedCommands.includes('start_pump')
                }
                className="btn bg-emerald-700 text-white hover:bg-emerald-800"
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
                className="btn bg-red-700 text-white hover:bg-red-800"
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
        <div className="alert-ok">
          {notice}
        </div>
      )}

      {error && (
        <div className="alert-error">
          {error}
        </div>
      )}

      {/* Command history */}
      <section className="panel p-5">
        <div className="mb-4">
          <h4 className="font-semibold">
            Command history
          </h4>

          <p className="mt-1 text-sm text-slate-500">
            Latest 50 command attempts, including successful,
            failed and rejected commands.
          </p>
        </div>

        {history.length === 0 ? (
          <p className="empty-state">
            No command history available yet.
          </p>
        ) : (
          <div className="panel overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
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

              <tbody className="divide-y divide-slate-200">
                {history.map((record) => (
                  <tr key={record.id}>
                    <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                      {formatDate(record.created_at)}
                    </td>

                    <td className="px-4 py-3 font-medium">
                      {record.command_type}
                    </td>

                    <td className="px-4 py-3 text-slate-600">
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

                    <td className="px-4 py-3 text-slate-600">
                      {record.error_message || '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      <ConfirmDialog
        open={confirmStart}
        title="Start the pump?"
        message={`${selectedDevice?.display_name ?? 'The pump'} will start watering. If it keeps running for 30 minutes or more, the max-runtime policy blocks further commands to it.`}
        confirmLabel="Start pump"
        onCancel={closeConfirm}
        onConfirm={() => {
          setConfirmStart(false)
          void handleCommand('start_pump')
        }}
      />
    </div>
  )
}
