import { useCallback, useEffect, useState } from 'react'
import { ChevronDown, ChevronRight, Plus, Tags, TrendingDown, TrendingUp } from 'lucide-react'
import { createCategory, createSubcategory, listCategories, listSubcategories } from '../../api/categories'
import { ApiClientError } from '../../api/client'
import { Button } from '../../components/base/Button'
import { Card } from '../../components/base/Card'
import { FormField } from '../../components/base/FormField'
import { IconButton } from '../../components/base/IconButton'
import { Input } from '../../components/base/Input'
import { PageHeader } from '../../components/base/PageHeader'
import { Select } from '../../components/base/Select'
import { StatusBadge } from '../../components/base/StatusBadge'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { LoadingState } from '../../components/feedback/LoadingState'
import { Modal } from '../../components/feedback/Modal'
import { useToast } from '../../components/feedback/Toast'
import type { Category, CategoryCreate, CategoryType, Subcategory } from '../../types/api'

type SubcategoryState = { loading: boolean; items: Subcategory[]; error: ApiClientError | null }
const CATEGORY_LABELS: Record<CategoryType, string> = { INCOME: 'Receita', EXPENSE: 'Despesa' }
const INITIAL_CATEGORY: CategoryCreate = { name: '', type: 'EXPENSE' }

