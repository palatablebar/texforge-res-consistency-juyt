<script setup lang="ts">
import { computed } from 'vue'
import { BLEND_LABELS, BlendMode } from '../../constants/blend'
import type { RecipeNode } from '../../types/node'

const props = defineProps<{ node: RecipeNode }>()
const emit = defineEmits<{ (event: 'update', params: Record<string, unknown>): void }>()
const params = computed(() => props.node.params_json || {})

function set(key: string, value: unknown) {
  emit('update', { [key]: value })
}
</script>

<template>
  <div class="param-block">
    <div class="field-row">
      <label class="field-label">BlendMode / 混合模式</label>
      <select class="field" :value="params.mode ?? BlendMode.MULTIPLY" @change="set('mode', ($event.target as HTMLSelectElement).value)">
        <option v-for="(label, value) in BLEND_LABELS" :key="value" :value="value">{{ label }}</option>
      </select>
    </div>
    <div class="field-row">
      <label class="field-label">opacity / 强度 {{ params.opacity ?? 0.65 }}</label>
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        :value="params.opacity ?? 0.65"
        @input="set('opacity', Number(($event.target as HTMLInputElement).value))"
      />
    </div>
  </div>
</template>

<style scoped>
.param-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
</style>
