export type UserRole = 'admin' | 'member'
export type WorkspaceRole = 'owner' | 'editor' | 'viewer'

export interface User {
  id: number
  email: string
  display_name: string
  role: UserRole
  workspace_role: WorkspaceRole
  daily_generation_quota: number
  created_at?: string
}

export interface QuotaSnapshot {
  daily_quota: number
  used_today: number
  remaining: number
  used_date: string
}
