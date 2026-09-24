import type { PropsWithChildren } from 'react'

type StatusTone = 'neutral' | 'success' | 'danger' | 'info'

interface StatusBadgeProps extends PropsWithChildren {
  tone?: StatusTone
}

export function StatusBadge({ children, tone = 'neutral' }: StatusBadgeProps) {
  return <span className={`status-badge status-badge--${tone}`}>{children}</span>
}
