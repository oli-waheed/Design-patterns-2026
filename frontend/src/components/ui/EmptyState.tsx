import type { ReactNode } from 'react'

type EmptyStateProps = {
  title: string
  children?: ReactNode
}

/** Consistent "nothing here yet" box for every panel. */
export default function EmptyState({ title, children }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <p className="font-medium text-slate-700">{title}</p>
      {children && <div className="mt-1">{children}</div>}
    </div>
  )
}
