export type NodeType =
  | 'noise_value'
  | 'noise_perlin'
  | 'noise_worley'
  | 'fbm'
  | 'gradient'
  | 'blend'
  | 'warp'
  | 'height'
  | 'normal'
  | 'ao'

export interface InputRef {
  slot: 'a' | 'b'
  from_node_id: number
}

export interface RecipeNode {
  id: number
  recipe_id: number
  node_type: NodeType
  label: string
  position_x: number
  position_y: number
  params_json: Record<string, unknown>
  input_refs_json: InputRef[]
  order_index: number
  is_disabled: boolean
}

export interface NodeBatchItem {
  id: number
  position_x?: number
  position_y?: number
  params_json?: Record<string, unknown>
  input_refs_json?: InputRef[]
  is_disabled?: boolean
}
