import { Card } from '../../components/base/Card'
import { PageHeader } from '../../components/base/PageHeader'
import { EmptyState } from '../../components/feedback/EmptyState'

export function CategoriesPage() {
  return (
    <div className="page-stack">
      <PageHeader title="Categorias" description="Estruture a natureza econômica de receitas e despesas." />
      <Card>
        <EmptyState title="Interface de categorias em preparação" description="Categorias e subcategorias funcionais serão adicionadas na próxima etapa de equivalência web." />
      </Card>
    </div>
  )
}
