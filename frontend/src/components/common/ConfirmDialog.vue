<script setup lang="ts">
defineProps<{ open: boolean; title: string; body: string }>()
const emit = defineEmits<{ (event: 'confirm'): void; (event: 'cancel'): void }>()
</script>

<template>
  <div v-if="open" class="overlay" @click.self="emit('cancel')">
    <div class="dialog">
      <div class="mono-label">请确认</div>
      <h3 class="dialog-title">{{ title }}</h3>
      <p class="dialog-body">{{ body }}</p>
      <div class="dialog-actions">
        <button class="btn btn-sm" @click="emit('cancel')">取消</button>
        <button class="btn btn-sm btn-primary" @click="emit('confirm')">确认删除</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: oklch(24% 0.02 62 / 0.28);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 40;
}
.dialog {
  width: min(440px, calc(100vw - 32px));
  background: var(--paper);
  border: 1px solid var(--ink);
  padding: 22px 24px;
}
.dialog-title {
  font-size: 24px;
  margin: 4px 0 8px;
}
.dialog-body {
  color: var(--ink-soft);
  font-size: 13px;
  margin: 0 0 20px;
}
.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}
</style>
