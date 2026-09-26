import { createContext, useCallback, useContext, useMemo, useState, type PropsWithChildren } from 'react'
import { CheckCircle2 } from 'lucide-react'

interface ToastContextValue {
  showSuccess: (message: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

export function ToastProvider({ children }: PropsWithChildren) {
  const [message, setMessage] = useState<string | null>(null)
  const showSuccess = useCallback((value: string) => {
    setMessage(value)
    window.setTimeout(() => setMessage(null), 3_500)
  }, [])
  const value = useMemo(() => ({ showSuccess }), [showSuccess])

  return (
    <ToastContext.Provider value={value}>
      {children}
      {message && (
        <div className="toast" role="status" aria-live="polite">
          <CheckCircle2 size={19} aria-hidden="true" />
          {message}
        </div>
      )}
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast deve ser usado dentro de ToastProvider.')
  return context
}