export function CategoriesPage() {
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<ApiClientError | null>(null)
  const [expanded, setExpanded] = useState<Set<number>>(new Set())
  const [subcategories, setSubcategories] = useState<Record<number, SubcategoryState>>({})
  const [categoryModal, setCategoryModal] = useState(false)
  const [subcategoryFor, setSubcategoryFor] = useState<Category | null>(null)
  const [categoryForm, setCategoryForm] = useState<CategoryCreate>(INITIAL_CATEGORY)
  const [subcategoryName, setSubcategoryName] = useState('')
  const [fieldError, setFieldError] = useState('')
  const [submitError, setSubmitError] = useState<ApiClientError | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { showSuccess } = useToast()

  const load = useCallback(async () => {
    setLoading(true); setLoadError(null)
    try { setCategories(await listCategories()) }
    catch (error) { setLoadError(error as ApiClientError) }
    finally { setLoading(false) }
  }, [])
  useEffect(() => { void load() }, [load])

  const loadChildren = useCallback(async (categoryId: number) => {
    setSubcategories((current) => ({ ...current, [categoryId]: { loading: true, items: current[categoryId]?.items ?? [], error: null } }))
    try {
      const items = await listSubcategories(categoryId)
      setSubcategories((current) => ({ ...current, [categoryId]: { loading: false, items, error: null } }))
    } catch (error) {
      setSubcategories((current) => ({ ...current, [categoryId]: { loading: false, items: [], error: error as ApiClientError } }))
    }
  }, [])

  const toggleCategory = (categoryId: number) => {
    const opening = !expanded.has(categoryId)
    setExpanded((current) => { const next = new Set(current); opening ? next.add(categoryId) : next.delete(categoryId); return next })
    if (opening && !subcategories[categoryId]) void loadChildren(categoryId)
  }

  const resetModalState = () => {
    if (submitting) return
    setCategoryModal(false); setSubcategoryFor(null); setCategoryForm(INITIAL_CATEGORY)
    setSubcategoryName(''); setFieldError(''); setSubmitError(null)
  }

  const submitCategory = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!categoryForm.name.trim()) { setFieldError('Informe o nome da categoria.'); return }
    setSubmitting(true); setFieldError(''); setSubmitError(null)
    try {
      const created = await createCategory({ ...categoryForm, name: categoryForm.name.trim() })
      setCategories((current) => [...current, created].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')))
      showSuccess('Categoria criada com sucesso.'); setCategoryModal(false); setCategoryForm(INITIAL_CATEGORY)
    } catch (error) {
      const apiError = error as ApiClientError
      apiError.field === 'name' ? setFieldError(apiError.message) : setSubmitError(apiError)
    } finally { setSubmitting(false) }
  }

  const submitSubcategory = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!subcategoryName.trim()) { setFieldError('Informe o nome da subcategoria.'); return }
    if (!subcategoryFor) return
    setSubmitting(true); setFieldError(''); setSubmitError(null)
    try {
      const created = await createSubcategory(subcategoryFor.id, { name: subcategoryName.trim() })
      setSubcategories((current) => ({ ...current, [subcategoryFor.id]: { loading: false, error: null, items: [...(current[subcategoryFor.id]?.items ?? []), created].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')) } }))
      setExpanded((current) => new Set(current).add(subcategoryFor.id))
      showSuccess('Subcategoria criada com sucesso.'); setSubcategoryFor(null); setSubcategoryName('')
    } catch (error) {
      const apiError = error as ApiClientError
      apiError.field === 'name' ? setFieldError(apiError.message) : setSubmitError(apiError)
    } finally { setSubmitting(false) }
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Organização econômica" title="Categorias" description="Organize receitas e despesas em uma hierarquia simples de categorias e subcategorias." action={<Button onClick={() => setCategoryModal(true)}><Plus size={18} />Nova categoria</Button>} />
      {loading && <Card><LoadingState message="Carregando categorias…" /></Card>}
      {!loading && loadError && <ErrorState message="Não foi possível carregar suas categorias." requestId={loadError.requestId ?? undefined} onRetry={() => void load()} />}
      {!loading && !loadError && categories.length === 0 && <Card><EmptyState title="Nenhuma categoria cadastrada" description="Crie categorias para representar a natureza de suas receitas e despesas." action={<Button onClick={() => setCategoryModal(true)}><Plus size={18} />Nova categoria</Button>} /></Card>}
      {!loading && !loadError && categories.length > 0 && (
        <div className="category-list" aria-label="Categorias cadastradas">
          {categories.map((category) => {
            const isExpanded = expanded.has(category.id); const children = subcategories[category.id]
            return (
              <Card className="category-card" key={category.id}>
                <div className="category-card__header">
                  <IconButton label={`${isExpanded ? 'Recolher' : 'Expandir'} ${category.name}`} icon={isExpanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />} aria-expanded={isExpanded} aria-controls={`subcategories-${category.id}`} onClick={() => toggleCategory(category.id)} />
                  <span className={`entity-icon entity-icon--${category.type.toLowerCase()}`}>{category.type === 'INCOME' ? <TrendingUp size={20} /> : <TrendingDown size={20} />}</span>
                  <div className="category-card__title"><h2>{category.name}</h2><StatusBadge tone={category.type === 'INCOME' ? 'success' : 'info'}>{CATEGORY_LABELS[category.type]}</StatusBadge></div>
                  <Button variant="ghost" disabled={!category.is_active} title={category.is_active ? undefined : 'Categoria inativa'} onClick={() => { setFieldError(''); setSubmitError(null); setSubcategoryFor(category) }}><Plus size={17} />Nova subcategoria</Button>
                </div>
                {isExpanded && (
                  <div className="subcategory-panel" id={`subcategories-${category.id}`}>
                    {children?.loading && <LoadingState message="Carregando subcategorias…" />}
                    {children?.error && <ErrorState message="Não foi possível carregar as subcategorias." onRetry={() => void loadChildren(category.id)} />}
                    {children && !children.loading && !children.error && children.items.length === 0 && <p className="subcategory-empty">Nenhuma subcategoria cadastrada.</p>}
                    {children && !children.loading && !children.error && children.items.length > 0 && <ul>{children.items.map((item) => <li key={item.id}><Tags size={16} aria-hidden="true" /><span>{item.name}</span><StatusBadge tone={item.is_active ? 'neutral' : 'danger'}>{item.is_active ? 'Ativa' : 'Inativa'}</StatusBadge></li>)}</ul>}
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      )}

      <Modal open={categoryModal} title="Nova categoria" description="A categoria define a natureza econômica do lançamento." onClose={resetModalState}>
        <form className="form-stack" onSubmit={submitCategory} noValidate>
          <FormField htmlFor="category-name" label="Nome" required error={fieldError}><Input id="category-name" autoFocus value={categoryForm.name} onChange={(event) => setCategoryForm({ ...categoryForm, name: event.target.value })} aria-invalid={Boolean(fieldError)} aria-describedby={fieldError ? 'category-name-error' : undefined} /></FormField>
          <FormField htmlFor="category-type" label="Tipo" required><Select id="category-type" value={categoryForm.type} onChange={(event) => setCategoryForm({ ...categoryForm, type: event.target.value as CategoryType })}><option value="EXPENSE">Despesa</option><option value="INCOME">Receita</option></Select></FormField>
          {submitError && <ErrorState message={submitError.message} requestId={submitError.requestId ?? undefined} />}
          <footer className="modal-actions"><Button type="button" variant="ghost" onClick={resetModalState} disabled={submitting}>Cancelar</Button><Button type="submit" loading={submitting}>Salvar categoria</Button></footer>
        </form>
      </Modal>

      <Modal open={Boolean(subcategoryFor)} title="Nova subcategoria" description={subcategoryFor ? `Categoria: ${subcategoryFor.name}` : undefined} onClose={resetModalState}>
        <form className="form-stack" onSubmit={submitSubcategory} noValidate>
          <FormField htmlFor="subcategory-name" label="Nome" required error={fieldError}><Input id="subcategory-name" autoFocus value={subcategoryName} onChange={(event) => setSubcategoryName(event.target.value)} aria-invalid={Boolean(fieldError)} aria-describedby={fieldError ? 'subcategory-name-error' : undefined} /></FormField>
          {submitError && <ErrorState message={submitError.message} requestId={submitError.requestId ?? undefined} />}
          <footer className="modal-actions"><Button type="button" variant="ghost" onClick={resetModalState} disabled={submitting}>Cancelar</Button><Button type="submit" loading={submitting}>Salvar subcategoria</Button></footer>
        </form>
      </Modal>
    </div>
  )
}
