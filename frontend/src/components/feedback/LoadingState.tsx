interface LoadingStateProps {
  message?: string
}

export function LoadingState({ message = 'Carregando…' }: LoadingStateProps) {
  return (
    <div className="feedback-state" role="status" aria-live="polite">
      <span className="loading-indicator" aria-hidden="true" />
      <span>{message}</span>
    </div>
  )
}
