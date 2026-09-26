import { fireEvent, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { renderWithProviders } from '../../test/render'
import type { TransactionDetail, TransactionListItem } from '../../types/api'
import { TransactionsPage } from './TransactionsPage'
import * as transactionsApi from '../../api/transactions'
import * as accountsApi from '../../api/accounts'
import * as categoriesApi from '../../api/categories'

vi.mock('../../api/transactions')
vi.mock('../../api/accounts')
vi.mock('../../api/categories')

const item: TransactionListItem = { id: 1, transaction_type: 'EXPENSE', derived_status: 'PARTIAL', description: 'Aluguel', amount: '1000.00', settled_amount: '400.00', remaining_amount: '600.00', period_settled_amount: '400.00', competence_date: '2026-09-01', due_date: '2026-09-10', reference_date: '2026-09-01', category: { id: 1, name: 'Moradia' }, subcategory: { id: 2, name: 'Aluguel' } }
const detail: TransactionDetail = { ...item, persisted_status: 'ACTIVE', notes: 'Contrato', cancellation: null, settlements: [{ id: 3, account: { id: 4, name: 'Principal' }, amount: '400.00', settled_at: '2026-09-10T15:00:00Z', notes: 'PIX' }] }
const page = { items: [item], pagination: { page: 1, page_size: 10, total_items: 11, total_pages: 2 } }
const summary = { perspective: 'COMPETENCE' as const, primary_1: '5000.00', primary_2: '1000.00', primary_3: '4000.00', receivable: '5000.00', payable: '600.00' }
const categories = [{ id: 1, name: 'Moradia', type: 'EXPENSE' as const, is_active: true }, { id: 8, name: 'Salário', type: 'INCOME' as const, is_active: true }]
const accounts = [{ id: 4, name: 'Principal', institution: null, account_type: 'CHECKING' as const, initial_balance: '0.00', initial_balance_date: null, is_active: true }]

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(transactionsApi.listTransactions).mockResolvedValue(page)
  vi.mocked(transactionsApi.getTransactionSummary).mockResolvedValue(summary)
  vi.mocked(transactionsApi.getTransaction).mockResolvedValue(detail)
  vi.mocked(transactionsApi.createTransaction).mockResolvedValue(detail)
  vi.mocked(transactionsApi.createSettledTransaction).mockResolvedValue({ ...detail, derived_status: 'SETTLED', remaining_amount: '0.00' })
  vi.mocked(transactionsApi.createSettlement).mockResolvedValue({ ...detail, derived_status: 'SETTLED', settled_amount: '1000.00', remaining_amount: '0.00' })
  vi.mocked(transactionsApi.cancelTransaction).mockResolvedValue({ ...detail, persisted_status: 'CANCELLED', derived_status: 'CANCELLED', settlements: [] })
  vi.mocked(accountsApi.listAccounts).mockResolvedValue(accounts)
  vi.mocked(categoriesApi.listCategories).mockResolvedValue(categories)
  vi.mocked(categoriesApi.listSubcategories).mockResolvedValue([{ id: 2, name: 'Aluguel', is_active: true }])
})

