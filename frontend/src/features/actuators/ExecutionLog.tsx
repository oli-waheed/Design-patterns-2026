import { useEffect, useState } from 'react'

import EmptyState from '../../components/ui/EmptyState'
import { SkeletonList } from '../../components/ui/Skeleton'
import { useRealtimeEvents } from '../../hooks/useRealtime'

import {
  getActuatorExecutions,
} from '../../services/actuatorApi'

import type {
  ActuatorExecutionDto,
} from '../../services/actuatorApi'

export default function ExecutionLog() {
  const [executions, setExecutions] = useState<
    ActuatorExecutionDto[]
  >([])

  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function loadExecutions(isRefresh = false) {
    try {
      if (isRefresh) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }

      setError(null)

      const data = await getActuatorExecutions(20)
      setExecutions(data)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to load actuator execution history',
      )
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  // Initial load: state is set only after the request finishes.
  useEffect(() => {
    let cancelled = false

    getActuatorExecutions(20)
      .then((data) => {
        if (!cancelled) {
          setExecutions(data)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'Failed to load actuator execution history',
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
  }, [])

  // Live: a state change or a failed command means a new execution row.
  useRealtimeEvents((event) => {
    if (
      event.type === 'actuator.state_changed' ||
      (event.type === 'alert.created' &&
        (event.payload as { event_type?: string }).event_type ===
          'command.failed')
    ) {
      void loadExecutions(true)
    }
  })

  function formatDate(value: string): string {
    const date = new Date(value)

    if (Number.isNaN(date.getTime())) {
      return value
    }

    return date.toLocaleString()
  }

  return (
    <div className="mt-8 space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h4 className="font-semibold">
            Recent actuator executions
          </h4>

          <p className="mt-1 text-sm text-slate-500">
            The latest 20 actuator command attempts and applied policies.
          </p>
        </div>

        <button
          type="button"
          onClick={() => loadExecutions(true)}
          disabled={loading || refreshing}
          className="btn btn-secondary"
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {loading && (
        <SkeletonList rows={3} label="Loading execution history…" rowClassName="h-10" />
      )}

      {error && (
        <div className="alert-error">
          <p>{error}</p>

          <button
            type="button"
            onClick={() => loadExecutions(true)}
            className="mt-2 font-medium underline"
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && executions.length === 0 && (
        <EmptyState title="No actuator executions yet">
          Actuator command attempts appear here after they run.
        </EmptyState>
      )}

      {!loading && executions.length > 0 && (
        <div className="panel overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-slate-700">
                  Time
                </th>

                <th className="px-4 py-3 text-left font-semibold text-slate-700">
                  Device
                </th>

                <th className="px-4 py-3 text-left font-semibold text-slate-700">
                  Result
                </th>

                <th className="px-4 py-3 text-left font-semibold text-slate-700">
                  Policies
                </th>

                <th className="px-4 py-3 text-left font-semibold text-slate-700">
                  Message
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-200 bg-white">
              {executions.map((execution) => (
                <tr key={execution.id}>
                  <td className="whitespace-nowrap px-4 py-3 text-slate-600">
                    {formatDate(execution.created_at)}
                  </td>

                  <td className="px-4 py-3 font-medium text-slate-800">
                    {execution.device_name}
                  </td>

                  <td className="px-4 py-3">
                    <span
                      className={`badge ${
                        execution.success ? 'badge-ok' : 'badge-error'
                      }`}
                    >
                      {execution.success ? 'Success' : 'Failed'}
                    </span>
                  </td>

                  <td className="px-4 py-3 text-slate-600">
                    {execution.policy_applied.length > 0
                      ? execution.policy_applied.join(', ')
                      : 'None'}
                  </td>

                  <td className="px-4 py-3 text-slate-600">
                    {execution.message || '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}