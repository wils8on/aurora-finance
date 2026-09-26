import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from '../../App'
import { ToastProvider } from '../../components/feedback/Toast'
import { jsonResponse } from '../../test/render'

const session = {
  user: { id: 1, name: 'Pessoa Aurora', email: 'aurora@example.com', currency: 'BRL' },
  csrf_token: 'csrf-test-token',
}
const unauthorized = () => jsonResponse({ error: { code: 'AUTHENTICATION_REQUIRED', message: 'Autenticação necessária.', field: null, details: {}, request_id: 'test' } }, 401)

function renderApp(initialEntry = '/') {
  return render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <ToastProvider><App /></ToastProvider>
    </MemoryRouter>,
  )
}

afterEach(() => vi.unstubAllGlobals())

describe('fluxo de autenticação', () => {
  it('mostra loading enquanto verifica a sessão inicial', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => undefined)))
    renderApp()
    expect(screen.getByText('Verificando sessão…')).toBeInTheDocument()
  })

  it('mostra login sem sessão e não repete /auth/me em loop', async () => {
    const fetchMock = vi.fn().mockResolvedValue(unauthorized())
    vi.stubGlobal('fetch', fetchMock)
    renderApp('/contas')
    expect(await screen.findByRole('heading', { name: 'Entre na sua vida financeira' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(String(fetchMock.mock.calls[0][0])).toContain('/auth/me')
  })

  it('faz login válido, preserva a rota e apresenta a identidade real', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) return unauthorized()
      if (url.endsWith('/auth/login')) return jsonResponse(session)
      if (url.endsWith('/accounts')) return jsonResponse([])
      if (url.endsWith('/health')) return jsonResponse({ status: 'ok' })
      throw new Error(`URL inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)
    renderApp('/contas')
    await userEvent.type(await screen.findByRole('textbox', { name: /Email/ }), 'aurora@example.com')
    await userEvent.type(screen.getByLabelText(/Senha/), 'frase-secreta-longa')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('heading', { name: 'Contas' })).toBeInTheDocument()
    expect(screen.getByText('Pessoa Aurora')).toBeInTheDocument()
    expect(screen.getByText('aurora@example.com')).toBeInTheDocument()
    const loginCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/auth/login'))
    expect(loginCall?.[1]).toMatchObject({ credentials: 'include', method: 'POST' })
  })

  it('exibe erro de credenciais sem sair do login', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      if (String(input).endsWith('/auth/me')) return unauthorized()
      return jsonResponse({ error: { code: 'INVALID_CREDENTIALS', message: 'Email ou senha inválidos.', field: null, details: {}, request_id: 'test' } }, 401)
    })
    vi.stubGlobal('fetch', fetchMock)
    renderApp()
    await userEvent.type(await screen.findByRole('textbox', { name: /Email/ }), 'aurora@example.com')
    await userEvent.type(screen.getByLabelText(/Senha/), 'senha-incorreta')
    await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Email ou senha inválidos.')
  })

  it('faz logout no servidor, envia CSRF e volta ao login', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) return jsonResponse(session)
      if (url.endsWith('/auth/logout')) return jsonResponse({ authenticated: false })
      if (url.endsWith('/health')) return jsonResponse({ status: 'ok' })
      throw new Error(`URL inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)
    renderApp()
    await userEvent.click(await screen.findByRole('button', { name: 'Sair' }))
    expect(await screen.findByRole('heading', { name: 'Entre na sua vida financeira' })).toBeInTheDocument()
    const logoutCall = fetchMock.mock.calls.find(([input]) => String(input).endsWith('/auth/logout'))
    expect(new Headers(logoutCall?.[1]?.headers).get('X-CSRF-Token')).toBe('csrf-test-token')
  })

  it('remove dados financeiros da tela ao receber 401 durante uma chamada protegida', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/auth/me')) return jsonResponse(session)
      if (url.endsWith('/accounts')) return unauthorized()
      if (url.endsWith('/health')) return jsonResponse({ status: 'ok' })
      throw new Error(`URL inesperada: ${url}`)
    })
    vi.stubGlobal('fetch', fetchMock)
    renderApp('/contas')
    expect(await screen.findByRole('heading', { name: 'Entre na sua vida financeira' })).toBeInTheDocument()
    await waitFor(() => expect(screen.queryByRole('heading', { name: 'Contas' })).not.toBeInTheDocument())
  })
})