describe('Movimentações Web', () => {
  it('renderiza competência por padrão, período, resumo real e listagem derivada', async () => {
    renderWithProviders(<TransactionsPage />)
    expect(screen.getByRole('button', { name: 'Competência' })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('Carregando movimentações…')).toBeInTheDocument()
    expect(await screen.findByText('Aluguel')).toBeInTheDocument()
    expect(screen.getAllByText('Parcial')).toHaveLength(2)
    expect(screen.getByText('R$ 4.000,00')).toBeInTheDocument()
    expect(transactionsApi.listTransactions).toHaveBeenCalledWith(expect.objectContaining({ perspective: 'COMPETENCE', page: 1, page_size: 10 }))
  })

  it('exibe empty state', async () => {
    vi.mocked(transactionsApi.listTransactions).mockResolvedValue({ items: [], pagination: { page: 1, page_size: 10, total_items: 0, total_pages: 1 } })
    renderWithProviders(<TransactionsPage />)
    expect(await screen.findByText('Nenhuma movimentação no período')).toBeInTheDocument()
  })

  it('exibe erro e permite tentar novamente', async () => {
    vi.mocked(transactionsApi.listTransactions).mockRejectedValueOnce(new Error('falha')).mockResolvedValue(page)
    renderWithProviders(<TransactionsPage />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
    expect(await screen.findByText('Aluguel')).toBeInTheDocument()
  })

  it('envia perspectiva, filtros suportados e paginação para a API', async () => {
    renderWithProviders(<TransactionsPage />); await screen.findByText('Aluguel')
    await userEvent.click(screen.getByRole('button', { name: 'Caixa' }))
    await userEvent.selectOptions(screen.getByLabelText('Tipo'), 'EXPENSE')
    await userEvent.selectOptions(screen.getByLabelText('Estado'), 'PARTIAL')
    await userEvent.type(screen.getByLabelText('Buscar'), 'alugu')
    await userEvent.click(screen.getByRole('button', { name: /Próxima/ }))
    await waitFor(() => expect(transactionsApi.listTransactions).toHaveBeenCalledWith(expect.objectContaining({ perspective: 'CASH', transaction_type: 'EXPENSE', derived_status: 'PARTIAL', search: 'alugu', page: 2 })))
  })

  it('aceita intervalo arbitrário e envia as duas datas à API', async () => {
    renderWithProviders(<TransactionsPage />); await screen.findByText('Aluguel')
    fireEvent.change(screen.getByLabelText('De'), { target: { value: '2026-08-15' } })
    fireEvent.change(screen.getByLabelText('Até'), { target: { value: '2026-10-05' } })
    await waitFor(() => expect(transactionsApi.listTransactions).toHaveBeenCalledWith(expect.objectContaining({ start_date: '2026-08-15', end_date: '2026-10-05' })))
  })

  it('distingue o liquidado no período do total na perspectiva de caixa', async () => {
    renderWithProviders(<TransactionsPage />); await screen.findByText('Aluguel')
    await userEvent.click(screen.getByRole('button', { name: 'Caixa' }))
    await waitFor(() => expect(screen.getByText('Liquidado no período')).toBeInTheDocument())
    expect(screen.getByText('Liquidado total')).toBeInTheDocument()
    expect(screen.getAllByText('R$ 400,00')).toHaveLength(2)
  })

  it('abre formulário e valida campos obrigatórios', async () => {
    renderWithProviders(<TransactionsPage />); await screen.findByText('Aluguel')
    await userEvent.click(screen.getByRole('button', { name: 'Nova movimentação' }))
    const dialog = screen.getByRole('dialog', { name: 'Nova movimentação' })
    await userEvent.click(within(dialog).getByRole('button', { name: 'Salvar movimentação' }))
    expect(within(dialog).getByText('Informe a descrição.')).toBeInTheDocument()
    expect(within(dialog).getByText('Informe um valor positivo com até duas casas.')).toBeInTheDocument()
  })

  it('cria pendente com money string e dependência categoria-subcategoria', async () => {
    renderWithProviders(<TransactionsPage />); await screen.findByText('Aluguel')
    await userEvent.click(screen.getByRole('button', { name: 'Nova movimentação' }))
    const dialog = screen.getByRole('dialog', { name: 'Nova movimentação' })
    await userEvent.type(within(dialog).getByLabelText('Descrição *'), 'Energia')
    await userEvent.type(within(dialog).getByLabelText('Valor *'), '250.55')
    fireEvent.change(within(dialog).getByLabelText('Competência *'), { target: { value: '2026-09-01' } })
    await userEvent.selectOptions(within(dialog).getByLabelText('Categoria *'), '1')
    expect(categoriesApi.listSubcategories).toHaveBeenCalledWith(1)
    await waitFor(() => expect(within(dialog).getByRole('option', { name: 'Aluguel' })).toBeInTheDocument())
    await userEvent.selectOptions(within(dialog).getByLabelText('Subcategoria'), '2')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Salvar movimentação' }))
    await waitFor(() => expect(transactionsApi.createTransaction).toHaveBeenCalledWith(expect.objectContaining({ description: 'Energia', amount: '250.55', category_id: 1, subcategory_id: 2 })))
    expect(typeof vi.mocked(transactionsApi.createTransaction).mock.calls[0][0].amount).toBe('string')
  })

  it('usa endpoint atômico para criação já liquidada', async () => {
    renderWithProviders(<TransactionsPage />); await screen.findByText('Aluguel')
    await userEvent.click(screen.getByRole('button', { name: 'Nova movimentação' }))
    const dialog = screen.getByRole('dialog', { name: 'Nova movimentação' })
    await userEvent.type(within(dialog).getByLabelText('Descrição *'), 'Histórica')
    await userEvent.type(within(dialog).getByLabelText('Valor *'), '90.00')
    fireEvent.change(within(dialog).getByLabelText('Competência *'), { target: { value: '2026-09-01' } })
    await userEvent.selectOptions(within(dialog).getByLabelText('Categoria *'), '1')
    await userEvent.click(within(dialog).getByRole('checkbox', { name: /Registrar como já realizada/ }))
    await userEvent.selectOptions(within(dialog).getByLabelText('Conta *'), '4')
    fireEvent.change(within(dialog).getByLabelText('Data e hora da liquidação *'), { target: { value: '2026-09-10T12:00' } })
    await userEvent.click(within(dialog).getByRole('button', { name: 'Salvar movimentação' }))
    await waitFor(() => expect(transactionsApi.createSettledTransaction).toHaveBeenCalledWith(expect.objectContaining({ amount: '90.00', settlement: expect.objectContaining({ amount: '90.00', settled_at: '2026-09-10T12:00:00-03:00' }) })))
    expect(transactionsApi.createTransaction).not.toHaveBeenCalled()
  })

  it('abre detalhe, mostra histórico e registra liquidação parcial/restante', async () => {
    renderWithProviders(<TransactionsPage />); await userEvent.click(await screen.findByText('Aluguel'))
    const dialog = await screen.findByRole('dialog', { name: 'Detalhe da movimentação' })
    expect(within(dialog).getByText('Histórico de liquidações')).toBeInTheDocument()
    expect(within(dialog).getByText('PIX')).toBeInTheDocument()
    await userEvent.click(within(dialog).getByRole('button', { name: 'Registrar liquidação' }))
    expect(within(dialog).getByText('Valor restante:')).toBeInTheDocument()
    await userEvent.selectOptions(within(dialog).getByLabelText('Conta *'), '4')
    fireEvent.change(within(dialog).getByLabelText('Data e hora *'), { target: { value: '2026-09-11T10:00' } })
    await userEvent.click(within(dialog).getByRole('button', { name: 'Liquidar restante' }))
    await userEvent.click(within(dialog).getByRole('button', { name: 'Confirmar liquidação' }))
    await waitFor(() => expect(transactionsApi.createSettlement).toHaveBeenCalledWith(1, expect.objectContaining({ amount: '600.00' })))
    expect(within(dialog).queryByRole('button', { name: 'Confirmar liquidação' })).not.toBeInTheDocument()
  })

  it('mostra erro da liquidação sem fechar detalhe', async () => {
    vi.mocked(transactionsApi.createSettlement).mockRejectedValue(new Error('excede'))
    renderWithProviders(<TransactionsPage />); await userEvent.click(await screen.findByText('Aluguel'))
    const dialog = await screen.findByRole('dialog', { name: 'Detalhe da movimentação' })
    await userEvent.click(within(dialog).getByRole('button', { name: 'Registrar liquidação' }))
    await userEvent.selectOptions(within(dialog).getByLabelText('Conta *'), '4')
    fireEvent.change(within(dialog).getByLabelText('Data e hora *'), { target: { value: '2026-09-11T10:00' } })
    await userEvent.click(within(dialog).getByRole('button', { name: 'Confirmar liquidação' }))
    expect(await within(dialog).findByRole('alert')).toBeInTheDocument()
  })

  it('expõe validações locais dos campos obrigatórios da liquidação', async () => {
    renderWithProviders(<TransactionsPage />); await userEvent.click(await screen.findByText('Aluguel'))
    const dialog = await screen.findByRole('dialog', { name: 'Detalhe da movimentação' })
    await userEvent.click(within(dialog).getByRole('button', { name: 'Registrar liquidação' }))
    fireEvent.change(within(dialog).getByLabelText('Valor *'), { target: { value: '' } })
    await userEvent.click(within(dialog).getByRole('button', { name: 'Confirmar liquidação' }))
    expect(within(dialog).getByText('Selecione a conta.')).toBeInTheDocument()
    expect(within(dialog).getByText('Informe um valor positivo com até duas casas.')).toBeInTheDocument()
    expect(within(dialog).getByText('Informe a data e hora da liquidação.')).toBeInTheDocument()
    expect(transactionsApi.createSettlement).not.toHaveBeenCalled()
  })

  it('permite cancelamento apenas sem liquidações conhecidas', async () => {
    vi.mocked(transactionsApi.getTransaction).mockResolvedValueOnce({ ...detail, derived_status: 'PENDING', settled_amount: '0.00', remaining_amount: '1000.00', settlements: [] })
    renderWithProviders(<TransactionsPage />); await userEvent.click(await screen.findByText('Aluguel'))
    let dialog = await screen.findByRole('dialog', { name: 'Detalhe da movimentação' })
    await userEvent.click(within(dialog).getByRole('button', { name: 'Cancelar movimentação' }))
    await userEvent.type(within(dialog).getByLabelText('Motivo'), 'Duplicada')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Confirmar cancelamento' }))
    await waitFor(() => expect(transactionsApi.cancelTransaction).toHaveBeenCalledWith(1, { reason: 'Duplicada' }))
    vi.mocked(transactionsApi.getTransaction).mockResolvedValue(detail)
    await userEvent.click(within(dialog).getByRole('button', { name: 'Fechar' }))
    await userEvent.click(screen.getByText('Aluguel'))
    dialog = await screen.findByRole('dialog', { name: 'Detalhe da movimentação' })
    expect(within(dialog).queryByRole('button', { name: 'Cancelar movimentação' })).not.toBeInTheDocument()
  })
})
