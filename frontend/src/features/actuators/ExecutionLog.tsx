import { useEffect, useState } from 'react'

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

  useEffect(() => {
    loadExecutions()
  }, [])

  function formatDate(value: string): string {
    const date = new Date(value)

    if (Number.isNaN(date.getTime())) {
      return value
    }

    return date.toLocaleString()
  }

  return (
    <div className="mt-6 space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h4 className="font-semibold">
            Recent actuator executions
          </h4>

          <p className="mt-1 text-sm text-gray-500">
            The latest 20 actuator command attempts and applied policies.
          </p>
        </div>

        <button
          type="button"
          onClick={() => loadExecutions(true)}
          disabled={loading || refreshing}
          className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-gray-50 disabled:opacity-50"
        >
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {loading && (
        <p className="rounded-lg bg-gray-50 p-4 text-sm text-gray-500">
          Loading execution history...
        </p>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-700">
            {error}
          </p>

          <button
            type="button"
            onClick={() => loadExecutions(true)}
            className="mt-2 text-sm font-medium text-red-700 underline"
          >
            Try again
          </button>
        </div>
      )}

      {!loading && !error && executions.length === 0 && (
        <div className="rounded-lg border border-dashed bg-gray-50 p-6 text-center">
          <p className="font-medium text-gray-700">
            No actuator executions yet.
          </p>

          <p className="mt-2 text-sm text-gray-500">
            Actuator command attempts will appear here after they are executed.
          </p>
        </div>
      )}

      {!loading && executions.length > 0 && (
        <div className="overflow-x-auto rounded-lg border">
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left font-semibold text-gray-700">
                  Time
                </th>

                <th className="px-4 py-3 text-left font-semibold text-gray-700">
                  Device
                </th>

                <th className="px-4 py-3 text-left font-semibold text-gray-700">
                  Result
                </th>

                <th className="px-4 py-3 text-left font-semibold text-gray-700">
                  Policies
                </th>

                <th className="px-4 py-3 text-left font-semibold text-gray-700">
                  Message
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-gray-200 bg-white">
              {executions.map((execution) => (
                <tr key={execution.id}>
                  <td className="whitespace-nowrap px-4 py-3 text-gray-600">
                    {formatDate(execution.created_at)}
                  </td>

                  <td className="px-4 py-3 font-medium text-gray-800">
                    {execution.device_name}
                  </td>

                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${
                        execution.success
                          ? 'bg-green-100 text-green-700'
                          : 'bg-red-100 text-red-700'
                      }`}
                    >
                      {execution.success ? 'Success' : 'Failed'}
                    </span>
                  </td>

                  <td className="px-4 py-3 text-gray-600">
                    {execution.policy_applied.length > 0
                      ? execution.policy_applied.join(', ')
                      : 'None'}
                  </td>

                  <td className="px-4 py-3 text-gray-600">
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