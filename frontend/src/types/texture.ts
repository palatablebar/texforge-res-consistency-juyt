export type TextureChannel = 'base_color' | 'normal' | 'roughness' | 'metallic' | 'ao' | 'height'

export interface TextureVariant {
  id: number
  recipe_id: number
  revision: number
  seed_used: number
  file_paths_json: Partial<Record<TextureChannel, string>>
  preview_path: string | null
  generation_ms: number
  seam_score: number
  status: 'generating' | 'ready' | 'failed'
  checksum: string | null
  algo_version: number
  is_current: number
  created_at?: string
}

export interface GenerateResponse {
  variant: TextureVariant
  message: string
}
