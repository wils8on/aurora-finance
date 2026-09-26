import { useState } from 'react'
import { cancelTransaction, createSettlement } from '../../api/transactions'
import { ApiClientError } from '../../api/client'
import { Button } from '../../components/base/Button'
import { FormField } from '../../components/base/FormField'
import { Input } from '../../components/base/Input'
import { Select } from '../../components/base/Select'
import { StatusBadge } from '../../components/base/StatusBadge'
import { ErrorState } from '../../components/feedback/ErrorState'
import type { Account, TransactionDetail as Detail } from '../../types/api'
import { formatEconomicDate, formatInstant, operationalDateTimeToIso } from '../../utils/dates'
import { formatMoneyBRL, isCanonicalMoney } from '../../utils/money'

const STATUS = { PENDING: 'Pendente', PARTIAL: 'Parcial', SETTLED: 'Liquidada', CANCELLED: 'Cancelada' } as const
const TONE = { PENDING: 'neutral', PARTIAL: 'info', SETTLED: 'success', CANCELLED: 'danger' } as const
interface Props { detail: Detail; accounts: Account[]; onChanged: (value: Detail, message: string) => void }

export function TransactionDetail({ detail, accounts, onChanged }: Props) {
  const [settling, setSettling] = useState(false)
  const [cancelling, setCancelling] = useState(false)
  const [accountId, setAccountId] = useState('')
  const [amount, setAmount] = useState(detail.remaining_amount)
  const [settledAt, setSettledAt] = useState('')
  const [notes, setNotes] = useState('')
  const [reason, setReason] = useState('')
  const [error, setError] = useState<ApiClientError | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const canSettle = detail.persisted_status === 'ACTIVE' && detail.remaining_amount !== '0.00'
  const canCancel = detail.persisted_status === 'ACTIVE' && detail.settlements.length === 0

  const addSettlement = async (event: React.FormEvent) => {
    event.preventDefault(); setError(null)
    const next: Record<string, string> = {}
    if (!accountId) next.account_id = 'Selecione a conta.'
    if (!isCanonicalMoney(amount) || amount === '0' || amount === '0.00' || amount.startsWith('-')) next.amount = 'Informe um valor positivo com até duas casas.'
    if (!settledAt) next.settled_at = 'Informe a data e hora da liquidação.'
    setFieldErrors(next)
    if (Object.keys(next).length) return
    setBusy(true)
    try {
      const updated = await createSettlement(detail.id, { account_id: Number(accountId), amount, settled_at: operationalDateTimeToIso(settledAt), notes: notes.trim() || null })
      setSettling(false)
      setFieldErrors({})
      onChanged(updated, 'Liquidação registrada com sucesso.')
    }
    catch (value) {
      const apiError = value as ApiClientError
      if (apiError.field && ['account_id', 'amount', 'settled_at'].includes(apiError.field)) setFieldErrors({ [apiError.field]: apiError.message })
      else setError(apiError)
    }
    finally { setBusy(false) }
  }
  const cancel = async (event: React.FormEvent) => {
    event.preventDefault(); setBusy(true); setError(null)
    try {
      const updated = await cancelTransaction(detail.id, { reason: reason.trim() || null })
      setCancelling(false)
      onChanged(updated, 'Movimentação cancelada com sucesso.')
    }
    catch (value) { setError(value as ApiClientError) }
    finally { setBusy(false) }
  }

  return <div className="transaction-detail">
    <div className="detail-heading"><div><span className="eyebrow">{detail.transaction_type === 'INCOME' ? 'Receita' : 'Despesa'}</span><h3>{detail.description}</h3></div><StatusBadge tone={TONE[detail.derived_status]}>{STATUS[detail.derived_status]}</StatusBadge></div>
    <dl className="detail-grid">
      <div><dt>Valor nominal</dt><dd>{formatMoneyBRL(detail.amount)}</dd></div><div><dt>Liquidado</dt><dd>{formatMoneyBRL(detail.settled_amount)}</dd></div><div><dt>Restante</dt><dd>{formatMoneyBRL(detail.remaining_amount)}</dd></div>
      <div><dt>Competência</dt><dd>{formatEconomicDate(detail.competence_date)}</dd></div><div><dt>Vencimento</dt><dd>{formatEconomicDate(detail.due_date)}</dd></div><div><dt>Categoria</dt><dd>{detail.category.name}{detail.subcategory ? ` · ${detail.subcategory.name}` : ''}</dd></div>
    </dl>
    {detail.notes && <section><h4>Observações</h4><p>{detail.notes}</p></section>}
    {detail.cancellation && <section className="cancellation-note"><h4>Cancelamento</h4><p>{formatInstant(detail.cancellation.cancelled_at)}{detail.cancellation.reason ? ` · ${detail.cancellation.reason}` : ''}</p></section>}
    <section><h4>Histórico de liquidações</h4>{detail.settlements.length === 0 ? <p className="muted">Nenhuma liquidação registrada.</p> : <ul className="settlement-history">{detail.settlements.map((item) => <li key={item.id}><div><strong>{item.account.name}</strong><span>{formatInstant(item.settled_at)}</span>{item.notes && <small>{item.notes}</small>}</div><b>{formatMoneyBRL(item.amount)}</b></li>)}</ul>}</section>
    {error && <ErrorState message={error.message} requestId={error.requestId ?? undefined} />}
    <div className="detail-actions">{canSettle && <Button type="button" onClick={() => { setSettling(!settling); setCancelling(false) }}>Registrar liquidação</Button>}{canCancel && <Button type="button" variant="danger" onClick={() => { setCancelling(!cancelling); setSettling(false) }}>Cancelar movimentação</Button>}</div>
    {settling && <form className="inline-operation form-stack" onSubmit={addSettlement} noValidate><p>Valor restante: <strong>{formatMoneyBRL(detail.remaining_amount)}</strong></p><div className="form-grid"><FormField htmlFor="settlement-account" label="Conta" required error={fieldErrors.account_id}><Select id="settlement-account" value={accountId} onChange={(e) => setAccountId(e.target.value)} aria-invalid={Boolean(fieldErrors.account_id)}><option value="">Selecione</option>{accounts.filter((item) => item.is_active).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</Select></FormField><FormField htmlFor="settlement-amount" label="Valor" required error={fieldErrors.amount}><Input id="settlement-amount" value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="decimal" aria-invalid={Boolean(fieldErrors.amount)} /></FormField></div><FormField htmlFor="settlement-at" label="Data e hora" required error={fieldErrors.settled_at}><Input id="settlement-at" type="datetime-local" value={settledAt} onChange={(e) => setSettledAt(e.target.value)} aria-invalid={Boolean(fieldErrors.settled_at)} /></FormField><FormField htmlFor="settlement-notes" label="Observações"><Input id="settlement-notes" value={notes} onChange={(e) => setNotes(e.target.value)} /></FormField><div className="modal-actions"><Button type="button" variant="ghost" onClick={() => setAmount(detail.remaining_amount)}>Liquidar restante</Button><Button type="submit" loading={busy}>Confirmar liquidação</Button></div></form>}
    {cancelling && <form className="inline-operation form-stack" onSubmit={cancel}><FormField htmlFor="cancellation-reason" label="Motivo" helper="Opcional"><Input id="cancellation-reason" value={reason} onChange={(e) => setReason(e.target.value)} /></FormField><div className="modal-actions"><Button type="submit" variant="danger" loading={busy}>Confirmar cancelamento</Button></div></form>}
  </div>
}
