<script setup lang="ts">
defineProps<{ title: string; body: string; actionLabel?: string }>()
const emit = defineEmits<{ (event: 'action'): void }>()
</script>

<template>
  <div class="empty">
    <div class="empty-ticket">
      <div class="ticket-line" />
      <div class="ticket-line short" />
    </div>
    <div>
      <div class="empty-title">{{ title }}</div>
      <p class="empty-body">{{ body }}</p>
      <button v-if="actionLabel" class="btn btn-sm" @click="emit('action')">{{ actionLabel }}</button>
    </div>
  </div>
</template>

<style scoped>
.empty {
  display: flex;
  gap: 22px;
  align-items: flex-start;
  padding: 40px 0;
  max-width: 620px;
}
.empty-ticket {
  width: 74px;
  height: 96px;
  border: 1px solid var(--paper-edge);
  padding: 14px 10px;
  background: var(--paper-2);
  flex-shrink: 0;
}
.ticket-line {
  height: 1px;
  background: var(--ink-soft);
  margin-bottom: 8px;
  opacity: 0.5;
}
.ticket-line.short {
  width: 60%;
}
.empty-title {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 20px;
  margin-bottom: 6px;
}
.empty-body {
  color: var(--ink-soft);
  font-size: 13px;
  margin: 0 0 14px;
  line-height: 1.65;
}
</style>
