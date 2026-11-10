import type { TextureChannel } from '../constants/channel'
import { CHANNEL_ORDER } from '../constants/channel'
import type { TextureVariant } from '../types/texture'

export interface PrecheckResult {
  ok: boolean
  duplicate: string[]
  missing: string[]
  message: string
}

export function precheckMapping(
  mapping: Partial<Record<'r' | 'g' | 'b' | 'a', TextureChannel | ''>>,
  variant: TextureVariant | null,
): PrecheckResult {
  const values = Object.values(mapping).filter((value): value is TextureChannel => Boolean(value))
  const duplicate = Array.from(new Set(values.filter((value, index) => values.indexOf(value) !== index)))
  const available = new Set(Object.keys(variant?.file_paths_json || {}))
  const missing = Array.from(new Set(values.filter((value) => !available.has(value))))
  return {
    ok: duplicate.length === 0 && missing.length === 0 && values.length > 0,
    duplicate,
    missing,
    message:
      duplicate.length > 0
        ? `同一通道被重复占用：${duplicate.join(' / ')}`
        : missing.length > 0
          ? `所选版本缺少通道：${missing.join(' / ')}`
          : '映射可用，可以打包',
  }
}

export function channelKeys(): TextureChannel[] {
  return [...CHANNEL_ORDER]
}
