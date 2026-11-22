type SparklineProps = {
  values: number[]
  width?: number
  height?: number
  label: string
}

/**
 * Tiny trend line for a sensor card: recent readings in a quiet slate,
 * the latest point in the series accent. Not a full chart, so no axes.
 */
export default function Sparkline({
  values,
  width = 120,
  height = 32,
  label,
}: SparklineProps) {
  if (values.length < 2) {
    return (
      <span className="text-xs text-slate-400" aria-label={label}>
        Trend after 2 readings
      </span>
    )
  }

  const pad = 4
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1

  const x = (index: number) =>
    pad + (index / (values.length - 1)) * (width - pad * 2)
  const y = (value: number) =>
    pad + (1 - (value - min) / span) * (height - pad * 2)

  const d = values
    .map((value, index) => `${index === 0 ? 'M' : 'L'}${x(index).toFixed(1)},${y(value).toFixed(1)}`)
    .join(' ')

  const last = values.length - 1

  return (
    <svg
      width={width}
      height={height}
      role="img"
      aria-label={label}
      className="block shrink-0"
    >
      <path
        d={d}
        fill="none"
        className="stroke-slate-400"
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      <circle
        cx={x(last)}
        cy={y(values[last])}
        r={3}
        className="fill-series-1 stroke-white"
        strokeWidth={1.5}
      />
    </svg>
  )
}
