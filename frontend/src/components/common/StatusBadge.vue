<script setup lang="ts">
import { computed } from 'vue'
import { RECIPE_STATUS_LABELS } from '../../constants/recipeStatus'
import type { RecipeStatus } from '../../types/recipe'

const props = defineProps<{ status: RecipeStatus | string; label?: string }>()

const tone = computed(() => {
  switch (props.status) {
    case 'ready':
      return { color: 'var(--moss)', dash: false }
    case 'generating':
      return { color: 'var(--gamboge)', dash: true }
    case 'failed':
      return { color: 'var(--vermilion)', dash: false }
    default:
      return { color: 'var(--ink-soft)', dash: true }
  }
})

const text = computed(() => props.label || RECIPE_STATUS_LABELS[props.status as RecipeStatus] || props.status)
</script>

<template>
  <span class="status-badge num" :style="{ color: tone.color, borderColor: tone.color + '55' }">
    <span class="dot" :style="{ backgroundColor: tone.color, borderRadius: tone.dash ? '0' : '50%' }" />
    {{ text }}
  </span>
</template>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 1px 7px;
  border: 1px solid;
  font-size: 11px;
  letter-spacing: 0.04em;
  white-space: nowrap;
}
.dot {
  width: 5px;
  height: 5px;
  display: inline-block;
}
</style>
