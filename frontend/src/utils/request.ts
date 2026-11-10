import type { AxiosInstance, AxiosError } from 'axios'

export interface NormalizedError {
  code: string
  message: string
  detail: string
  status?: number
  retryAfter?: number
}

export function normalizeAxiosError(error: unknown): NormalizedError {
  const axiosError = error as AxiosError<any>
  const data = axiosError?.response?.data
  if (data && typeof data === 'object' && data.code) {
    return {
      code: data.code,
      message: data.message || '请求失败',
      detail: data.detail || '',
      status: axiosError.response?.status,
      retryAfter: data.extra?.retry_after,
    }
  }
  return {
    code: 'NETWORK',
    message: axiosError?.message || '网络异常，请检查后端服务',
    detail: '',
    status: axiosError?.response?.status,
  }
}

export function installInterceptors(http: AxiosInstance): void {
  http.interceptors.request.use((config) => {
    const token = localStorage.getItem('texforge_token')
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
  })
  http.interceptors.response.use(
    (response) => response,
    (error) => Promise.reject(normalizeAxiosError(error)),
  )
}
