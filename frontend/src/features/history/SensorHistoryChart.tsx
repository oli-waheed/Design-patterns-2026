import { useEffect, useMemo, useRef, useState } from 'react'

import EmptyState from '../../components/ui/EmptyState'
import { Skeleton } from '../../components/ui/Skeleton'
import { useRealtimeEvents } from '../../hooks/useRealtime'
import {
  getDevices,
  getLocation,
  getSensorReadingsRange,
  type DeviceDto,
  type ReadingDto,
  type ZoneDto,
} from '../../services/api'
import type { ReadingCreatedPayload } from '../../services/realtime'

/*
 * Phase 13 history chart.
 *
 * Data comes only from GET /api/sensors/{id}/readings?from=&to= (stored
 * sensor_readings, oldest first). New reading.created frames for the
 * selected sensor are appended live while the window ends at "now".
 */

const RANGES = [
  { key: '15m', label: '15 min', ms: 15 * 60 * 1000 },
  { key: '1h', label: '1 h', ms: 60 * 60 * 1000 },
  { key: '6h', label: '6 h', ms: 6 * 60 * 60 * 1000 },
  { key: '24h', label: '24 h', ms: 24 * 60 * 60 * 1000 },
  { key: '7d', label: '7 days', ms: 7 * 24 * 60 * 60 * 1000 },
] as const

type RangeKey = (typeof RANGES)[number]['key']

type Point = {
  t: number
  value: number
  unit: string
  source: string
  recordedAt: string
}

const HEIGHT = 260
const MARGIN = { top: 16, right: 76, bottom: 28, left: 48 }

function toPoint(reading: ReadingDto): Point {
  return {
    t: new Date(reading.recorded_at).getTime(),
    value: reading.value,
    unit: reading.unit,
    source: reading.source,
    recordedAt: reading.recorded_at,
  }
}

function formatValue(value: number, unit: string): string {
  return unit === 'vwc' ? value.toFixed(3) : value.toFixed(0)
}

