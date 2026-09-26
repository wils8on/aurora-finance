import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { getCurrentSession, login as requestLogin, logout as requestLogout } from '../../api/auth'
import { ApiClientError, configureAuthentication } from '../../api/client'
import type { AuthenticatedUser } from '../../types/api'

type AuthState = 'loading' | 'authenticated' | 'unauthenticated'
interface AuthValue {
  state: AuthState
  user: AuthenticatedUser | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>('loading')
  const [user, setUser] = useState<AuthenticatedUser | null>(null)
  const unauthenticate = useCallback(() => {
    configureAuthentication({ csrfToken: null })
    setUser(null)
    setState('unauthenticated')
  }, [])

  useEffect(() => {
    configureAuthentication({ onUnauthorized: unauthenticate })
    void getCurrentSession().then((session) => {
      configureAuthentication({ csrfToken: session.csrf_token })
      setUser(session.user)
      setState('authenticated')
    }).catch((error) => {
      if (error instanceof ApiClientError && error.status === 401) unauthenticate()
      else unauthenticate()
    })
    return () => configureAuthentication({ onUnauthorized: null })
  }, [unauthenticate])

  const login = useCallback(async (email: string, password: string) => {
    const session = await requestLogin(email, password)
    configureAuthentication({ csrfToken: session.csrf_token })
    setUser(session.user)
    setState('authenticated')
  }, [])

  const logout = useCallback(async () => {
    try { await requestLogout() } finally { unauthenticate() }
  }, [unauthenticate])

  const value = useMemo(() => ({ state, user, login, logout }), [state, user, login, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth deve ser utilizado dentro de AuthProvider.')
  return value
}
