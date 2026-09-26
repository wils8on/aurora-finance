export interface HealthResponse {
  status: string
}

export interface ApiError {
  code: string
  message: string
  field: string | null
  details: Record<string, unknown>
  request_id: string | null
}

export interface ApiErrorEnvelope {
  error: ApiError
}

export type Money = string
export type EconomicDate = string
export type AccountType = 'CHECKING' | 'SAVINGS' | 'CASH' | 'DIGITAL' | 'OTHER'
export type CategoryType = 'INCOME' | 'EXPENSE'

export interface Account {
  id: number
  name: string
  institution: string | null
  account_type: AccountType
  initial_balance: Money
  initial_balance_date: EconomicDate | null
  is_active: boolean
}

export interface AccountCreate {
  name: string
  institution: string | null
  account_type: AccountType
  initial_balance: Money
  initial_balance_date: EconomicDate | null
}

export interface Category {
  id: number
  name: string
  type: CategoryType
  is_active: boolean
}

export interface CategoryCreate {
  name: string
  type: CategoryType
}

export interface Subcategory {
  id: number
  name: string
  is_active: boolean
}

export interface SubcategoryCreate {
  name: string
}

export type TransactionType = 'INCOME' | 'EXPENSE'
export type TransactionStatus = 'ACTIVE' | 'CANCELLED'
export type DerivedTransactionStatus = 'PENDING' | 'PARTIAL' | 'SETTLED' | 'CANCELLED'
export type DatePerspective = 'COMPETENCE' | 'DUE' | 'CASH'

export interface NamedReference { id: number; name: string }
export interface Settlement {
  id: number
  account: NamedReference
  amount: Money
  settled_at: string
  notes: string | null
}
export interface TransactionCancellation { cancelled_at: string; reason: string | null }
export interface TransactionListItem {
  id: number
  transaction_type: TransactionType
  derived_status: DerivedTransactionStatus
  description: string
  amount: Money
  settled_amount: Money
  remaining_amount: Money
  period_settled_amount: Money
  competence_date: EconomicDate
  due_date: EconomicDate | null
  reference_date: EconomicDate
  category: NamedReference
  subcategory: NamedReference | null
}
export interface TransactionDetail extends Omit<TransactionListItem, 'period_settled_amount' | 'reference_date'> {
  persisted_status: TransactionStatus
  notes: string | null
  cancellation: TransactionCancellation | null
  settlements: Settlement[]
}
export interface Pagination { page: number; page_size: number; total_items: number; total_pages: number }
export interface TransactionPage { items: TransactionListItem[]; pagination: Pagination }
export interface TransactionSummary {
  perspective: DatePerspective
  primary_1: Money
  primary_2: Money
  primary_3: Money
  receivable: Money
  payable: Money
}
export interface TransactionCreate {
  transaction_type: TransactionType
  description: string
  amount: Money
  competence_date: EconomicDate
  due_date: EconomicDate | null
  category_id: number
  subcategory_id: number | null
  notes: string | null
}
export interface SettlementCreate { account_id: number; amount: Money; settled_at: string; notes: string | null }
export interface SettledTransactionCreate extends Omit<TransactionCreate, 'notes'> {
  transaction_notes: string | null
  settlement: SettlementCreate
}
export interface CancellationCreate { reason: string | null }
export interface TransactionQuery {
  perspective: DatePerspective
  start_date: EconomicDate
  end_date: EconomicDate
  transaction_type?: TransactionType
  derived_status?: DerivedTransactionStatus
  category_id?: number
  subcategory_id?: number
  search?: string
  include_cancelled?: boolean
  page: number
  page_size: number
}
