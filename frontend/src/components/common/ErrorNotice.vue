<script setup lang="ts">
defineProps<{ code?: string; message: string; detail?: string; recoverable?: boolean }>()
const emit = defineEmits<{ (event: 'retry'): void }>()
</script>

<template>
  <div class="error-notice">
    <div class="error-head">
      <span class="mono-label">生成失败</span>
      <span v-if="code" class="error-code num">{{ code }}</span>
    </div>
    <div class="error-message">{{ message }}</div>
    <div v-if="detail" class="error-detail">{{ detail }}</div>
    <button v-if="recoverable" class="btn btn-sm" @click="emit('retry')">重试本次生成</button>
  </div>
</template>

<style scoped>
.error-notice {
  border: 1px solid var(--vermilion);
  padding: 12px 14px;
  margin: 12px 0;
}
.error-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.error-code {
  color: var(--vermilion);
  font-size: 11px;
}
.error-message {
  font-size: 13px;
}
.error-detail {
  color: var(--ink-soft);
  font-size: 12px;
  margin: 4px 0 10px;
}
</style>
