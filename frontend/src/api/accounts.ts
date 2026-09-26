import type { Account, AccountCreate } from '../types/api'
import { apiGet, apiPost } from './client'

export function listAccounts(): Promise<Account[]> {
  return apiGet<Account[]>('/accounts')
}

export function createAccount(payload: AccountCreate): Promise<Account> {
  return apiPost<Account, AccountCreate>('/accounts', payload)
}
