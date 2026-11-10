export interface QuotaSnapshot {
  daily_quota: number
  used_today: number
  remaining: number
  used_date: string
}

export interface RateLimitError {
  code: 'TEX-1009' | 'TEX-1010'
  retry_after?: number
  message: string
}