function formatTick(t: number, rangeMs: number): string {
  const date = new Date(t)

  if (rangeMs > 24 * 60 * 60 * 1000) {
    return date.toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    })
  }

  return date.toLocaleTimeString(undefined, {
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Round step for about `count` ticks between min and max. */
function niceStep(span: number, count: number): number {
  const raw = span / Math.max(count, 1)
  const power = 10 ** Math.floor(Math.log10(raw))
  const unit = raw / power

  const nice = unit <= 1 ? 1 : unit <= 2 ? 2 : unit <= 5 ? 5 : 10

  return nice * power
}

function yDomain(points: Point[], zone: ZoneDto | null): [number, number] {
  const values = points.map((point) => point.value)

  if (zone && points[0]?.unit === 'vwc') {
    values.push(zone.moisture_threshold_low, zone.moisture_threshold_high)
  }

  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || Math.abs(max) || 1
  const step = niceStep(span, 4)

  const low = Math.max(0, Math.floor((min - span * 0.1) / step) * step)
  const high = Math.ceil((max + span * 0.1) / step) * step

  return [low, high === low ? low + step : high]
}

/** Split into segments where readings are missing, so gaps are not bridged. */
function segments(points: Point[]): Point[][] {
  if (points.length < 2) {
    return [points]
  }

  const gaps = points
    .slice(1)
    .map((point, index) => point.t - points[index].t)
    .sort((a, b) => a - b)

  const median = gaps[Math.floor(gaps.length / 2)]
  const maxGap = Math.max(median * 5, 60 * 1000)

  const result: Point[][] = [[points[0]]]

  for (let index = 1; index < points.length; index += 1) {
    if (points[index].t - points[index - 1].t > maxGap) {
      result.push([])
    }

    result[result.length - 1].push(points[index])
  }

  return result
}

function useElementWidth<T extends HTMLElement>() {
  const ref = useRef<T | null>(null)
  const [width, setWidth] = useState(640)

  useEffect(() => {
    const element = ref.current

    if (!element) {
      return
    }

    const observer = new ResizeObserver((entries) => {
      setWidth(Math.max(280, Math.floor(entries[0].contentRect.width)))
    })

    observer.observe(element)

    return () => observer.disconnect()
  }, [])

  return [ref, width] as const
}

export default function SensorHistoryChart() {
  const [sensors, setSensors] = useState<DeviceDto[]>([])
  const [sensorId, setSensorId] = useState('')
  const [rangeKey, setRangeKey] = useState<RangeKey>('1h')
  const [points, setPoints] = useState<Point[]>([])
  const [zone, setZone] = useState<ZoneDto | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showTable, setShowTable] = useState(false)
  const [hoverIndex, setHoverIndex] = useState<number | null>(null)
  const [window_, setWindow] = useState<{ from: number; to: number }>(
    () => ({ from: 0, to: 0 }),
  )

  const [containerRef, width] = useElementWidth<HTMLDivElement>()

  const range = RANGES.find((item) => item.key === rangeKey) ?? RANGES[1]
  const sensor = sensors.find((item) => item.id === sensorId)

  // Sensors for the selector; moisture sensors first.
  useEffect(() => {
    let cancelled = false

    getDevices(undefined, 'sensor')
      .then((data) => {
        if (cancelled) {
          return
        }

        const sorted = [...data].sort((a, b) =>
          a.device_type === b.device_type
            ? a.display_name.localeCompare(b.display_name)
            : a.device_type === 'moisture_sensor'
              ? -1
              : 1,
        )

        setSensors(sorted)
        setSensorId((current) => current || sorted[0]?.id || '')

        if (sorted.length === 0) {
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load sensors')
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  // Zone thresholds for the selected sensor (shown as a band).
  const zoneId = sensor?.zone_id ?? null
  const locationId = sensor?.location_id ?? null

  useEffect(() => {
    let cancelled = false

    const request =
      zoneId && locationId
        ? getLocation(locationId).then(
            (config) => config.zones.find((item) => item.id === zoneId) ?? null,
          )
        : Promise.resolve(null)

    request
      .then((data) => {
        if (!cancelled) {
          setZone(data)
        }
      })
      .catch(() => {
        if (!cancelled) {
          setZone(null)
        }
      })

    return () => {
      cancelled = true
    }
  }, [zoneId, locationId])

  // Stored readings for the window.
  useEffect(() => {
    if (!sensorId) {
      return
    }

    let cancelled = false
    const to = Date.now()
    const from = to - range.ms

    getSensorReadingsRange(
      sensorId,
      new Date(from).toISOString(),
      new Date(to).toISOString(),
    )
      .then((rows) => {
        if (!cancelled) {
          setPoints(rows.map(toPoint))
          setWindow({ from, to })
          setError(null)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : 'Failed to load history',
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
  }, [sensorId, range.ms])

  // Live: append new readings for this sensor and slide the window.
  useRealtimeEvents((event) => {
    if (event.type !== 'reading.created') {
      return
    }

    const payload = event.payload as ReadingCreatedPayload

    if (payload.device_id !== sensorId) {
      return
    }

    const point = toPoint(payload)
    const from = Date.now() - range.ms

    setPoints((current) =>
      [...current.filter((item) => item.t >= from), point].sort(
        (a, b) => a.t - b.t,
      ),
    )
    setWindow({ from, to: Math.max(Date.now(), point.t) })
  })

  function changeSensor(id: string) {
    setLoading(true)
    setHoverIndex(null)
    setSensorId(id)
  }

  function changeRange(key: RangeKey) {
    setLoading(true)
    setHoverIndex(null)
    setRangeKey(key)
  }

  const chart = useMemo(() => {
    if (points.length === 0) {
      return null
    }

    const innerWidth = width - MARGIN.left - MARGIN.right
    const innerHeight = HEIGHT - MARGIN.top - MARGIN.bottom
    const [yMin, yMax] = yDomain(points, zone)
    const xMin = window_.from || points[0].t
    const xMax = Math.max(window_.to, points[points.length - 1].t)

    const x = (t: number) =>
      MARGIN.left + ((t - xMin) / Math.max(xMax - xMin, 1)) * innerWidth
    const y = (value: number) =>
      MARGIN.top + (1 - (value - yMin) / (yMax - yMin)) * innerHeight

    const yStep = niceStep(yMax - yMin, 4)
    const yTicks: number[] = []
    for (let tick = yMin; tick <= yMax + yStep / 2; tick += yStep) {
      yTicks.push(Number(tick.toFixed(6)))
    }

    const xTickCount = Math.max(2, Math.min(6, Math.floor(innerWidth / 110)))
    const xTicks = Array.from(
      { length: xTickCount },
      (_, index) => xMin + ((xMax - xMin) * index) / (xTickCount - 1),
    )

    const paths = segments(points).map((segment) =>
      segment
        .map(
          (point, index) =>
            `${index === 0 ? 'M' : 'L'}${x(point.t).toFixed(1)},${y(point.value).toFixed(1)}`,
        )
        .join(' '),
    )

    return { x, y, yTicks, xTicks, paths, innerWidth, innerHeight }
  }, [points, zone, width, window_])

  function handlePointer(event: React.PointerEvent<SVGRectElement>) {
    if (!chart || points.length === 0) {
      return
    }

    const box = event.currentTarget.getBoundingClientRect()
    const px = event.clientX - box.left + MARGIN.left

    // Nearest point by x.
    let best = 0
    let bestDistance = Infinity

    points.forEach((point, index) => {
      const distance = Math.abs(chart.x(point.t) - px)

      if (distance < bestDistance) {
        best = index
        bestDistance = distance
      }
    })

    setHoverIndex(best)
  }

  const latest = points[points.length - 1]
  const hovered = hoverIndex !== null ? points[hoverIndex] : null
  const unit = latest?.unit ?? (sensor?.device_type === 'light_sensor' ? 'lux' : 'vwc')
  const values = points.map((point) => point.value)
  const showBand = zone && unit === 'vwc'

  return (
    <div className="mt-6 space-y-4">
      {/* Filters: one row above the chart. */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <label className="text-sm">
          <span className="field-label">Sensor</span>
          <select
            value={sensorId}
            onChange={(event) => changeSensor(event.target.value)}
            disabled={sensors.length === 0}
            className="field w-full sm:w-72"
          >
            {sensors.map((item) => (
              <option key={item.id} value={item.id}>
                {item.display_name} ({item.device_type.replace('_sensor', '')})
              </option>
            ))}
          </select>
        </label>

        <div className="flex flex-wrap items-center gap-2">
          <div
            role="group"
            aria-label="Time range"
            className="inline-flex rounded-md border border-slate-300 bg-white p-0.5"
          >
            {RANGES.map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => changeRange(item.key)}
                aria-pressed={rangeKey === item.key}
                className={`rounded px-3 py-1.5 text-sm font-medium ${
                  rangeKey === item.key
                    ? 'bg-slate-900 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {item.label}
              </button>
            ))}
          </div>

          <button
            type="button"
            onClick={() => setShowTable((current) => !current)}
            aria-pressed={showTable}
            className="btn btn-secondary btn-sm"
          >
            {showTable ? 'Show chart' : 'Show table'}
          </button>
        </div>
      </div>

      {error && <p className="alert-error">{error}</p>}

      {points.length > 0 && (
        <dl className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
          <div className="flex gap-1.5">
            <dt className="text-slate-500">Readings</dt>
            <dd className="font-medium tabular-nums text-slate-900">
              {points.length}
            </dd>
          </div>
          <div className="flex gap-1.5">
            <dt className="text-slate-500">Min</dt>
            <dd className="font-medium tabular-nums text-slate-900">
              {formatValue(Math.min(...values), unit)}
            </dd>
          </div>
          <div className="flex gap-1.5">
            <dt className="text-slate-500">Max</dt>
            <dd className="font-medium tabular-nums text-slate-900">
              {formatValue(Math.max(...values), unit)}
            </dd>
          </div>
          {showBand && (
            <div className="flex gap-1.5">
              <dt className="text-slate-500">Zone target</dt>
              <dd className="font-medium tabular-nums text-slate-900">
                {zone.moisture_threshold_low.toFixed(2)}–
                {zone.moisture_threshold_high.toFixed(2)} vwc
              </dd>
            </div>
          )}
        </dl>
      )}

      <div ref={containerRef} className="relative">
        {loading ? (
          <Skeleton className="h-[260px] w-full" />
        ) : sensors.length === 0 ? (
          <EmptyState title="No sensors yet">
            Create or provision a sensor to see its history.
          </EmptyState>
        ) : points.length === 0 ? (
          <EmptyState title="No readings in this range">
            Try a longer range, or take a reading with “Read now”.
          </EmptyState>
        ) : showTable ? (
          <div className="panel max-h-[260px] overflow-auto">
            <table className="min-w-full text-sm">
              <thead className="sticky top-0 bg-slate-50 text-left text-slate-600">
                <tr>
                  <th className="px-4 py-2 font-semibold">Time</th>
                  <th className="px-4 py-2 text-right font-semibold">
                    Value ({unit})
                  </th>
                  <th className="px-4 py-2 font-semibold">Source</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {[...points].reverse().map((point) => (
                  <tr key={`${point.t}-${point.value}`}>
                    <td className="whitespace-nowrap px-4 py-1.5 text-slate-600">
                      {new Date(point.t).toLocaleString()}
                    </td>
                    <td className="px-4 py-1.5 text-right tabular-nums text-slate-900">
                      {formatValue(point.value, unit)}
                    </td>
                    <td className="px-4 py-1.5 text-slate-600">
                      {point.source}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          chart && (
            <>
              <svg
                width={width}
                height={HEIGHT}
                role="img"
                aria-label={`${sensor?.display_name ?? 'Sensor'}: ${points.length} readings over the last ${range.label}, latest ${formatValue(latest.value, unit)} ${unit}.`}
                className="block touch-none select-none"
              >
                {/* Zone target band (recessive). */}
                {showBand && (
                  <g>
                    <rect
                      x={MARGIN.left}
                      width={chart.innerWidth}
                      y={chart.y(zone.moisture_threshold_high)}
                      height={Math.max(
                        0,
                        chart.y(zone.moisture_threshold_low) -
                          chart.y(zone.moisture_threshold_high),
                      )}
                      className="fill-chart-band"
                    />
                    <text
                      x={MARGIN.left + 6}
                      y={chart.y(zone.moisture_threshold_high) + 12}
                      className="fill-emerald-700 text-[11px]"
                    >
                      Zone target
                    </text>
                  </g>
                )}

                {/* Gridlines + y labels. */}
                {chart.yTicks.map((tick) => (
                  <g key={tick}>
                    <line
                      x1={MARGIN.left}
                      x2={MARGIN.left + chart.innerWidth}
                      y1={chart.y(tick)}
                      y2={chart.y(tick)}
                      className="stroke-chart-grid"
                      strokeWidth={1}
                    />
                    <text
                      x={MARGIN.left - 8}
                      y={chart.y(tick)}
                      dy="0.32em"
                      textAnchor="end"
                      className="fill-slate-500 text-[11px] tabular-nums"
                    >
                      {unit === 'vwc' ? tick.toFixed(2) : tick.toFixed(0)}
                    </text>
                  </g>
                ))}

                {/* X labels. */}
                {chart.xTicks.map((tick, index) => (
                  <text
                    key={tick}
                    x={chart.x(tick)}
                    y={HEIGHT - 8}
                    textAnchor={
                      index === 0
                        ? 'start'
                        : index === chart.xTicks.length - 1
                          ? 'end'
                          : 'middle'
                    }
                    className="fill-slate-500 text-[11px]"
                  >
                    {formatTick(tick, range.ms)}
                  </text>
                ))}

                {/* The series. */}
                {chart.paths.map((d, index) => (
                  <path
                    key={index}
                    d={d}
                    fill="none"
                    className="stroke-series-1"
                    strokeWidth={2}
                    strokeLinejoin="round"
                    strokeLinecap="round"
                  />
                ))}

                {/* Latest value at the line end. */}
                <circle
                  cx={chart.x(latest.t)}
                  cy={chart.y(latest.value)}
                  r={4}
                  className="fill-series-1 stroke-white"
                  strokeWidth={2}
                />
                <text
                  x={chart.x(latest.t) + 8}
                  y={chart.y(latest.value)}
                  dy="0.32em"
                  className="fill-slate-700 text-xs font-semibold tabular-nums"
                >
                  {formatValue(latest.value, unit)}
                </text>

                {/* Crosshair. */}
                {hovered && (
                  <g pointerEvents="none">
                    <line
                      x1={chart.x(hovered.t)}
                      x2={chart.x(hovered.t)}
                      y1={MARGIN.top}
                      y2={MARGIN.top + chart.innerHeight}
                      className="stroke-slate-400"
                      strokeWidth={1}
                    />
                    <circle
                      cx={chart.x(hovered.t)}
                      cy={chart.y(hovered.value)}
                      r={5}
                      className="fill-series-1 stroke-white"
                      strokeWidth={2}
                    />
                  </g>
                )}

                {/* Hit area larger than the line. */}
                <rect
                  x={MARGIN.left}
                  y={MARGIN.top}
                  width={chart.innerWidth}
                  height={chart.innerHeight}
                  fill="transparent"
                  onPointerMove={handlePointer}
                  onPointerDown={handlePointer}
                  onPointerLeave={() => setHoverIndex(null)}
                />
              </svg>

              {hovered && (
                <div
                  className="pointer-events-none absolute top-2 z-10 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs shadow-md"
                  style={{
                    left: Math.min(
                      Math.max(chart.x(hovered.t) - 70, 0),
                      width - 150,
                    ),
                  }}
                >
                  <p className="text-slate-500">
                    {new Date(hovered.t).toLocaleString()}
                  </p>
                  <p className="mt-0.5 font-semibold tabular-nums text-slate-900">
                    {formatValue(hovered.value, unit)} {unit}
                    <span className="ml-1 font-normal text-slate-500">
                      · {hovered.source}
                    </span>
                  </p>
                </div>
              )}
            </>
          )
        )}
      </div>
    </div>
  )
}
