<script setup lang="ts">
import { computed } from 'vue'
import { seamGrade } from '../../utils/formatters'

const props = defineProps<{ score: number | null | undefined; showThreshold?: boolean }>()

const clampScore = computed(() => Math.max(0, Math.min(100, props.score ?? 0)))
const tone = computed(() => {
  const value = props.score ?? 0
  if (value >= 88) return 'var(--moss)'
  if (value >= 75) return 'var(--moss)'
  if (value >= 60) return 'var(--gamboge)'
  return 'var(--vermilion)'
})
</script>

<template>
  <div class="seam">
    <div class="seam-head">
      <span class="mono-label">接缝评分 / seam_score</span>
      <span class="seam-value num">
        {{ score ?? '—' }}
        <span class="seam-grade">{{ score === null || score === undefined ? '' : seamGrade(score) }}</span>
      </span>
    </div>
    <div class="seam-track">
      <span class="seam-fill" :style="{ width: clampScore + '%', background: tone }" />
      <span v-if="showThreshold" class="threshold" />
    </div>
    <div class="seam-scale mono-label">
      <span>0</span><span>60</span><span>75</span><span>100</span>
    </div>
  </div>
</template>

<style scoped>
.seam-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 4px;
}
.seam-value {
  font-size: 14px;
}
.seam-grade {
  font-size: 11px;
  color: var(--ink-soft);
  margin-left: 4px;
}
.seam-track {
  position: relative;
  height: 6px;
  background: var(--paper-2);
  border: 1px solid var(--paper-edge);
}
.seam-fill {
  position: absolute;
  inset: 0 auto 0 0;
  display: block;
}
.threshold {
  position: absolute;
  left: 60%;
  top: -2px;
  bottom: -2px;
  width: 1px;
  background: var(--gamboge);
}
.seam-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 3px;
  font-size: 9px;
  letter-spacing: 0.08em;
}
</style>
