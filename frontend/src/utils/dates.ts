import type { EconomicDate } from '../types/api'

const ECONOMIC_DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/

export function formatEconomicDate(value: EconomicDate | null): string {
  if (!value) return 'Não informada'
  const match = ECONOMIC_DATE_PATTERN.exec(value)
  if (!match) return value
  return `${match[3]}/${match[2]}/${match[1]}`
}
