import { Card } from '../../components/base/Card'
import { PageHeader } from '../../components/base/PageHeader'
import { EmptyState } from '../../components/feedback/EmptyState'

export function AccountsPage() {
  return (
    <div className="page-stack">
      <PageHeader title="Contas" description="Organize onde seus recursos financeiros estão." />
      <Card>
        <EmptyState title="Interface de contas em preparação" description="A listagem e o cadastro funcional serão construídos na próxima etapa de equivalência web." />
      </Card>
    </div>
  )
}
