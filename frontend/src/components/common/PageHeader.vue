<script setup lang="ts">
defineProps<{ title: string; kicker?: string; subtitle?: string; index?: string }>()
</script>

<template>
  <header class="page-header rule">
    <div class="flex items-end justify-between gap-6 flex-wrap">
      <div>
        <div v-if="kicker" class="mono-label mb-1">{{ kicker }}</div>
        <h1 class="page-title">{{ title }}</h1>
        <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
      </div>
      <div class="flex items-center gap-3">
        <slot name="actions" />
      </div>
    </div>
    <div v-if="index" class="index-stamp num">{{ index }}</div>
  </header>
</template>

<style scoped>
.page-header {
  position: relative;
  padding: 22px 0 18px;
}
.page-title {
  font-size: clamp(20px, 2.4vw, 34px);
}
.subtitle {
  margin: 6px 0 0;
  color: var(--ink-soft);
  font-size: 13px;
  max-width: 720px;
}
.index-stamp {
  position: absolute;
  right: 0;
  top: 26px;
  font-size: 11px;
  letter-spacing: 0.16em;
  color: var(--ink-soft);
}
</style>
