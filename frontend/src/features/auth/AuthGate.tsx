import { LoadingState } from '../../components/feedback/LoadingState'
import { useAuth } from './AuthContext'
import { LoginPage } from './LoginPage'

export function AuthGate({ children }: { children: React.ReactNode }) {
  const { state } = useAuth()
  if (state === 'loading') return <main className="auth-loading"><LoadingState message="Verificando sessão…" /></main>
  if (state === 'unauthenticated') return <LoginPage />
  return children
}
