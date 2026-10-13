
import { useEffect, useState } from 'react'
import {
  evaluateAutomation,
  getLocations,
  saveAutomationStrategy,
  type AutomationEvaluationDto,
  type LocationSummaryDto,
  type StrategyKey,
} from '../../services/api'

const PREFERRED_LOCATION_ID = '8a85f6dc-8033-4366-9dc0-f47fc7766fcb'

export default function StrategyPanel() {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([])
  const [locationId, setLocationId] = useState('')
  const [strategy, setStrategy] = useState<StrategyKey>('conservative')
  const [result, setResult] = useState<AutomationEvaluationDto | null>(null)
  const [loadingLocations, setLoadingLocations] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  useEffect(() => {
    let cancelled = false

    async function loadLocations() {
      try {
        setError('')
        const data = await getLocations()

        if (cancelled) return

        setLocations(data)

        if (data.length > 0) {
          const preferredLocation = data.find(
            (location) => location.id === PREFERRED_LOCATION_ID,
          )

          setLocationId(preferredLocation?.id ?? data[0].id)
        } else {
          setLocationId('')
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to load locations.',
          )
        }
      } finally {
        if (!cancelled) setLoadingLocations(false)
      }
    }

    void loadLocations()

    return () => {
      cancelled = true
    }
  }, [])

  async function handleSaveStrategy() {
    if (!locationId) {
      setError('Please select a location.')
      return
    }

    try {
      setLoading(true)
      setError('')
      setMessage('')

      await saveAutomationStrategy(locationId, strategy)
      setMessage(`Saved ${strategy} strategy successfully.`)

      // Clear old results because the active strategy has changed.
      setResult(null)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to save automation strategy.',
      )
    } finally {
      setLoading(false)
    }
  }

  async function handleEvaluate() {
    if (!locationId) {
      setError('Please select a location.')
      return
    }

    try {
      setLoading(true)
      setError('')
      setMessage('')

      const evaluation = await evaluateAutomation(locationId)

      setResult(evaluation)

      // The backend response is authoritative about the active strategy.
      setStrategy(evaluation.strategy_key)
      setMessage('Automation evaluation completed.')
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Failed to evaluate automation.',
      )
    } finally {
      setLoading(false)
    }
  }

  function handleLocationChange(nextLocationId: string) {
    setLocationId(nextLocationId)
    setResult(null)
    setMessage('')
    setError('')
  }

  return (
    <section className="space-y-5">
      <div>
        <h3 className="text-lg font-semibold">Automation Strategy</h3>
        <p className="mt-1 text-sm text-gray-600">
          Choose a location and strategy, save your selection, then evaluate
          the latest moisture readings.
        </p>
      </div>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-300 bg-red-50 p-3 text-sm text-red-700"
        >
          {error}
        </div>
      )}

      {message && (
        <div
          role="status"
          className="rounded-lg border border-green-300 bg-green-50 p-3 text-sm text-green-800"
        >
          {message}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label
            htmlFor="automation-location"
            className="mb-2 block text-sm font-medium"
          >
            Location
          </label>

          <select
            id="automation-location"
            value={locationId}
            onChange={(event) => handleLocationChange(event.target.value)}
            disabled={loading || loadingLocations || locations.length === 0}
            className="w-full rounded-lg border px-3 py-2"
          >
            <option value="">Select a location</option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name} — {location.id.slice(0, 8)}
              </option>
            ))}
          </select>

          {loadingLocations && (
            <p className="mt-1 text-xs text-gray-500">Loading locations...</p>
          )}

          {!loadingLocations && locations.length === 0 && (
            <p className="mt-1 text-xs text-gray-500">
              Create a location before using automation.
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="automation-strategy"
            className="mb-2 block text-sm font-medium"
          >
            Strategy
          </label>

          <select
            id="automation-strategy"
            value={strategy}
            onChange={(event) => {
              setStrategy(event.target.value as StrategyKey)
              setResult(null)
              setMessage('')
              setError('')
            }}
            disabled={loading}
            className="w-full rounded-lg border px-3 py-2"
          >
            <option value="conservative">Conservative</option>
            <option value="aggressive">Aggressive</option>
          </select>

          <p className="mt-1 text-xs text-gray-500">
            Save your selection before evaluating to make it the active
            strategy.
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleSaveStrategy}
          disabled={loading || loadingLocations || !locationId}
          className="rounded-lg bg-black px-4 py-2 text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? 'Please wait...' : 'Save Strategy'}
        </button>

        <button
          type="button"
          onClick={handleEvaluate}
          disabled={loading || loadingLocations || !locationId}
          className="rounded-lg border px-4 py-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? 'Please wait...' : 'Evaluate Automation'}
        </button>
      </div>

      {result && (
        <div className="space-y-4">
          <div className="rounded-lg border p-4">
            <h4 className="font-semibold">Evaluation Results</h4>
            <p className="mt-1 text-sm text-gray-600">
              Active strategy:{' '}
              <span className="font-medium text-gray-900">
                {result.strategy_key}
              </span>
            </p>
          </div>

          {result.recommendations.length === 0 ? (
            <p className="rounded-lg border p-4 text-sm text-gray-600">
              No zones were found for this location.
            </p>
          ) : (
            <div className="space-y-3">
              {result.recommendations.map((recommendation) => {
                const actionClass =
                  recommendation.action === 'irrigate'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-gray-100 text-gray-700'

                return (
                  <article
                    key={recommendation.zone_id}
                    className="rounded-lg border p-4"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <h4 className="font-semibold">
                        {recommendation.zone_name}
                      </h4>

                      <span
                        className={`rounded-full px-3 py-1 text-sm font-medium ${actionClass}`}
                      >
                        {recommendation.action}
                      </span>
                    </div>

                    <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
                      <div>
                        <dt className="text-gray-500">Moisture</dt>
                        <dd className="font-medium">
                          {recommendation.moisture == null
                            ? 'No reading'
                            : recommendation.moisture.toFixed(3)}
                        </dd>
                      </div>

                      <div>
                        <dt className="text-gray-500">Low threshold</dt>
                        <dd className="font-medium">
                          {recommendation.low_threshold}
                        </dd>
                      </div>

                      <div>
                        <dt className="text-gray-500">High threshold</dt>
                        <dd className="font-medium">
                          {recommendation.high_threshold}
                        </dd>
                      </div>
                    </dl>

                    <p className="mt-3 text-sm text-gray-700">
                      {recommendation.reason}
                    </p>
                  </article>
                )
              })}
            </div>
          )}
        </div>
      )}
    </section>
  )
}
