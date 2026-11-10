export type AuditAction =
  | 'recipe_create'
  | 'recipe_copy'
  | 'recipe_delete'
  | 'variant_delete'
  | 'pack_download'
  | 'node_batch_update'

export interface AuditEntry {
  id: number
  actor_id: number | null
  actor_name: string | null
  action: AuditAction
  entity_type: string
  entity_id: number | null
  payload_json: Record<string, unknown>
  created_at: string
}
