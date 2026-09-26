import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AccountsPage } from './AccountsPage'
import { jsonResponse, renderWithProviders } from '../../test/render'

const account = {
  id: 1,
  name: 'Conta principal',
  institution: 'Banco Aurora',
  account_type: 'CHECKING',
  initial_balance: '1234.56',
  initial_balance_date: '2026-09-24',
  is_active: true,
}

describe('AccountsPage', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('exibe loading', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => undefined)))
    renderWithProviders(<AccountsPage />)
    expect(screen.getByText('Carregando contas…')).toBeInTheDocument()
  })

  it('exibe estado vazio', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse([])))
    renderWithProviders(<AccountsPage />)
    expect(await screen.findByText('Nenhuma conta cadastrada')).toBeInTheDocument()
  })

  it('exibe erro e retry', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(jsonResponse({ error: { code: 'FAIL', message: 'Falha', field: null, details: {}, request_id: 'req-1' } }, 500))
      .mockResolvedValueOnce(jsonResponse([]))
    vi.stubGlobal('fetch', fetchMock)
    renderWithProviders(<AccountsPage />)
    await userEvent.click(await screen.findByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByText('Nenhuma conta cadastrada')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it('lista somente informações reais e distingue saldo inicial', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse([account])))
    renderWithProviders(<AccountsPage />)
    expect(await screen.findByText('Conta principal')).toBeInTheDocument()
    expect(screen.getByText('R$ 1.234,56')).toBeInTheDocument()
    expect(screen.getByText('24/09/2026')).toBeInTheDocument()
    expect(screen.getByText('Saldo inicial')).toBeInTheDocument()
    expect(screen.queryByText('Saldo atual')).not.toBeInTheDocument()
  })

  it('abre o modal Nova Conta', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse([])))
    renderWithProviders(<AccountsPage />)
    await screen.findByText('Nenhuma conta cadastrada')
    await userEvent.click(screen.getAllByRole('button', { name: /Nova conta/ })[0])
    expect(screen.getByRole('dialog', { name: 'Nova conta' })).toBeInTheDocument()
    expect(screen.getByLabelText('Saldo inicial *')).toHaveValue('0.00')
  })

  it('cria conta e mantém dinheiro como string no contrato', async () => {
    let sentPayload: Record<string, unknown> = {}
    const fetchMock = vi.fn().mockImplementation((_url: string, options?: RequestInit) => {
      if (options?.method === 'POST') {
        sentPayload = JSON.parse(options.body as string)
        return Promise.resolve(jsonResponse(account, 201))
      }
      return Promise.resolve(jsonResponse([]))
    })
    vi.stubGlobal('fetch', fetchMock)
    renderWithProviders(<AccountsPage />)
    await screen.findByText('Nenhuma conta cadastrada')
    await userEvent.click(screen.getAllByRole('button', { name: /Nova conta/ })[0])
    await userEvent.type(screen.getByLabelText('Nome *'), 'Conta principal')
    await userEvent.clear(screen.getByLabelText('Saldo inicial *'))
    await userEvent.type(screen.getByLabelText('Saldo inicial *'), '1234.56')
    await userEvent.click(screen.getByRole('button', { name: 'Salvar conta' }))
    expect(await screen.findByText('Conta criada com sucesso.')).toBeInTheDocument()
    expect(screen.getByText('Conta principal')).toBeInTheDocument()
    expect(sentPayload.initial_balance).toBe('1234.56')
    expect(typeof sentPayload.initial_balance).toBe('string')
    expect(sentPayload).not.toHaveProperty('user_id')
  })

  it('associa conflito da API ao campo nome', async () => {
    const fetchMock = vi.fn().mockImplementation((_url: string, options?: RequestInit) => {
      if (options?.method === 'POST') return Promise.resolve(jsonResponse({ error: { code: 'ACCOUNT_NAME_CONFLICT', message: 'Já existe uma Account ativa com esse nome.', field: 'name', details: {}, request_id: 'req-conflict' } }, 409))
      return Promise.resolve(jsonResponse([]))
    })
    vi.stubGlobal('fetch', fetchMock)
    renderWithProviders(<AccountsPage />)
    await screen.findByText('Nenhuma conta cadastrada')
    await userEvent.click(screen.getAllByRole('button', { name: /Nova conta/ })[0])
    await userEvent.type(screen.getByLabelText('Nome *'), 'Duplicada')
    await userEvent.click(screen.getByRole('button', { name: 'Salvar conta' }))
    expect(await screen.findByText('Já existe uma Account ativa com esse nome.')).toBeInTheDocument()
    expect(screen.getByLabelText('Nome *')).toHaveAttribute('aria-invalid', 'true')
    await waitFor(() => expect(screen.getByRole('dialog')).toBeInTheDocument())
  })
})
