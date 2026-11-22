
import { useEffect, useState } from 'react'
import {
  evaluateAutomation,
  getLocations,
  getSavedStrategy,
  saveAutomationStrategy,
  type AutomationEvaluationDto,
  type LocationSummaryDto,
  type StrategyKey,
} from '../../services/api'

export default function StrategyPanel() {
  const [locations, setLocations] = useState<LocationSummaryDto[]>([])
  const [locationId, setLocationId] = useState('')
  const [strategy, setStrategy] = useState<StrategyKey>('conservative')
  const [result, setResult] = useState<AutomationEvaluationDto | null>(null)
  const [loadingLocations, setLoadingLocations] = useState(true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')

  // Strategy persisted for the selected location (Phase 6 automation_rules).
  // undefined = still loading, null = nothing saved yet.
  const [savedStrategy, setSavedStrategy] = useState<
    StrategyKey | null | undefined
  >(undefined)

  useEffect(() => {
    if (!locationId) {
      return
    }

    let cancelled = false

    getSavedStrategy(locationId)
      .then((data) => {
        if (!cancelled) {
          setSavedStrategy(data.strategy_key)
          setStrategy(data.strategy_key ?? 'conservative')
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSavedStrategy(null)
        }
      })

    return () => {
      cancelled = true
    }
  }, [locationId])

  useEffect(() => {
    let cancelled = false

    async function loadLocations() {
      try {
        setError('')
        const data = await getLocations()

        if (cancelled) return

        setLocations(data)

        if (data.length > 0) {
          setLocationId(data[0].id)
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
      setSavedStrategy(strategy)
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
      setSavedStrategy(evaluation.strategy_key)

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
    setSavedStrategy(undefined)
    setResult(null)
    setMessage('')
    setError('')
  }

  return (
    <section className="space-y-5">
      <p className="text-sm text-slate-600">
        Choose a location and strategy, save your selection, then evaluate
        the latest moisture readings.
      </p>

      {error && (
        <div
          role="alert"
          className="alert-error"
        >
          {error}
        </div>
      )}

      {message && (
        <div
          role="status"
          className="alert-ok"
        >
          {message}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <label
            htmlFor="automation-location"
            className="field-label"
          >
            Location
          </label>

          <select
            id="automation-location"
            value={locationId}
            onChange={(event) => handleLocationChange(event.target.value)}
            disabled={loading || loadingLocations || locations.length === 0}
            className="field w-full"
          >
            <option value="">Select a location</option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {location.name}
              </option>
            ))}
          </select>

          {loadingLocations && (
            <p className="mt-1 text-xs text-slate-500">Loading locations...</p>
          )}

          {!loadingLocations && locations.length === 0 && (
            <p className="mt-1 text-xs text-slate-500">
              Create a location before using automation.
            </p>
          )}
        </div>

        <div>
          <label
            htmlFor="automation-strategy"
            className="field-label"
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
            className="field w-full"
          >
            <option value="conservative">Conservative</option>
            <option value="aggressive">Aggressive</option>
          </select>

          <p className="mt-2 text-xs text-slate-500">
            {savedStrategy === undefined && locationId ? (
              'Loading saved strategy…'
            ) : savedStrategy ? (
              <>
                Saved strategy:{' '}
                <span className="badge badge-info capitalize">
                  {savedStrategy}
                </span>
                {strategy !== savedStrategy && (
                  <span className="ml-1 text-warn-ink">
                    (unsaved change — save to make it active)
                  </span>
                )}
              </>
            ) : (
              'No strategy saved yet. Evaluate uses Conservative until you save one.'
            )}
          </p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleSaveStrategy}
          disabled={loading || loadingLocations || !locationId}
          className="btn btn-primary"
        >
          {loading ? 'Please wait...' : 'Save Strategy'}
        </button>

        <button
          type="button"
          onClick={handleEvaluate}
          disabled={loading || loadingLocations || !locationId}
          className="btn btn-secondary"
        >
          {loading ? 'Please wait...' : 'Evaluate Automation'}
        </button>
      </div>

      {result && (
        <div className="space-y-4">
          <div className="panel p-4">
            <h4 className="font-semibold">Evaluation Results</h4>
            <p className="mt-1 text-sm text-slate-600">
              Active strategy:{' '}
              <span className="font-medium text-slate-900">
                {result.strategy_key}
              </span>
            </p>
          </div>

          {result.recommendations.length === 0 ? (
            <p className="rounded-lg border p-4 text-sm text-slate-600">
              No zones were found for this location.
            </p>
          ) : (
            <div className="space-y-3">
              {result.recommendations.map((recommendation) => {
                const actionClass =
                  recommendation.action === 'irrigate'
                    ? 'bg-blue-100 text-blue-800'
                    : 'bg-slate-100 text-slate-700'

                return (
                  <article
                    key={recommendation.zone_id}
                    className="panel p-4"
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
                        <dt className="text-slate-500">Moisture</dt>
                        <dd className="font-medium">
                          {recommendation.moisture == null
                            ? 'No reading'
                            : recommendation.moisture.toFixed(3)}
                        </dd>
                      </div>

                      <div>
                        <dt className="text-slate-500">Low threshold</dt>
                        <dd className="font-medium">
                          {recommendation.low_threshold}
                        </dd>
                      </div>

                      <div>
                        <dt className="text-slate-500">High threshold</dt>
                        <dd className="font-medium">
                          {recommendation.high_threshold}
                        </dd>
                      </div>
                    </dl>

                    <p className="mt-3 text-sm text-slate-700">
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
