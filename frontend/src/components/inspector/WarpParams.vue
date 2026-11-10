<script setup lang="ts">
import { computed } from 'vue'
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
      <label class="field-label">strength / 扭曲强度 {{ params.strength ?? 0.35 }}</label>
      <input type="range" min="0" max="1" step="0.01" :value="params.strength ?? 0.35" @input="set('strength', Number(($event.target as HTMLInputElement).value))" />
    </div>
    <div class="field-row">
      <label class="field-label">scale / 扭曲尺度</label>
      <input class="field num" type="number" step="0.5" :value="params.scale ?? 3" @change="set('scale', Number(($event.target as HTMLInputElement).value))" />
    </div>
    <div class="field-row">
      <label class="field-label">iterations / 叠加次数</label>
      <input class="field num" type="number" min="1" max="4" :value="params.iterations ?? 2" @change="set('iterations', Number(($event.target as HTMLInputElement).value))" />
    </div>
    <div class="field-row">
      <label class="field-label">seed_offset / 种子偏移</label>
      <input class="field num" type="number" :value="params.seed_offset ?? 5" @change="set('seed_offset', Number(($event.target as HTMLInputElement).value))" />
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
