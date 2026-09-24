interface ErrorStateProps {
  title?: string
  message: string
  requestId?: string
  onRetry?: () => void
}

export function ErrorState({
  title = 'Não foi possível concluir a operação',
  message,
  requestId,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="feedback-state feedback-state--error" role="alert">
      <div>
        <strong>{title}</strong>
        <p>{message}</p>
        {requestId && <small>Referência: {requestId}</small>}
      </div>
      {onRetry && (
        <button className="button button--secondary" type="button" onClick={onRetry}>
          Tentar novamente
        </button>
      )}
    </div>
  )
}
