import { apiGet, apiPost } from './client'
import type { AuthSessionResponse } from '../types/api'

export function getCurrentSession() { return apiGet<AuthSessionResponse>('auth/me') }
export function login(email: string, password: string) { return apiPost<AuthSessionResponse, { email: string; password: string }>('auth/login', { email, password }) }
export function logout() { return apiPost<{ authenticated: boolean }, Record<string, never>>('auth/logout', {}) }
