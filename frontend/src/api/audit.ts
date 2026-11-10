import http from './http'
import type { AuditEntry } from '../types/audit'

export async function recentAudit(limit = 10): Promise<AuditEntry[]> {
  const { data } = await http.get<AuditEntry[]>('/audit/recent', { params: { limit } })
  return data
}
