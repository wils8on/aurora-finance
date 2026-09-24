import { Link } from 'react-router-dom'
import { Card } from '../components/base/Card'
import { EmptyState } from '../components/feedback/EmptyState'

export function NotFoundPage() {
  return (
    <Card>
      <EmptyState
        title="Página não encontrada"
        description="O endereço informado não faz parte da foundation atual do Aurora Finance."
        action={<Link className="button button--primary" to="/">Voltar ao início</Link>}
      />
    </Card>
  )
}
