<script setup lang="ts">
import { computed } from 'vue'
import { usePreviewStore } from '../../stores/previewStore'

const store = usePreviewStore()
const quota = computed(() => store.quota)
const percent = computed(() => {
  if (!quota.value || !quota.value.daily_quota) return 0
  return Math.min(100, Math.round((quota.value.used_today / quota.value.daily_quota) * 100))
})
</script>

<template>
  <div class="quota">
    <div class="mono-label">今日配额</div>
    <div class="quota-line num">
      <span>{{ quota?.used_today ?? 0 }}</span>
      <span class="slash">/</span>
      <span>{{ quota?.daily_quota ?? '—' }}</span>
    </div>
    <div class="quota-track">
      <span class="quota-fill" :style="{ width: percent + '%' }" />
    </div>
  </div>
</template>

<style scoped>
.quota {
  min-width: 92px;
}
.quota-line {
  font-size: 12px;
  color: var(--ink-soft);
}
.slash {
  margin: 0 2px;
}
.quota-track {
  margin-top: 3px;
  height: 2px;
  background: var(--paper-edge);
}
.quota-fill {
  display: block;
  height: 100%;
  background: var(--vermilion);
}
</style>
