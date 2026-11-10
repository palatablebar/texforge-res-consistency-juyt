import { getVariant } from '../api/variant'
import type { TextureVariant } from '../types/texture'

const BACKOFF = [1200, 2400, 4800, 4800, 4800]

export async function pollVariant(variantId: number, onUpdate?: (variant: TextureVariant) => void, maxTries = 20): Promise<TextureVariant | null> {
  for (let attempt = 0; attempt < maxTries; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, BACKOFF[Math.min(attempt, BACKOFF.length - 1)]))
    try {
      const variant = await getVariant(variantId)
      onUpdate?.(variant)
      if (variant.status !== 'generating') return variant
    } catch {
      // 429/5xx 时延长间隔，继续退避
    }
  }
  return null
}
