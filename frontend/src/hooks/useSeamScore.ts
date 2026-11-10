import { computed } from 'vue'

export function useSeamScore(score: () => number | null | undefined) {
  const grade = computed(() => {
    const value = score()
    if (value === null || value === undefined) return { label: '—', tone: 'muted' }
    if (value >= 88) return { label: '优', tone: 'moss' }
    if (value >= 75) return { label: '良', tone: 'moss' }
    if (value >= 60) return { label: '可接受', tone: 'gamboge' }
    return { label: '需修补', tone: 'vermilion' }
  })
  return { grade }
}
