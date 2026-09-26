import type { PropsWithChildren } from 'react'

type GlassLevel = 'subtle' | 'elevated' | 'modal'

interface GlassPanelProps extends PropsWithChildren {
  className?: string
  level?: GlassLevel
}

export function GlassPanel({ children, className = '', level = 'subtle' }: GlassPanelProps) {
  return <section className={`glass-panel glass-panel--${level} ${className}`.trim()}>{children}</section>
}
