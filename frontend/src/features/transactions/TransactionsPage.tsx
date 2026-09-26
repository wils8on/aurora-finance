import { useCallback, useEffect, useMemo, useState } from 'react'
import { CalendarRange, ChevronLeft, ChevronRight, FilterX, Plus, Search } from 'lucide-react'
import { listAccounts } from '../../api/accounts'
import { listCategories, listSubcategories } from '../../api/categories'
import { ApiClientError } from '../../api/client'
import { getTransaction, getTransactionSummary, listTransactions } from '../../api/transactions'
import { Button } from '../../components/base/Button'
import { Card } from '../../components/base/Card'
import { FormField } from '../../components/base/FormField'
import { Input } from '../../components/base/Input'
import { PageHeader } from '../../components/base/PageHeader'
import { Select } from '../../components/base/Select'
import { StatusBadge } from '../../components/base/StatusBadge'
import { EmptyState } from '../../components/feedback/EmptyState'
import { ErrorState } from '../../components/feedback/ErrorState'
import { LoadingState } from '../../components/feedback/LoadingState'
import { Modal } from '../../components/feedback/Modal'
import { useToast } from '../../components/feedback/Toast'
import type { Account, Category, DatePerspective, DerivedTransactionStatus, Subcategory, TransactionDetail as Detail, TransactionPage, TransactionQuery, TransactionSummary, TransactionType } from '../../types/api'
import { currentOperationalMonth, formatEconomicDate } from '../../utils/dates'
import { formatMoneyBRL } from '../../utils/money'
import { TransactionDetail } from './TransactionDetail'
import { TransactionForm } from './TransactionForm'

const STATUS_LABELS = { PENDING: 'Pendente', PARTIAL: 'Parcial', SETTLED: 'Liquidada', CANCELLED: 'Cancelada' } as const
const STATUS_TONES = { PENDING: 'neutral', PARTIAL: 'info', SETTLED: 'success', CANCELLED: 'danger' } as const
const PERSPECTIVE_LABELS = { COMPETENCE: 'Competência', DUE: 'Vencimento', CASH: 'Caixa' } as const
const SUMMARY_LABELS = { COMPETENCE: ['Receitas', 'Despesas', 'Resultado'], DUE: ['A receber', 'A pagar', 'Vencido'], CASH: ['Recebido', 'Pago', 'Fluxo líquido'] } as const

