<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { recentAudit } from '../../api/audit'
import { AUDIT_ACTION_LABELS } from '../../constants/auditActions'
import { formatDate } from '../../utils/formatters'
import type { AuditEntry } from '../../types/audit'

const entries = ref<AuditEntry[]>([])
const open = ref(false)

onMounted(async () => {
  try {
    entries.value = await recentAudit(10)
  } catch {
    entries.value = []
  }
})
</script>

<template>
  <section class="trail rule">
    <button class="trail-toggle" @click="open = !open">
      <span class="mono-label">操作记录 / ActivityTrail</span>
      <span class="num trail-count">{{ entries.length }}</span>
      <span class="trail-arrow">{{ open ? '收起' : '展开最近 10 条' }}</span>
    </button>
    <ul v-if="open" class="trail-list">
      <li v-for="entry in entries" :key="entry.id" class="trail-item">
        <span class="num time">{{ formatDate(entry.created_at) }}</span>
        <span class="action">{{ AUDIT_ACTION_LABELS[entry.action] || entry.action }}</span>
        <span class="entity num">{{ entry.entity_type }}#{{ entry.entity_id ?? '—' }}</span>
        <span class="actor">{{ entry.actor_name || '系统' }}</span>
      </li>
      <li v-if="!entries.length" class="trail-empty">还没有审计记录，做一个写操作试试。</li>
    </ul>
  </section>
</template>

<style scoped>
.trail {
  margin-top: 28px;
}
.trail-toggle {
  width: 100%;
  display: flex;
  align-items: baseline;
  gap: 12px;
  padding: 10px 0;
  background: none;
  border: none;
  cursor: pointer;
  color: var(--ink);
  text-align: left;
}
.trail-count {
  color: var(--ink-soft);
  font-size: 12px;
}
.trail-arrow {
  margin-left: auto;
  font-size: 11px;
  color: var(--ink-soft);
}
.trail-list {
  list-style: none;
  margin: 0;
  padding: 0 0 12px;
}
.trail-item {
  display: grid;
  grid-template-columns: 160px 120px 1fr 120px;
  gap: 12px;
  padding: 5px 0;
  border-bottom: 1px dotted var(--paper-edge);
  font-size: 12px;
}
.time,
.entity {
  color: var(--ink-soft);
}
.actor {
  text-align: right;
}
.trail-empty {
  color: var(--ink-soft);
  font-size: 12px;
  padding: 8px 0;
}
</style>
