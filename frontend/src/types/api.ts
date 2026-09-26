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
