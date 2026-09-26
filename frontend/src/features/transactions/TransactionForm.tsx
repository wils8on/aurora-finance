import { useEffect, useState } from 'react'
import { createSettledTransaction, createTransaction } from '../../api/transactions'
import { listSubcategories } from '../../api/categories'
import { ApiClientError } from '../../api/client'
import { Button } from '../../components/base/Button'
import { FormField } from '../../components/base/FormField'
import { Input } from '../../components/base/Input'
import { Select } from '../../components/base/Select'
import { ErrorState } from '../../components/feedback/ErrorState'
import type { Account, Category, Subcategory, TransactionDetail, TransactionType } from '../../types/api'
import { isCanonicalMoney } from '../../utils/money'
import { operationalDateTimeToIso } from '../../utils/dates'

interface Props { categories: Category[]; accounts: Account[]; onCancel: () => void; onCreated: (value: TransactionDetail) => void }
type Errors = Partial<Record<'description' | 'amount' | 'competence_date' | 'category_id' | 'account_id' | 'settled_at', string>>

export function TransactionForm({ categories, accounts, onCancel, onCreated }: Props) {
  const [type, setType] = useState<TransactionType>('EXPENSE')
  const [description, setDescription] = useState('')
  const [amount, setAmount] = useState('')
  const [competence, setCompetence] = useState('')
  const [due, setDue] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [subcategoryId, setSubcategoryId] = useState('')
  const [notes, setNotes] = useState('')
  const [realized, setRealized] = useState(false)
  const [accountId, setAccountId] = useState('')
  const [settledAt, setSettledAt] = useState('')
  const [settlementNotes, setSettlementNotes] = useState('')
  const [subcategories, setSubcategories] = useState<Subcategory[]>([])
  const [errors, setErrors] = useState<Errors>({})
  const [submitError, setSubmitError] = useState<ApiClientError | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const availableCategories = categories.filter((item) => item.is_active && item.type === type)

  useEffect(() => {
    setCategoryId(''); setSubcategoryId(''); setSubcategories([])
  }, [type])
  useEffect(() => {
    if (!categoryId) { setSubcategories([]); return }
    void listSubcategories(Number(categoryId)).then((items) => setSubcategories(items.filter((item) => item.is_active)))
  }, [categoryId])

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    const next: Errors = {}
    if (!description.trim()) next.description = 'Informe a descrição.'
    if (!isCanonicalMoney(amount) || amount.startsWith('-') || amount === '0' || amount === '0.00') next.amount = 'Informe um valor positivo com até duas casas.'
    if (!competence) next.competence_date = 'Informe a competência.'
    if (!categoryId) next.category_id = 'Selecione a categoria.'
    if (realized && !accountId) next.account_id = 'Selecione a conta.'
    if (realized && !settledAt) next.settled_at = 'Informe a data e hora da liquidação.'
    setErrors(next)
    if (Object.keys(next).length) return
    setSubmitting(true); setSubmitError(null)
    const base = {
      transaction_type: type, description: description.trim(), amount,
      competence_date: competence, due_date: due || null, category_id: Number(categoryId),
      subcategory_id: subcategoryId ? Number(subcategoryId) : null,
    }
    try {
      const created = realized
        ? await createSettledTransaction({ ...base, transaction_notes: notes.trim() || null, settlement: { account_id: Number(accountId), amount, settled_at: operationalDateTimeToIso(settledAt), notes: settlementNotes.trim() || null } })
        : await createTransaction({ ...base, notes: notes.trim() || null })
      onCreated(created)
    } catch (error) {
      const apiError = error as ApiClientError
      if (apiError.field && apiError.field in next) setErrors({ [apiError.field]: apiError.message })
      else setSubmitError(apiError)
    } finally { setSubmitting(false) }
  }

  return <form className="form-stack" onSubmit={submit} noValidate>
    <div className="form-grid">
      <FormField htmlFor="transaction-type" label="Tipo" required><Select id="transaction-type" value={type} onChange={(e) => setType(e.target.value as TransactionType)}><option value="EXPENSE">Despesa</option><option value="INCOME">Receita</option></Select></FormField>
      <FormField htmlFor="transaction-amount" label="Valor" required error={errors.amount}><Input id="transaction-amount" inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} aria-invalid={Boolean(errors.amount)} /></FormField>
    </div>
    <FormField htmlFor="transaction-description" label="Descrição" required error={errors.description}><Input id="transaction-description" value={description} onChange={(e) => setDescription(e.target.value)} aria-invalid={Boolean(errors.description)} /></FormField>
    <div className="form-grid">
      <FormField htmlFor="transaction-competence" label="Competência" required error={errors.competence_date}><Input id="transaction-competence" type="date" value={competence} onChange={(e) => setCompetence(e.target.value)} aria-invalid={Boolean(errors.competence_date)} /></FormField>
      <FormField htmlFor="transaction-due" label="Vencimento" helper="Opcional"><Input id="transaction-due" type="date" value={due} onChange={(e) => setDue(e.target.value)} /></FormField>
    </div>
    <div className="form-grid">
      <FormField htmlFor="transaction-category" label="Categoria" required error={errors.category_id}><Select id="transaction-category" value={categoryId} onChange={(e) => { setCategoryId(e.target.value); setSubcategoryId('') }} aria-invalid={Boolean(errors.category_id)}><option value="">Selecione</option>{availableCategories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></FormField>
      <FormField htmlFor="transaction-subcategory" label="Subcategoria" helper="Opcional"><Select id="transaction-subcategory" value={subcategoryId} onChange={(e) => setSubcategoryId(e.target.value)} disabled={!categoryId}><option value="">Sem subcategoria</option>{subcategories.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></FormField>
    </div>
    <FormField htmlFor="transaction-notes" label="Observações" helper="Opcional"><textarea className="input textarea" id="transaction-notes" value={notes} onChange={(e) => setNotes(e.target.value)} /></FormField>
    <label className="check-field"><input type="checkbox" checked={realized} onChange={(e) => setRealized(e.target.checked)} /><span><strong>Registrar como já realizada</strong><small>Cria a movimentação e sua liquidação de forma atômica.</small></span></label>
    {realized && <div className="settlement-fields">
      <div className="form-grid">
        <FormField htmlFor="historical-account" label="Conta" required error={errors.account_id}><Select id="historical-account" value={accountId} onChange={(e) => setAccountId(e.target.value)}><option value="">Selecione</option>{accounts.filter((item) => item.is_active).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></FormField>
        <FormField htmlFor="historical-settled-at" label="Data e hora da liquidação" required error={errors.settled_at}><Input id="historical-settled-at" type="datetime-local" value={settledAt} onChange={(e) => setSettledAt(e.target.value)} /></FormField>
      </div>
      <FormField htmlFor="historical-notes" label="Observações da liquidação" helper="Opcional"><Input id="historical-notes" value={settlementNotes} onChange={(e) => setSettlementNotes(e.target.value)} /></FormField>
    </div>}
    {submitError && <ErrorState message={submitError.message} requestId={submitError.requestId ?? undefined} />}
    <footer className="modal-actions"><Button type="button" variant="ghost" onClick={onCancel} disabled={submitting}>Cancelar</Button><Button type="submit" loading={submitting}>Salvar movimentação</Button></footer>
  </form>
}
