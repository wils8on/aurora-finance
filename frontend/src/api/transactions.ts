import type {
  CancellationCreate, SettlementCreate, SettledTransactionCreate, TransactionCreate,
  TransactionDetail, TransactionPage, TransactionQuery, TransactionSummary,
} from '../types/api'
import { apiGet, apiPost } from './client'

function queryString(query: TransactionQuery): string {
  const params = new URLSearchParams()
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== '' && value !== false) params.set(key, String(value))
  })
  return params.toString()
}

export function listTransactions(query: TransactionQuery): Promise<TransactionPage> {
  return apiGet<TransactionPage>(`/transactions?${queryString(query)}`)
}
export function getTransaction(id: number): Promise<TransactionDetail> {
  return apiGet<TransactionDetail>(`/transactions/${id}`)
}
export function createTransaction(payload: TransactionCreate): Promise<TransactionDetail> {
  return apiPost<TransactionDetail, TransactionCreate>('/transactions', payload)
}
export function createSettledTransaction(payload: SettledTransactionCreate): Promise<TransactionDetail> {
  return apiPost<TransactionDetail, SettledTransactionCreate>('/transactions/settled', payload)
}
export function createSettlement(id: number, payload: SettlementCreate): Promise<TransactionDetail> {
  return apiPost<TransactionDetail, SettlementCreate>(`/transactions/${id}/settlements`, payload)
}
export function cancelTransaction(id: number, payload: CancellationCreate): Promise<TransactionDetail> {
  return apiPost<TransactionDetail, CancellationCreate>(`/transactions/${id}/cancellation`, payload)
}
export function getTransactionSummary(query: TransactionQuery): Promise<TransactionSummary> {
  return apiGet<TransactionSummary>(`/transaction-summaries?${queryString(query)}`)
}
