<script setup lang="ts">
import { computed } from 'vue'
import { specFor } from '../../constants/nodeRegistry'
import type { RecipeNode } from '../../types/node'

const props = defineProps<{ node: RecipeNode; selected: boolean; scale?: number }>()
const emit = defineEmits<{
  (event: 'select', id: number): void
  (event: 'dragstart', payload: { id: number; event: PointerEvent }): void
}>()

const spec = computed(() => specFor(props.node.node_type))
const accent = computed(() => spec.value?.accent || 'var(--ink)')
const inputs = computed(() => spec.value?.inputs || [])
const paramSummary = computed(() => {
  const params = props.node.params_json || {}
  const entries = Object.entries(params).slice(0, 3)
  return entries.map(([key, value]) => `${key}: ${typeof value === 'number' ? Number(value.toFixed(2)) : value}`)
})

function onPointerDown(event: PointerEvent) {
  emit('select', props.node.id)
  emit('dragstart', { id: props.node.id, event })
}
</script>

<template>
  <div
    class="node-card"
    :class="{ selected, disabled: node.is_disabled }"
    :style="{
      left: node.position_x + 'px',
      top: node.position_y + 'px',
      borderTopColor: accent,
      transform: `scale(${scale ?? 1})`,
    }"
    @pointerdown.prevent="onPointerDown"
  >
    <div class="node-head">
      <span class="node-type mono-label" :style="{ color: accent }">
        {{ spec?.noise ? 'NoiseType' : spec?.group }}
      </span>
      <span class="node-index num">{{ String(node.order_index + 1).padStart(2, '0') }}</span>
    </div>
    <div class="node-title">{{ node.label }}</div>
    <div class="node-params num">
      <span v-for="line in paramSummary" :key="line">{{ line }}</span>
    </div>
    <div class="node-ports">
      <div class="port-in">
        <span v-for="slot in inputs" :key="slot" class="port" :class="`port-${slot}`">{{ slot }}</span>
      </div>
      <span class="port-out">out</span>
    </div>
    <span v-if="node.is_disabled" class="disabled-flag mono-label">已禁用</span>
  </div>
</template>

<style scoped>
.node-card {
  position: absolute;
  width: 168px;
  background: var(--paper);
  border: 1px solid var(--paper-edge);
  border-top: 2px solid var(--ink);
  padding: 8px 10px 6px;
  cursor: grab;
  user-select: none;
  z-index: 2;
  transition: border-color 140ms, box-shadow 140ms;
}
.node-card.selected {
  border-color: var(--ink);
  z-index: 3;
}
.node-card.disabled {
  opacity: 0.55;
}
.node-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}
.node-type {
  font-size: 8px;
  letter-spacing: 0.1em;
}
.node-index {
  font-size: 9px;
  color: var(--ink-soft);
}
.node-title {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 16px;
  margin: 2px 0 3px;
  line-height: 1.1;
}
.node-params {
  display: flex;
  flex-direction: column;
  gap: 0;
  font-size: 9px;
  color: var(--ink-soft);
  min-height: 26px;
}
.node-ports {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px dotted var(--paper-edge);
  font-size: 9px;
  color: var(--ink-soft);
}
.port-in {
  display: flex;
  gap: 4px;
}
.port {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border: 1px solid var(--ink-soft);
  font-size: 8px;
}
.port-out {
  border-bottom: 1px solid var(--ink-soft);
}
.disabled-flag {
  position: absolute;
  right: 6px;
  bottom: 4px;
  font-size: 8px;
  color: var(--vermilion);
}
</style>
