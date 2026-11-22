type SkeletonProps = {
  className?: string
}

/** Grey pulsing block shown while data is loading. */
export function Skeleton({ className = 'h-4 w-full' }: SkeletonProps) {
  return <div className={`skeleton ${className}`} aria-hidden="true" />
}

type SkeletonListProps = {
  rows?: number
  label?: string
  rowClassName?: string
}

/** A stack of skeleton rows with an accessible loading label. */
export function SkeletonList({
  rows = 3,
  label = 'Loading…',
  rowClassName = 'h-16',
}: SkeletonListProps) {
  return (
    <div className="space-y-3" role="status" aria-live="polite">
      <span className="sr-only">{label}</span>
      {Array.from({ length: rows }, (_, index) => (
        <Skeleton key={index} className={`${rowClassName} w-full`} />
      ))}
    </div>
  )
}
