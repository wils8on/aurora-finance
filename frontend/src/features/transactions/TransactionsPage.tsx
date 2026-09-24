import { Card } from '../../components/base/Card'
import { PageHeader } from '../../components/base/PageHeader'
import { EmptyState } from '../../components/feedback/EmptyState'

export function TransactionsPage() {
  return (
    <div className="page-stack">
      <PageHeader title="Movimentações" description="Acompanhe compromissos econômicos e suas realizações financeiras." />
      <Card>
        <EmptyState title="Interface de movimentações em preparação" description="Nenhuma movimentação financeira é consultada ou exibida nesta foundation." />
      </Card>
    </div>
  )
}
