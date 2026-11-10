<script setup lang="ts">
import { computed } from 'vue'
import type { RecipeNode } from '../../types/node'

const props = defineProps<{ nodes: RecipeNode[]; width: number; height: number; selectedId?: number | null }>()

const NODE_WIDTH = 168
const NODE_HEAD = 40

const byId = computed(() => new Map(props.nodes.map((node) => [node.id, node])))

const edges = computed(() => {
  const result: Array<{ key: string; d: string; active: boolean; source: number; target: number }> = []
  props.nodes.forEach((target) => {
    ;(target.input_refs_json || []).forEach((ref) => {
      const source = byId.value.get(ref.from_node_id)
      if (!source) return
      const sx = source.position_x + NODE_WIDTH
      const sy = source.position_y + NODE_HEAD + 18
      const tx = target.position_x
      const ty = target.position_y + NODE_HEAD + 18
      const dx = Math.max(40, Math.abs(tx - sx) * 0.45)
      const d = `M ${sx} ${sy} C ${sx + dx} ${sy}, ${tx - dx} ${ty}, ${tx} ${ty}`
      result.push({
        key: `${source.id}-${target.id}-${ref.slot}`,
        d,
        active: props.selectedId === source.id || props.selectedId === target.id,
        source: source.id,
        target: target.id,
      })
    })
  })
  return result
})
</script>

<template>
  <svg class="edge-layer" :width="width" :height="height">
    <path v-for="edge in edges" :key="edge.key" :d="edge.d" class="edge" :class="{ active: edge.active }" />
    <circle v-for="edge in edges" :key="edge.key + '-dot'" :cx="0" :cy="0" r="0" />
  </svg>
</template>

<style scoped>
.edge-layer {
  position: absolute;
  left: 0;
  top: 0;
  pointer-events: none;
  z-index: 1;
}
.edge {
  fill: none;
  stroke: var(--paper-edge);
  stroke-width: 1.4;
}
.edge.active {
  stroke: var(--vermilion);
  stroke-width: 1.8;
}
</style>
