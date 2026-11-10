<script setup lang="ts">
import { computed } from 'vue'
import type { RecipeNode } from '../../types/node'

const props = defineProps<{ node: RecipeNode }>()
const emit = defineEmits<{ (event: 'update', params: Record<string, unknown>): void }>()

const params = computed(() => props.node.params_json || {})
const isNoise = computed(() => props.node.node_type.startsWith('noise_') || props.node.node_type === 'fbm')
const isWorley = computed(() => props.node.node_type === 'noise_worley')
const isFbm = computed(() => props.node.node_type === 'fbm')

function set(key: string, value: unknown) {
  emit('update', { [key]: value })
}
</script>

<template>
  <div v-if="isNoise" class="param-block">
    <div class="field-row">
      <label class="field-label">frequency / 频率</label>
      <input
        class="field num"
        type="number"
        step="0.1"
        :value="params.frequency ?? 4"
        @change="set('frequency', Number(($event.target as HTMLInputElement).value))"
      />
    </div>
    <div v-if="isWorley" class="field-row">
      <label class="field-label">cells / 颗粒格数</label>
      <input
        class="field num"
        type="number"
        :value="params.cells ?? 10"
        @change="set('cells', Number(($event.target as HTMLInputElement).value))"
      />
    </div>
    <div v-if="isWorley" class="field-row">
      <label class="field-label">jitter / 抖动</label>
      <input
        class="field num"
        type="number"
        step="0.05"
        min="0"
        max="1"
        :value="params.jitter ?? 0.9"
        @change="set('jitter', Number(($event.target as HTMLInputElement).value))"
      />
    </div>
    <template v-if="isFbm">
      <div class="field-row">
        <label class="field-label">octaves / 叠加层数</label>
        <input
          class="field num"
          type="number"
          min="1"
          max="8"
          :value="params.octaves ?? 5"
          @change="set('octaves', Number(($event.target as HTMLInputElement).value))"
        />
      </div>
      <div class="field-row">
        <label class="field-label">persistence / 衰减</label>
        <input
          class="field num"
          type="number"
          step="0.05"
          :value="params.persistence ?? 0.5"
          @change="set('persistence', Number(($event.target as HTMLInputElement).value))"
        />
      </div>
      <div class="field-row">
        <label class="field-label">lacunarity / 频率倍增</label>
        <input
          class="field num"
          type="number"
          step="0.1"
          :value="params.lacunarity ?? 2"
          @change="set('lacunarity', Number(($event.target as HTMLInputElement).value))"
        />
      </div>
      <div class="field-row">
        <label class="field-label">grayness / 与上游混合</label>
        <input
          class="field num"
          type="number"
          step="0.05"
          :value="params.grayness ?? 0.5"
          @change="set('grayness', Number(($event.target as HTMLInputElement).value))"
        />
      </div>
    </template>
    <div class="field-row">
      <label class="field-label">contrast / 对比</label>
      <input
        class="field num"
        type="number"
        step="0.05"
        :value="params.contrast ?? 1"
        @change="set('contrast', Number(($event.target as HTMLInputElement).value))"
      />
    </div>
    <div class="field-row">
      <label class="field-label">seed_offset / 种子偏移</label>
      <input
        class="field num"
        type="number"
        :value="params.seed_offset ?? 0"
        @change="set('seed_offset', Number(($event.target as HTMLInputElement).value))"
      />
    </div>
  </div>
</template>

<style scoped>
.param-block {
  display: flex;
  flex-direction: column;
  gap: 9px;
}
</style>
