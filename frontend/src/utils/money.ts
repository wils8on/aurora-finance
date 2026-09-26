import type { Money } from '../types/api'

const MONEY_PATTERN = /^-?(?:0|[1-9]\d*)(?:\.\d{1,2})?$/

export function isCanonicalMoney(value: string): value is Money {
  return MONEY_PATTERN.test(value)
}

export function formatMoneyBRL(value: Money): string {
  if (!isCanonicalMoney(value)) return value

  const negative = value.startsWith('-')
  const unsigned = negative ? value.slice(1) : value
  const [integerPart, decimalPart = ''] = unsigned.split('.')
  const grouped = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  const cents = decimalPart.padEnd(2, '0')
  return `${negative ? '- ' : ''}R$ ${grouped},${cents}`
}
