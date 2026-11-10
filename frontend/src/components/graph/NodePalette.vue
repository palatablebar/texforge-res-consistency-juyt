<script setup lang="ts">
import { computed, ref } from 'vue'
import { NODE_GROUP_LABELS, NODE_REGISTRY } from '../../constants/nodeRegistry'
import type { NodeType } from '../../types/node'

const emit = defineEmits<{ (event: 'pick', type: NodeType): void }>()
const collapsed = ref(false)

const groups = computed(() =>
  (['noise', 'blend', 'operator'] as const).map((group) => ({
    group,
    label: NODE_GROUP_LABELS[group],
    nodes: NODE_REGISTRY.filter((spec) => spec.group === group),
  })),
)
</script>

<template>
  <aside class="palette" :class="{ collapsed }">
    <button class="palette-toggle mono-label" @click="collapsed = !collapsed">
      {{ collapsed ? '＋' : '收起节点库' }}
    </button>
    <template v-if="!collapsed">
      <div v-for="group in groups" :key="group.group" class="palette-group">
        <div class="mono-label group-label">{{ group.label }}</div>
        <button
          v-for="spec in group.nodes"
          :key="spec.type"
          class="palette-node"
          :style="{ borderLeftColor: spec.accent }"
          @click="emit('pick', spec.type)"
        >
          <span class="palette-node-label">{{ spec.label }}</span>
          <span class="palette-node-slots mono-label">{{ spec.inputs.length ? spec.inputs.join('+') + ' → out' : 'out' }}</span>
        </button>
      </div>
      <p class="palette-hint">拖入或点击添加节点；连线在节点卡端口上操作。</p>
    </template>
  </aside>
</template>

<style scoped>
.palette {
  width: 240px;
  flex-shrink: 0;
  border-right: 1px solid var(--paper-edge);
  padding: 10px 12px 16px;
  overflow-y: auto;
  background: var(--paper);
}
.palette.collapsed {
  width: 56px;
  padding: 10px 6px;
}
.palette-toggle {
  width: 100%;
  background: none;
  border: none;
  padding: 4px 0 8px;
  text-align: left;
  cursor: pointer;
  color: var(--ink-soft);
}
.palette-group {
  margin-bottom: 14px;
}
.group-label {
  margin-bottom: 5px;
  padding-bottom: 3px;
  border-bottom: 1px solid var(--paper-edge);
}
.palette-node {
  display: flex;
  flex-direction: column;
  width: 100%;
  text-align: left;
  background: var(--paper);
  border: 1px solid var(--paper-edge);
  border-left: 2px solid var(--ink-soft);
  padding: 5px 8px;
  margin-bottom: 4px;
  cursor: pointer;
}
.palette-node:hover {
  background: var(--paper-2);
}
.palette-node-label {
  font-size: 12px;
}
.palette-node-slots {
  font-size: 8px;
  letter-spacing: 0.06em;
}
.palette-hint {
  margin: 12px 0 0;
  font-size: 11px;
  line-height: 1.6;
  color: var(--ink-soft);
}
</style>
