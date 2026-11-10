import type { RecipeNode } from './node'

export type RecipeStatus = 'draft' | 'generating' | 'ready' | 'failed'

export interface Recipe {
  id: number
  owner_id: number
  name: string
  slug: string
  description: string
  resolution: number
  seed: number
  status: RecipeStatus
  thumbnail_path: string | null
  current_variant_id: number | null
  created_at?: string
  updated_at?: string
  node_count: number
  variant_count: number
  last_seam_score: number | null
  owner_name: string | null
}

export interface RecipeDetail extends Recipe {
  nodes: RecipeNode[]
  recent_variants: Array<{
    id: number
    revision: number
    seed_used: number
    seam_score: number
    generation_ms: number
    status: string
    preview_path: string | null
    is_current: number
  }>
}
