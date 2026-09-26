import { describe, expect, it } from 'vitest'
import { formatEconomicDate } from './dates'
import { formatMoneyBRL } from './money'

describe('formatação financeira segura', () => {
  it('formata dinheiro diretamente da string decimal', () => {
    const money: string = '1234567890123456.78'
    expect(formatMoneyBRL(money)).toBe('R$ 1.234.567.890.123.456,78')
  })

  it('formata data econômica sem construir Date', () => {
    expect(formatEconomicDate('2026-09-24')).toBe('24/09/2026')
  })
})
