export interface ApiErrorEnvelope {
  code: string
  message: string
  detail: string
  request_id?: string | null
  extra?: Record<string, unknown>
}

export interface PagePayload<T> {
  items: T[]
  page: number
  page_size: number
  total: number
}
