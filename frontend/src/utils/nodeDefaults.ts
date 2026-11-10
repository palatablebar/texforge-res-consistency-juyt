import { NODE_REGISTRY, specFor } from '../constants/nodeRegistry'
import type { NodeType } from '../types/node'

export function defaultParams(type: NodeType): Record<string, unknown> {
  const spec = specFor(type)
  return spec ? { ...spec.defaults } : {}
}

export function inputSlots(type: NodeType): Array<'a' | 'b'> {
  return specFor(type)?.inputs ?? []
}

export function paletteOptions(): string[] {
  const spec = NODE_REGISTRY.find((item) => item.type === 'height')
  return ['terracotta', 'metal', 'fabric']
}

export function defaultLabel(type: NodeType, index: number): string {
  const spec = specFor(type)
  const base = spec?.label || type
  return `${base}-${String(index).padStart(2, '0')}`
}
