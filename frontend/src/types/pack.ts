export type PackPreset = 'orm' | 'mra' | 'custom'
export type PackSlot = 'r' | 'g' | 'b' | 'a'
export type OutputFormat = 'png' | 'tga'

export interface ChannelPack {
  id: number
  recipe_id: number
  variant_id: number | null
  name: string
  channel_mapping_json: Partial<Record<PackSlot, string>>
  output_format: OutputFormat
  preset: PackPreset
  file_path: string | null
  byte_size: number
  status: 'pending' | 'ready' | 'failed'
  created_at?: string
}
