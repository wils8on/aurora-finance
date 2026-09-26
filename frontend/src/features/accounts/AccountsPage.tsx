import { useCallback, useEffect, useState } from 'react'
import { Building2, CalendarDays, Plus, WalletCards } from 'lucide-react'
import { createAccount, listAccounts } from '../../api/accounts'
import { ApiClientError } from '../../api/client'
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
import type { Account, AccountCreate, AccountType } from '../../types/api'
import { formatEconomicDate } from '../../utils/dates'
import { formatMoneyBRL, isCanonicalMoney } from '../../utils/money'

const ACCOUNT_TYPE_LABELS: Record<AccountType, string> = {
  CHECKING: 'Conta corrente', SAVINGS: 'Poupança', CASH: 'Dinheiro',
  DIGITAL: 'Conta digital', OTHER: 'Outra',
}

const INITIAL_FORM: AccountCreate = {
  name: '', institution: null, account_type: 'CHECKING',
  initial_balance: '0.00', initial_balance_date: null,
}

export function AccountsPage() {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<ApiClientError | null>(null)
  const [isModalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<AccountCreate>(INITIAL_FORM)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [submitError, setSubmitError] = useState<ApiClientError | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const { showSuccess } = useToast()

  const load = useCallback(async () => {
    setLoading(true); setLoadError(null)
    try { setAccounts(await listAccounts()) }
    catch (error) { setLoadError(error as ApiClientError) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { void load() }, [load])

  const closeModal = useCallback(() => {
    if (submitting) return
    setModalOpen(false); setForm(INITIAL_FORM); setFieldErrors({}); setSubmitError(null)
  }, [submitting])

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    const errors: Record<string, string> = {}
    if (!form.name.trim()) errors.name = 'Informe o nome da conta.'
    if (!isCanonicalMoney(form.initial_balance)) errors.initial_balance = 'Use um valor decimal com até duas casas, como 1000.00.'
    setFieldErrors(errors)
    if (Object.keys(errors).length) return

    setSubmitting(true); setSubmitError(null)
    try {
      const created = await createAccount({ ...form, name: form.name.trim(), institution: form.institution?.trim() || null })
      setAccounts((current) => [...current, created].sort((a, b) => a.name.localeCompare(b.name, 'pt-BR')))
      showSuccess('Conta criada com sucesso.')
      setModalOpen(false); setForm(INITIAL_FORM)
    } catch (error) {
      const apiError = error as ApiClientError
      if (apiError.field) setFieldErrors({ [apiError.field]: apiError.message })
      else setSubmitError(apiError)
    } finally { setSubmitting(false) }
  }

  return (
    <div className="page-stack">
      <PageHeader eyebrow="Organização financeira" title="Contas" description="Cadastre os locais onde seus recursos estão. Nesta etapa, exibimos somente o saldo inicial informado." action={<Button onClick={() => setModalOpen(true)}><Plus size={18} />Nova conta</Button>} />

      {loading && <Card><LoadingState message="Carregando contas…" /></Card>}
      {!loading && loadError && <ErrorState message="Não foi possível carregar suas contas." requestId={loadError.requestId ?? undefined} onRetry={() => void load()} />}
      {!loading && !loadError && accounts.length === 0 && <Card><EmptyState title="Nenhuma conta cadastrada" description="Crie sua primeira conta para registrar onde seus recursos financeiros estão." action={<Button onClick={() => setModalOpen(true)}><Plus size={18} />Nova conta</Button>} /></Card>}
      {!loading && !loadError && accounts.length > 0 && (
        <div className="account-grid" aria-label="Contas cadastradas">
          {accounts.map((account) => (
            <Card className="account-card" key={account.id}>
              <div className="account-card__top"><span className="entity-icon"><WalletCards size={20} /></span><StatusBadge tone={account.is_active ? 'success' : 'neutral'}>{account.is_active ? 'Ativa' : 'Inativa'}</StatusBadge></div>
              <h2>{account.name}</h2>
              <p className="account-card__institution"><Building2 size={16} />{account.institution || 'Instituição não informada'}</p>
              <dl className="account-card__details">
                <div><dt>Tipo</dt><dd>{ACCOUNT_TYPE_LABELS[account.account_type]}</dd></div>
                <div><dt>Saldo inicial</dt><dd className="money-value">{formatMoneyBRL(account.initial_balance)}</dd></div>
                <div><dt><CalendarDays size={15} />Data do saldo inicial</dt><dd>{formatEconomicDate(account.initial_balance_date)}</dd></div>
              </dl>
            </Card>
          ))}
        </div>
      )}

      <Modal open={isModalOpen} title="Nova conta" description="Informe somente os dados iniciais disponíveis no contrato atual." onClose={closeModal}>
        <form className="form-stack" onSubmit={handleSubmit} noValidate>
          <FormField htmlFor="account-name" label="Nome" required error={fieldErrors.name}><Input id="account-name" autoFocus value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} aria-invalid={Boolean(fieldErrors.name)} aria-describedby={fieldErrors.name ? 'account-name-error' : undefined} /></FormField>
          <FormField htmlFor="account-institution" label="Instituição" helper="Opcional"><Input id="account-institution" value={form.institution ?? ''} onChange={(event) => setForm({ ...form, institution: event.target.value })} /></FormField>
          <FormField htmlFor="account-type" label="Tipo de conta" required><Select id="account-type" value={form.account_type} onChange={(event) => setForm({ ...form, account_type: event.target.value as AccountType })}>{Object.entries(ACCOUNT_TYPE_LABELS).map(([value, label]) => <option value={value} key={value}>{label}</option>)}</Select></FormField>
          <div className="form-grid">
            <FormField htmlFor="initial-balance" label="Saldo inicial" required error={fieldErrors.initial_balance} helper="Use ponto como separador decimal."><Input id="initial-balance" inputMode="decimal" value={form.initial_balance} onChange={(event) => setForm({ ...form, initial_balance: event.target.value })} aria-invalid={Boolean(fieldErrors.initial_balance)} aria-describedby={fieldErrors.initial_balance ? 'initial-balance-error' : 'initial-balance-helper'} /></FormField>
            <FormField htmlFor="initial-balance-date" label="Data do saldo inicial" helper="Opcional"><Input id="initial-balance-date" type="date" value={form.initial_balance_date ?? ''} onChange={(event) => setForm({ ...form, initial_balance_date: event.target.value || null })} /></FormField>
          </div>
          {submitError && <ErrorState message={submitError.message} requestId={submitError.requestId ?? undefined} />}
          <footer className="modal-actions"><Button type="button" variant="ghost" onClick={closeModal} disabled={submitting}>Cancelar</Button><Button type="submit" loading={submitting}>Salvar conta</Button></footer>
        </form>
      </Modal>
    </div>
  )
}
