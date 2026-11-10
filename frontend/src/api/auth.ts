import http from './http'
import type { User, QuotaSnapshot } from '../types/user'

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
  quota: QuotaSnapshot
}

export async function loginRequest(email: string, password: string): Promise<LoginResponse> {
  const { data } = await http.post<LoginResponse>('/auth/login', { email, password })
  return data
}

export async function meRequest(): Promise<User> {
  const { data } = await http.get<User>('/auth/me')
  return data
}

export async function quotaRequest(): Promise<QuotaSnapshot> {
  const { data } = await http.get<QuotaSnapshot>('/quota/me')
  return data
}
