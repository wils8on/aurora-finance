import type { EconomicDate } from '../types/api'

const ECONOMIC_DATE_PATTERN = /^(\d{4})-(\d{2})-(\d{2})$/

export function formatEconomicDate(value: EconomicDate | null): string {
  if (!value) return 'Não informada'
  const match = ECONOMIC_DATE_PATTERN.exec(value)
  if (!match) return value
  return `${match[3]}/${match[2]}/${match[1]}`
}

export function currentOperationalMonth(): { start: EconomicDate; end: EconomicDate; label: string } {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(new Date())
  const year = parts.find((part) => part.type === 'year')?.value ?? '1970'
  const month = parts.find((part) => part.type === 'month')?.value ?? '01'
  return monthPeriod(`${year}-${month}`)
}

export function monthPeriod(monthValue: string): { start: EconomicDate; end: EconomicDate; label: string } {
  const [year, month] = monthValue.split('-')
  const days = new Date(Date.UTC(Number(year), Number(month), 0)).getUTCDate()
  const label = new Intl.DateTimeFormat('pt-BR', { month: 'long', year: 'numeric', timeZone: 'UTC' })
    .format(new Date(`${year}-${month}-01T00:00:00Z`))
  return { start: `${year}-${month}-01`, end: `${year}-${month}-${String(days).padStart(2, '0')}`, label }
}

export function formatInstant(value: string): string {
  return new Intl.DateTimeFormat('pt-BR', {
    timeZone: 'America/Sao_Paulo', dateStyle: 'short', timeStyle: 'short',
  }).format(new Date(value))
}

export function operationalDateTimeToIso(value: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2}))?$/.exec(value)
  if (!match) return value
  const probe = new Date(Date.UTC(+match[1], +match[2] - 1, +match[3], +match[4], +match[5], +(match[6] ?? '0')))
  const offsetName = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/Sao_Paulo', timeZoneName: 'longOffset',
  }).formatToParts(probe).find((part) => part.type === 'timeZoneName')?.value
  const offset = /^GMT([+-]\d{2}:\d{2})$/.exec(offsetName ?? '')?.[1]
  return `${value.length === 16 ? `${value}:00` : value}${offset ?? '-03:00'}`
}
