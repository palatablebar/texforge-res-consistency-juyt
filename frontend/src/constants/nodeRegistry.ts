import type { NodeType } from '../types/node'
import { BlendMode } from './blend'
import { NoiseType } from './noise'

export interface NodeSpec {
  type: NodeType
  label: string
  group: 'noise' | 'blend' | 'operator'
  noise?: NoiseType
  inputs: Array<'a' | 'b'>
  defaults: Record<string, unknown>
  accent: string
}

export const NODE_REGISTRY: NodeSpec[] = [
  { type: 'noise_value', label: '值噪声', group: 'noise', noise: NoiseType.VALUE, inputs: [], accent: 'var(--indigo)', defaults: { frequency: 6, seed_offset: 0, contrast: 1 } },
  { type: 'noise_perlin', label: '柏林噪声', group: 'noise', noise: NoiseType.PERLIN, inputs: [], accent: 'var(--indigo)', defaults: { frequency: 4, seed_offset: 3, contrast: 1 } },
  { type: 'noise_worley', label: '沃利颗粒', group: 'noise', noise: NoiseType.WORLEY, inputs: [], accent: 'var(--indigo)', defaults: { cells: 10, jitter: 0.9, seed_offset: 7, contrast: 1 } },
  { type: 'fbm', label: '分形叠加', group: 'noise', noise: NoiseType.FBM, inputs: ['a'], accent: 'var(--indigo)', defaults: { octaves: 5, persistence: 0.5, lacunarity: 2, frequency: 4, seed_offset: 11, grayness: 0.5 } },
  { type: 'blend', label: '混合', group: 'blend', inputs: ['a', 'b'], accent: 'var(--vermilion)', defaults: { mode: BlendMode.MULTIPLY, opacity: 0.65 } },
  { type: 'gradient', label: '渐变', group: 'operator', inputs: ['a'], accent: 'var(--gamboge)', defaults: { angle: 0, softness: 0.35, palette: 'terracotta' } },
  { type: 'warp', label: '域扭曲', group: 'operator', inputs: ['a'], accent: 'var(--moss)', defaults: { strength: 0.35, scale: 3, iterations: 2, seed_offset: 5 } },
  { type: 'height', label: '高度', group: 'operator', inputs: ['a'], accent: 'var(--ink)', defaults: { contrast: 1.25, invert: false, palette: 'terracotta', levels: 8 } },
  { type: 'normal', label: '法线', group: 'operator', inputs: ['a'], accent: 'var(--indigo)', defaults: { normal_scale: 1, flip_y: false } },
  { type: 'ao', label: '环境遮蔽', group: 'operator', inputs: ['a'], accent: 'var(--ink-soft)', defaults: { radius: 6, strength: 0.75 } },
]

export const NODE_GROUP_LABELS: Record<NodeSpec['group'], string> = {
  noise: '噪声 / NoiseType',
  blend: '混合 / BlendMode',
  operator: '算子',
}

export function specFor(type: NodeType): NodeSpec | undefined {
  return NODE_REGISTRY.find((spec) => spec.type === type)
}
