import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { CategoriesPage } from './CategoriesPage'
import { jsonResponse, renderWithProviders } from '../../test/render'

const categories = [
  { id: 1, name: 'Salário', type: 'INCOME', is_active: true },
  { id: 2, name: 'Moradia', type: 'EXPENSE', is_active: true },
]

describe('CategoriesPage', () => {
  beforeEach(() => vi.restoreAllMocks())

  it('exibe loading', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => undefined)))
    renderWithProviders(<CategoriesPage />)
    expect(screen.getByText('Carregando categorias…')).toBeInTheDocument()
  })

  it('exibe estado vazio', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse([])))
    renderWithProviders(<CategoriesPage />)
    expect(await screen.findByText('Nenhuma categoria cadastrada')).toBeInTheDocument()
  })

  it('lista categorias e traduz INCOME/EXPENSE textualmente', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse(categories)))
    renderWithProviders(<CategoriesPage />)
    expect(await screen.findByText('Salário')).toBeInTheDocument()
    expect(screen.getByText('Receita')).toBeInTheDocument()
    expect(screen.getByText('Despesa')).toBeInTheDocument()
  })

  it('cria Categoria com enum real', async () => {
    let payload: Record<string, unknown> = {}
    const fetchMock = vi.fn().mockImplementation((_url: string, options?: RequestInit) => {
      if (options?.method === 'POST') {
        payload = JSON.parse(options.body as string)
        return Promise.resolve(jsonResponse({ id: 3, name: 'Lazer', type: 'EXPENSE', is_active: true }, 201))
      }
      return Promise.resolve(jsonResponse([]))
    })
    vi.stubGlobal('fetch', fetchMock)
    renderWithProviders(<CategoriesPage />)
    await screen.findByText('Nenhuma categoria cadastrada')
    await userEvent.click(screen.getAllByRole('button', { name: /Nova categoria/ })[0])
    await userEvent.type(screen.getByLabelText('Nome *'), 'Lazer')
    await userEvent.click(screen.getByRole('button', { name: 'Salvar categoria' }))
    expect(await screen.findByText('Categoria criada com sucesso.')).toBeInTheDocument()
    expect(screen.getByText('Lazer')).toBeInTheDocument()
    expect(payload).toEqual({ name: 'Lazer', type: 'EXPENSE' })
  })

  it('expande Categoria e carrega Subcategorias', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.endsWith('/categories/2/subcategories')) return Promise.resolve(jsonResponse([{ id: 10, name: 'Aluguel', is_active: true }]))
      return Promise.resolve(jsonResponse(categories))
    })
    vi.stubGlobal('fetch', fetchMock)
    renderWithProviders(<CategoriesPage />)
    await screen.findByText('Moradia')
    await userEvent.click(screen.getByRole('button', { name: 'Expandir Moradia' }))
    expect(await screen.findByText('Aluguel')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/categories/2/subcategories'), expect.anything())
  })

  it('cria Subcategoria no contexto da Categoria e atualiza sem reload', async () => {
    let postUrl = ''
    let postPayload: Record<string, unknown> = {}
    const fetchMock = vi.fn().mockImplementation((url: string, options?: RequestInit) => {
      if (options?.method === 'POST') {
        postUrl = url
        postPayload = JSON.parse(options.body as string)
        return Promise.resolve(jsonResponse({ id: 11, name: 'Energia', is_active: true }, 201))
      }
      if (url.endsWith('/subcategories')) return Promise.resolve(jsonResponse([]))
      return Promise.resolve(jsonResponse([categories[1]]))
    })
    vi.stubGlobal('fetch', fetchMock)
    renderWithProviders(<CategoriesPage />)
    await screen.findByText('Moradia')
    await userEvent.click(screen.getByRole('button', { name: 'Nova subcategoria' }))
    expect(screen.getByText('Categoria: Moradia')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Nome *'), 'Energia')
    await userEvent.click(screen.getByRole('button', { name: 'Salvar subcategoria' }))
    expect(await screen.findByText('Subcategoria criada com sucesso.')).toBeInTheDocument()
    expect(screen.getByText('Energia')).toBeInTheDocument()
    expect(postUrl).toContain('/categories/2/subcategories')
    expect(postPayload).toEqual({ name: 'Energia' })
  })

  it('exibe erro de carregamento das categorias', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(jsonResponse({ error: { code: 'FAIL', message: 'Falha', field: null, details: {}, request_id: 'req' } }, 500)))
    renderWithProviders(<CategoriesPage />)
    expect(await screen.findByText('Não foi possível carregar suas categorias.')).toBeInTheDocument()
  })
})
