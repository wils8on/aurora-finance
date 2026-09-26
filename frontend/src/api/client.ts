import type { ApiError, ApiErrorEnvelope } from '../types/api'

const DEFAULT_TIMEOUT_MS = 8_000
const configuredBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim()
let csrfToken: string | null = null
let unauthorizedHandler: (() => void) | null = null

export const API_BASE_URL = (
  configuredBaseUrl || 'http://localhost:8000/api/v1'
).replace(/\/$/, '')

export class ApiClientError extends Error {
  readonly code: string
  readonly field: string | null
  readonly details: Record<string, unknown>
  readonly requestId: string | null
  readonly status: number

  constructor(error: ApiError, status: number) {
    super(error.message)
    this.name = 'ApiClientError'
    this.code = error.code
    this.field = error.field
    this.details = error.details
    this.requestId = error.request_id
    this.status = status
  }
}

export function configureAuthentication(options: { csrfToken?: string | null; onUnauthorized?: (() => void) | null }) {
  if ('csrfToken' in options) csrfToken = options.csrfToken ?? null
  if ('onUnauthorized' in options) unauthorizedHandler = options.onUnauthorized ?? null
}

function isApiErrorEnvelope(value: unknown): value is ApiErrorEnvelope {
  if (!value || typeof value !== 'object' || !('error' in value)) return false
  const error = (value as { error: unknown }).error
  return Boolean(
    error &&
      typeof error === 'object' &&
      'code' in error &&
      'message' in error &&
      typeof (error as ApiError).code === 'string' &&
      typeof (error as ApiError).message === 'string',
  )
}

async function parseJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type') ?? ''
  if (!contentType.includes('application/json')) return null
  return response.json()
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  timeoutMs = DEFAULT_TIMEOUT_MS,
): Promise<T> {
  const controller = new AbortController()
  const timeout = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(`${API_BASE_URL}/${path.replace(/^\//, '')}`, {
      ...options,
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        ...(options.method && !['GET', 'HEAD'].includes(options.method) && csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
        ...options.headers,
      },
      signal: controller.signal,
    })
    const payload = await parseJson(response)

    if (!response.ok) {
      if (isApiErrorEnvelope(payload)) {
        const error = new ApiClientError(payload.error, response.status)
        if (response.status === 401 && path !== 'auth/login') unauthorizedHandler?.()
        throw error
      }
      throw new ApiClientError(
        {
          code: 'HTTP_ERROR',
          message: 'A API retornou uma resposta inesperada.',
          field: null,
          details: {},
          request_id: response.headers.get('X-Request-ID'),
        },
        response.status,
      )
    }

    return payload as T
  } catch (error) {
    if (error instanceof ApiClientError) throw error
    const timedOut = error instanceof DOMException && error.name === 'AbortError'
    throw new ApiClientError(
      {
        code: timedOut ? 'REQUEST_TIMEOUT' : 'NETWORK_ERROR',
        message: timedOut
          ? 'A API demorou mais que o esperado para responder.'
          : 'Não foi possível conectar à API.',
        field: null,
        details: {},
        request_id: null,
      },
      0,
    )
  } finally {
    window.clearTimeout(timeout)
  }
}

export function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path)
}

export function apiPost<TResponse, TPayload>(
  path: string,
  payload: TPayload,
): Promise<TResponse> {
  return apiRequest<TResponse>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}
