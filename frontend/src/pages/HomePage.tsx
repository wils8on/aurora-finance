import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getHealth } from '../api/health'
import { ApiClientError } from '../api/client'
import { Card } from '../components/base/Card'
import { PageHeader } from '../components/base/PageHeader'
import { StatusBadge } from '../components/base/StatusBadge'
import { ErrorState } from '../components/feedback/ErrorState'
import { LoadingState } from '../components/feedback/LoadingState'

type HealthState =
  | { kind: 'loading' }
  | { kind: 'available' }
  | { kind: 'error'; error: ApiClientError }

const shortcuts = [
  { to: '/movimentacoes', title: 'Movimentações', description: 'Compromissos e realizações financeiras.' },
  { to: '/contas', title: 'Contas', description: 'Locais onde seus recursos financeiros estão.' },
  { to: '/categorias', title: 'Categorias', description: 'Organização da natureza de receitas e despesas.' },
]

export function HomePage() {
  const [health, setHealth] = useState<HealthState>({ kind: 'loading' })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let active = true
    setHealth({ kind: 'loading' })
    getHealth()
      .then(() => active && setHealth({ kind: 'available' }))
      .catch((error: unknown) => {
        if (!active) return
        const structured = error instanceof ApiClientError
          ? error
          : new ApiClientError({ code: 'UNKNOWN_ERROR', message: 'Falha inesperada.', field: null, details: {}, request_id: null }, 0)
        setHealth({ kind: 'error', error: structured })
      })
    return () => {
      active = false
    }
  }, [attempt])

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Bem-vindo"
        title="Clareza para suas decisões financeiras."
        description="O Aurora Finance é uma plataforma pessoal de gestão, planejamento e inteligência financeira."
      />

      <Card className="health-card">
        <div className="health-card__heading">
          <div>
            <span className="section-label">Conectividade</span>
            <h2>Status da API</h2>
          </div>
          {health.kind === 'available' && <StatusBadge tone="success">Disponível</StatusBadge>}
          {health.kind === 'error' && <StatusBadge tone="danger">Indisponível</StatusBadge>}
          {health.kind === 'loading' && <StatusBadge tone="info">Verificando</StatusBadge>}
        </div>
        {health.kind === 'loading' && <LoadingState message="Verificando conexão com a API…" />}
        {health.kind === 'available' && (
          <p className="health-message">A fundação web está conectada ao backend local.</p>
        )}
        {health.kind === 'error' && (
          <ErrorState
            title="API indisponível"
            message="Verifique se o backend local está em execução e tente novamente."
            requestId={health.error.requestId ?? undefined}
            onRetry={() => setAttempt((value) => value + 1)}
          />
        )}
      </Card>

      <section aria-labelledby="areas-title">
        <div className="section-heading">
          <span className="section-label">Estrutura inicial</span>
          <h2 id="areas-title">Áreas previstas</h2>
        </div>
        <div className="shortcut-grid">
          {shortcuts.map((shortcut) => (
            <Link className="shortcut-card" to={shortcut.to} key={shortcut.to}>
              <span className="shortcut-card__arrow" aria-hidden="true">↗</span>
              <h3>{shortcut.title}</h3>
              <p>{shortcut.description}</p>
              <span className="shortcut-card__status">Interface em preparação</span>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
