import type { RecipeStatus } from '../types/recipe'

export const RECIPE_STATUS_LABELS: Record<RecipeStatus, string> = {
  draft: '草稿',
  generating: '生成中',
  ready: '就绪',
  failed: '失败',
}
