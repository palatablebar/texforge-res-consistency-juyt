<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import EdgeLayer from './EdgeLayer.vue'
import NodeCard from './NodeCard.vue'
import type { RecipeNode } from '../../types/node'

const props = defineProps<{ nodes: RecipeNode[]; selectedId: number | null; zoom: number }>()
const emit = defineEmits<{
  (event: 'select', id: number): void
  (event: 'move', payload: { id: number; x: number; y: number }): void
  (event: 'moved', payload: { id: number; x: number; y: number }): void
  (event: 'zoom', value: number): void
}>()

const canvas = ref<HTMLElement | null>(null)
const dragging = ref<{ id: number; offsetX: number; offsetY: number } | null>(null)

const bounds = computed(() => {
  const maxX = Math.max(0, ...props.nodes.map((node) => node.position_x + 220))
  const maxY = Math.max(0, ...props.nodes.map((node) => node.position_y + 160))
  return { width: Math.max(900, maxX + 60), height: Math.max(520, maxY + 60) }
})

function onDragStart({ id, event }: { id: number; event: PointerEvent }) {
  const node = props.nodes.find((item) => item.id === id)
  if (!node || !canvas.value) return
  const rect = canvas.value.getBoundingClientRect()
  dragging.value = {
    id,
    offsetX: (event.clientX - rect.left) / props.zoom - node.position_x,
    offsetY: (event.clientY - rect.top) / props.zoom - node.position_y,
  }
  window.addEventListener('pointermove', onPointerMove)
  window.addEventListener('pointerup', onPointerUp, { once: true })
}

function onPointerMove(event: PointerEvent) {
  if (!dragging.value || !canvas.value) return
  const rect = canvas.value.getBoundingClientRect()
  const x = Math.max(8, Math.min(bounds.value.width - 180, (event.clientX - rect.left) / props.zoom - dragging.value.offsetX))
  const y = Math.max(8, Math.min(bounds.value.height - 110, (event.clientY - rect.top) / props.zoom - dragging.value.offsetY))
  emit('move', { id: dragging.value.id, x: Math.round(x), y: Math.round(y) })
}

function onPointerUp() {
  window.removeEventListener('pointermove', onPointerMove)
  const node = props.nodes.find((item) => item.id === dragging.value?.id)
  if (node) emit('moved', { id: node.id, x: node.position_x, y: node.position_y })
  dragging.value = null
}

function fit() {
  if (!canvas.value) return
  const width = bounds.value.width
  const height = bounds.value.height
  const scale = Math.min(1.4, Math.max(0.45, Math.min(canvas.value.clientWidth / width, canvas.value.clientHeight / height)))
  emit('zoom', Number(scale.toFixed(2)))
}

let autoFitted = false
watch(
  () => props.nodes.length,
  async (length) => {
    if (!length || autoFitted) return
    await nextTick()
    window.setTimeout(() => {
      if (!autoFitted) {
        fit()
        autoFitted = true
      }
    }, 120)
  },
)

onBeforeUnmount(() => {
  window.removeEventListener('pointermove', onPointerMove)
})
</script>

<template>
  <section class="canvas-shell">
    <div class="canvas-toolbar">
      <span class="mono-label">节点画布 / DAG</span>
      <div class="toolbar-actions">
        <button class="btn btn-sm btn-ghost" @click="emit('zoom', Math.max(0.5, zoom - 0.1))">－</button>
        <span class="num zoom-value">{{ Math.round(zoom * 100) }}%</span>
        <button class="btn btn-sm btn-ghost" @click="emit('zoom', Math.min(1.6, zoom + 0.1))">＋</button>
        <button class="btn btn-sm" @click="fit">适应画布</button>
      </div>
    </div>
    <div ref="canvas" class="canvas-viewport paper-grid">
      <div
        class="canvas-plane"
        :style="{ width: bounds.width + 'px', height: bounds.height + 'px', transform: `scale(${zoom})` }"
      >
        <EdgeLayer :nodes="nodes" :width="bounds.width" :height="bounds.height" :selected-id="selectedId" />
        <NodeCard
          v-for="node in nodes"
          :key="node.id"
          :node="node"
          :selected="selectedId === node.id"
          :scale="1"
          @select="emit('select', $event)"
          @dragstart="onDragStart"
        />
      </div>
    </div>
  </section>
</template>

<style scoped>
.canvas-shell {
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--paper);
}
.canvas-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--paper-edge);
}
.toolbar-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}
.zoom-value {
  font-size: 11px;
  color: var(--ink-soft);
  min-width: 38px;
  text-align: center;
}
.canvas-viewport {
  flex: 1;
  overflow: auto;
  position: relative;
  min-height: 420px;
}
.canvas-plane {
  position: relative;
  transform-origin: 0 0;
}
</style>
