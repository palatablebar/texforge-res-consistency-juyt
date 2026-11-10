<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import NoiseParams from './NoiseParams.vue'
import BlendParams from './BlendParams.vue'
import WarpParams from './WarpParams.vue'
import GradientParams from './GradientParams.vue'
import SeamScoreBar from '../texture/SeamScoreBar.vue'
import ChannelStrip from '../texture/ChannelStrip.vue'
import { CHANNEL_LABELS, TextureChannel } from '../../constants/channel'
import type { RecipeNode } from '../../types/node'
import type { TextureVariant } from '../../types/texture'

const props = defineProps<{
  node: RecipeNode | null
  variant: TextureVariant | null
  history: string[]
  disabled?: boolean
}>()
const emit = defineEmits<{
  (event: 'update', payload: { nodeId: number; params: Record<string, unknown> }): void
  (event: 'generate'): void
}>()

const tab = ref<'params' | 'channels' | 'history'>('params')
const debounceTimer = ref<number | null>(null)
const pending = ref<Record<string, unknown>>({})

const isNoise = computed(() => {
  const type = props.node?.node_type || ''
  return type.startsWith('noise_') || type === 'fbm'
})

function applyParams(params: Record<string, unknown>) {
  if (!props.node) return
  pending.value = { ...props.node.params_json, ...params }
  if (debounceTimer.value) window.clearTimeout(debounceTimer.value)
  debounceTimer.value = window.setTimeout(() => {
    emit('update', { nodeId: props.node!.id, params: pending.value })
  }, 400)
}

watch(() => props.node?.id, () => {
  if (tab.value === 'params') {
    if (debounceTimer.value) window.clearTimeout(debounceTimer.value)
  }
})

const tabList = [
  { key: 'params', label: '参数' },
  { key: 'channels', label: '通道' },
  { key: 'history', label: '历史' },
] as const
</script>

<template>
  <aside class="inspector editor-inspector">
    <div class="tabs">
      <button
        v-for="item in tabList"
        :key="item.key"
        class="tab"
        :class="{ active: tab === item.key }"
        @click="tab = item.key"
      >
        {{ item.label }}
      </button>
    </div>

    <div v-if="tab === 'params'" class="inspector-body">
      <template v-if="node">
        <div class="node-meta">
          <div class="mono-label">节点 / {{ node.node_type }}</div>
          <h3 class="inspector-title">{{ node.label }}</h3>
          <div class="mono-label num">#{{ node.id }} · order {{ node.order_index }}</div>
        </div>
        <NoiseParams v-if="isNoise" :node="node" @update="applyParams" />
        <BlendParams v-else-if="node.node_type === 'blend'" :node="node" @update="applyParams" />
        <WarpParams v-else-if="node.node_type === 'warp'" :node="node" @update="applyParams" />
        <GradientParams v-else-if="node.node_type === 'gradient'" :node="node" @update="applyParams" />
        <div v-else class="param-block">
          <div v-for="(value, key) in node.params_json" :key="key" class="field-row">
            <label class="field-label">{{ key }}</label>
            <input
              class="field num"
              :type="typeof value === 'number' ? 'number' : 'text'"
              :value="value as string | number"
              @change="applyParams({ [key]: typeof value === 'number' ? Number(($event.target as HTMLInputElement).value) : ($event.target as HTMLInputElement).value })"
            />
          </div>
        </div>
        <div class="inspector-actions">
          <button class="btn btn-sm" :disabled="disabled" @click="emit('generate')">提交生成</button>
          <span class="mono-label">参数变更 400ms 防抖保存</span>
        </div>
      </template>
      <p v-else class="hint">从画布或节点库选择一个节点。</p>
    </div>

    <div v-else-if="tab === 'channels'" class="inspector-body">
      <SeamScoreBar :score="variant?.seam_score ?? null" show-threshold />
      <ChannelStrip :variant="variant" class="mt-3" />
      <div class="channel-legend">
        <div v-for="(label, key) in CHANNEL_LABELS" :key="key" class="legend-row">
          <span class="mono-label">{{ key }}</span>
          <span>{{ label }}</span>
        </div>
      </div>
      <p class="hint">通道缩略图直接来自后端生成的文件，前端不做像素合成。</p>
    </div>

    <div v-else class="inspector-body">
      <div class="mono-label mb-2">最近操作 / 撤销栈最多 20 步</div>
      <ul class="history-list">
        <li v-for="(item, index) in history" :key="index" class="num">{{ item }}</li>
        <li v-if="!history.length" class="hint">暂无操作记录</li>
      </ul>
      <p class="hint">拖动节点松手后会批量 PATCH 坐标；改参数会在 400ms 后提交。</p>
    </div>
  </aside>
</template>

<style scoped>
.inspector {
  width: 320px;
  flex-shrink: 0;
  border-left: 1px solid var(--paper-edge);
  background: var(--paper);
  overflow-y: auto;
}
.tabs {
  display: flex;
  gap: 2px;
  border-bottom: 1px solid var(--paper-edge);
  padding: 0 10px;
}
.inspector-body {
  padding: 14px 16px 24px;
}
.node-meta {
  border-bottom: 1px dotted var(--paper-edge);
  padding-bottom: 8px;
  margin-bottom: 12px;
}
.inspector-title {
  font-size: 22px;
  margin: 2px 0;
}
.field-row {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.param-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.inspector-actions {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--paper-edge);
}
.channel-legend {
  margin-top: 12px;
}
.legend-row {
  display: flex;
  justify-content: space-between;
  padding: 3px 0;
  border-bottom: 1px dotted var(--paper-edge);
  font-size: 12px;
}
.history-list {
  list-style: none;
  padding: 0;
  margin: 0;
  font-size: 12px;
  color: var(--ink-soft);
}
.history-list li {
  padding: 3px 0;
  border-bottom: 1px dotted var(--paper-edge);
}
.hint {
  color: var(--ink-soft);
  font-size: 11px;
  line-height: 1.6;
  margin-top: 14px;
}
.mt-3 {
  margin-top: 12px;
}
</style>
