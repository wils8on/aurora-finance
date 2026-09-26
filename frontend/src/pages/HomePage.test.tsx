import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { HomePage } from './HomePage'
import { renderWithProviders } from '../test/render'

describe('HomePage', () => {
  it('renderiza a landing sem dados financeiros falsos', () => {
    renderWithProviders(<HomePage />)
    expect(screen.getByRole('heading', { name: 'Clareza para suas decisões financeiras.' })).toBeInTheDocument()
    expect(screen.getByText('Visão completa')).toBeInTheDocument()
    expect(screen.queryByText(/saldo atual/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/receita mensal/i)).not.toBeInTheDocument()
  })
})
