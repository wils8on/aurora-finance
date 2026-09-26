import { useCallback, useEffect, useState } from 'react'
import { ApiClientError } from '../api/client'
import { getHealth } from '../api/health'

export type HealthState =
  | { kind: 'loading' }
  | { kind: 'available' }
  | { kind: 'error'; error: ApiClientError }

export function useHealth() {
  const [state, setState] = useState<HealthState>({ kind: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    setState({ kind: 'loading' })
    getHealth()
      .then(() => active && setState({ kind: 'available' }))
      .catch((error: unknown) => {
        if (active) {
          setState({
            kind: 'error',
            error: error instanceof ApiClientError
              ? error
              : new ApiClientError(
                  { code: 'UNKNOWN_ERROR', message: 'Falha inesperada.', field: null, details: {}, request_id: null },
                  0,
                ),
          })
        }
      })
    return () => { active = false }
  }, [attempt])

  const retry = useCallback(() => setAttempt((value) => value + 1), [])
  return { state, retry }
}
