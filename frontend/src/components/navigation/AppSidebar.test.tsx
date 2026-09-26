import { screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AppSidebar } from './AppSidebar'
import { jsonResponse, renderWithProviders } from '../../test/render'

describe('AppSidebar', () => {
  const user = { id: 1, name: 'Pessoa Teste', email: 'pessoa@example.com', currency: 'BRL' }

  it('mostra o health discretamente no rodapé', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ status: 'ok' })))
    renderWithProviders(<AppSidebar isOpen onClose={() => undefined} user={user} onLogout={vi.fn()} />)
    expect(await screen.findByText('Sistema conectado')).toBeInTheDocument()
    expect(screen.getByText('API disponível')).toBeInTheDocument()
  })

  it('expõe itens futuros como indisponíveis e sem navegação', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => undefined)))
    renderWithProviders(<AppSidebar isOpen onClose={() => undefined} user={user} onLogout={vi.fn()} />)
    const budget = screen.getByText('Orçamento').closest('li')
    expect(budget).toHaveAttribute('aria-disabled', 'true')
    expect(screen.queryByRole('link', { name: /Orçamento/ })).not.toBeInTheDocument()
  })
})
