import { request } from './http'
import type { CurrentUser } from '@/types/user'

export function fetchCurrentUser(): Promise<CurrentUser> {
  return request<CurrentUser>('/api/auth/me')
}

export function logout(): Promise<{ message: string }> {
  return request('/api/auth/logout', { method: 'POST' })
}