export function TransactionsPage() {
  const initial = useMemo(currentOperationalMonth, [])
  const [startDate, setStartDate] = useState(initial.start)
  const [endDate, setEndDate] = useState(initial.end)
  const [perspective, setPerspective] = useState<DatePerspective>('COMPETENCE')
  const [type, setType] = useState<TransactionType | ''>('')
  const [status, setStatus] = useState<DerivedTransactionStatus | ''>('')
  const [categoryId, setCategoryId] = useState('')
  const [subcategoryId, setSubcategoryId] = useState('')
  const [search, setSearch] = useState('')
  const [includeCancelled, setIncludeCancelled] = useState(false)
  const [page, setPage] = useState(1)
  const [data, setData] = useState<TransactionPage | null>(null)
  const [summary, setSummary] = useState<TransactionSummary | null>(null)
  const [accounts, setAccounts] = useState<Account[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [subcategories, setSubcategories] = useState<Subcategory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<ApiClientError | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [detail, setDetail] = useState<Detail | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailError, setDetailError] = useState<ApiClientError | null>(null)
  const [revision, setRevision] = useState(0)
  const { showSuccess } = useToast()
  const query = useMemo<TransactionQuery>(() => ({ perspective, start_date: startDate, end_date: endDate, transaction_type: type || undefined, derived_status: status || undefined, category_id: categoryId ? Number(categoryId) : undefined, subcategory_id: subcategoryId ? Number(subcategoryId) : undefined, search: search.trim() || undefined, include_cancelled: includeCancelled || undefined, page, page_size: 10 }), [perspective, startDate, endDate, type, status, categoryId, subcategoryId, search, includeCancelled, page])

  useEffect(() => { void Promise.all([listAccounts(), listCategories()]).then(([a, c]) => { setAccounts(a); setCategories(c) }) }, [])
  useEffect(() => { if (!categoryId) { setSubcategories([]); setSubcategoryId(''); return }; void listSubcategories(Number(categoryId)).then(setSubcategories) }, [categoryId])
  const load = useCallback(async () => { setLoading(true); setError(null); try { const [items, totals] = await Promise.all([listTransactions(query), getTransactionSummary(query)]); setData(items); setSummary(totals) } catch (value) { setError(value as ApiClientError) } finally { setLoading(false) } }, [query])
  useEffect(() => { void load() }, [load, revision])
  useEffect(() => { setPage(1) }, [perspective, startDate, endDate, type, status, categoryId, subcategoryId, search, includeCancelled])

  const openDetail = async (id: number) => { setDetailLoading(true); setDetailError(null); setDetail(null); try { setDetail(await getTransaction(id)) } catch (value) { setDetailError(value as ApiClientError) } finally { setDetailLoading(false) } }
  const clearFilters = () => { setType(''); setStatus(''); setCategoryId(''); setSubcategoryId(''); setSearch(''); setIncludeCancelled(false) }
  const changed = (value: Detail, message: string) => { setDetail(value); setRevision((item) => item + 1); showSuccess(message) }
  const refDateLabel = perspective === 'COMPETENCE' ? 'Competência' : perspective === 'DUE' ? 'Vencimento' : 'Liquidação no período'

  return <div className="page-stack transactions-page">
    <PageHeader eyebrow="Vida financeira" title="Movimentações" description="Acompanhe receitas e despesas, do compromisso econômico à realização financeira." action={<Button onClick={() => setCreateOpen(true)}><Plus size={18} />Nova movimentação</Button>} />
    <Card className="period-panel"><div className="perspective-tabs" aria-label="Perspectiva financeira">{(['COMPETENCE', 'DUE', 'CASH'] as DatePerspective[]).map((item) => <button key={item} type="button" className={perspective === item ? 'active' : ''} aria-pressed={perspective === item} onClick={() => setPerspective(item)}>{PERSPECTIVE_LABELS[item]}</button>)}</div><fieldset className="period-range"><legend>Período</legend><CalendarRange size={18} aria-hidden="true" /><label htmlFor="transaction-start">De</label><Input id="transaction-start" type="date" value={startDate} max={endDate} onChange={(event) => setStartDate(event.target.value)} /><label htmlFor="transaction-end">Até</label><Input id="transaction-end" type="date" value={endDate} min={startDate} onChange={(event) => setEndDate(event.target.value)} /></fieldset></Card>
    {summary && !loading && !error && <section className="summary-grid" aria-label={`Resumo por ${PERSPECTIVE_LABELS[perspective].toLowerCase()}`}>{[summary.primary_1, summary.primary_2, summary.primary_3].map((value, index) => <Card className="summary-card" key={SUMMARY_LABELS[perspective][index]}><span>{SUMMARY_LABELS[perspective][index]}</span><strong>{formatMoneyBRL(value)}</strong></Card>)}{perspective === 'COMPETENCE' && <><Card className="summary-card summary-card--secondary"><span>A receber</span><strong>{formatMoneyBRL(summary.receivable)}</strong></Card><Card className="summary-card summary-card--secondary"><span>A pagar</span><strong>{formatMoneyBRL(summary.payable)}</strong></Card></>}</section>}
    <Card className="filter-panel"><div className="filter-grid"><FormField htmlFor="transaction-search" label="Buscar"><div className="input-with-icon"><Search size={16} /><Input id="transaction-search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Descrição" /></div></FormField><FormField htmlFor="filter-type" label="Tipo"><Select id="filter-type" value={type} onChange={(e) => setType(e.target.value as TransactionType | '')}><option value="">Todos</option><option value="INCOME">Receita</option><option value="EXPENSE">Despesa</option></Select></FormField><FormField htmlFor="filter-status" label="Estado"><Select id="filter-status" value={status} onChange={(e) => setStatus(e.target.value as DerivedTransactionStatus | '')}><option value="">Todos</option>{Object.entries(STATUS_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</Select></FormField><FormField htmlFor="filter-category" label="Categoria"><Select id="filter-category" value={categoryId} onChange={(e) => setCategoryId(e.target.value)}><option value="">Todas</option>{categories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></FormField><FormField htmlFor="filter-subcategory" label="Subcategoria"><Select id="filter-subcategory" value={subcategoryId} onChange={(e) => setSubcategoryId(e.target.value)} disabled={!categoryId}><option value="">Todas</option>{subcategories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></FormField></div><div className="filter-footer"><label className="simple-check"><input type="checkbox" checked={includeCancelled} onChange={(e) => setIncludeCancelled(e.target.checked)} />Incluir canceladas</label><Button variant="ghost" onClick={clearFilters}><FilterX size={17} />Limpar filtros</Button></div></Card>
    {loading && <Card><LoadingState message="Carregando movimentações…" /></Card>}
    {!loading && error && <ErrorState message={error.message} requestId={error.requestId ?? undefined} onRetry={() => void load()} />}
    {!loading && !error && data?.items.length === 0 && <Card><EmptyState title="Nenhuma movimentação no período" description="Ajuste os filtros ou registre uma nova receita ou despesa." action={<Button onClick={() => setCreateOpen(true)}><Plus size={18} />Nova movimentação</Button>} /></Card>}
    {!loading && !error && data && data.items.length > 0 && <><div className="transaction-list" aria-label="Movimentações encontradas">{data.items.map((item) => <button type="button" className="transaction-card" key={item.id} onClick={() => void openDetail(item.id)}><div className="transaction-card__identity"><span className={`transaction-direction transaction-direction--${item.transaction_type.toLowerCase()}`}>{item.transaction_type === 'INCOME' ? 'Receita' : 'Despesa'}</span><strong>{item.description}</strong><small>{item.category.name}{item.subcategory ? ` · ${item.subcategory.name}` : ''}</small></div><div className="transaction-card__date"><span>{refDateLabel}</span><strong>{formatEconomicDate(item.reference_date)}</strong></div><dl className={perspective === 'CASH' ? 'transaction-values--cash' : ''}><div><dt>Nominal</dt><dd>{formatMoneyBRL(item.amount)}</dd></div><div><dt>Liquidado total</dt><dd>{formatMoneyBRL(item.settled_amount)}</dd></div>{perspective === 'CASH' && <div><dt>Liquidado no período</dt><dd>{formatMoneyBRL(item.period_settled_amount)}</dd></div>}<div><dt>Restante</dt><dd>{formatMoneyBRL(item.remaining_amount)}</dd></div></dl><StatusBadge tone={STATUS_TONES[item.derived_status]}>{STATUS_LABELS[item.derived_status]}</StatusBadge></button>)}</div><nav className="pagination" aria-label="Paginação"><Button variant="secondary" disabled={data.pagination.page <= 1} onClick={() => setPage((value) => value - 1)}><ChevronLeft size={17} />Anterior</Button><span>Página <strong>{data.pagination.page}</strong> de <strong>{data.pagination.total_pages}</strong> · {data.pagination.total_items} itens</span><Button variant="secondary" disabled={data.pagination.page >= data.pagination.total_pages} onClick={() => setPage((value) => value + 1)}>Próxima<ChevronRight size={17} /></Button></nav></>}
    <Modal open={createOpen} title="Nova movimentação" description="Registre uma obrigação econômica ou um fato financeiro identificável." onClose={() => setCreateOpen(false)}><TransactionForm categories={categories} accounts={accounts} onCancel={() => setCreateOpen(false)} onCreated={(value) => { setCreateOpen(false); setRevision((item) => item + 1); showSuccess(value.derived_status === 'SETTLED' ? 'Movimentação realizada criada com sucesso.' : 'Movimentação criada com sucesso.') }} /></Modal>
    <Modal open={detailLoading || Boolean(detail) || Boolean(detailError)} title="Detalhe da movimentação" onClose={() => { setDetail(null); setDetailError(null); setDetailLoading(false) }}>{detailLoading && <LoadingState message="Carregando detalhe…" />}{detailError && <ErrorState message={detailError.message} requestId={detailError.requestId ?? undefined} />}{detail && <TransactionDetail detail={detail} accounts={accounts} onChanged={changed} />}</Modal>
  </div>
}
