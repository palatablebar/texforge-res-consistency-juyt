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
      <label class="field-label">angle / 角度</label>
      <input class="field num" type="number" step="1" :value="params.angle ?? 0" @change="set('angle', Number(($event.target as HTMLInputElement).value))" />
    </div>
    <div class="field-row">
      <label class="field-label">softness / 柔软度 {{ params.softness ?? 0.35 }}</label>
      <input type="range" min="0.05" max="1" step="0.01" :value="params.softness ?? 0.35" @input="set('softness', Number(($event.target as HTMLInputElement).value))" />
    </div>
    <div class="field-row">
      <label class="field-label">palette / 色板</label>
      <select class="field" :value="params.palette ?? 'terracotta'" @change="set('palette', ($event.target as HTMLSelectElement).value)">
        <option value="terracotta">哑光陶土</option>
        <option value="metal">拉丝金属</option>
        <option value="fabric">织物</option>
      </select>
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
