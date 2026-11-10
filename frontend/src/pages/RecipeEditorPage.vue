<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import AppShell from '../components/common/AppShell.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import QuotaMeter from '../components/common/QuotaMeter.vue'
import PermissionNotice from '../components/common/PermissionNotice.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import NodePalette from '../components/graph/NodePalette.vue'
import NodeCanvas from '../components/graph/NodeCanvas.vue'
import ParamInspector from '../components/inspector/ParamInspector.vue'
import { useAuthStore } from '../stores/authStore'
import { useNodeGraphStore } from '../stores/nodeGraphStore'
import { useRecipeStore } from '../stores/recipeStore'
import { usePreviewStore } from '../stores/previewStore'
import { useNodeGraph } from '../hooks/useNodeGraph'
import { pollVariant } from '../hooks/useGenerationPolling'
import { batchUpdateNodes, generateVariant, patchRecipe } from '../api/recipe'
import { createNode } from '../api/node'
import { quotaRequest } from '../api/auth'
import { defaultLabel, defaultParams } from '../utils/nodeDefaults'
import { formatMs, formatResolution, formatSeam } from '../utils/formatters'
import type { NodeType } from '../types/node'
import type { TextureVariant } from '../types/texture'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const recipeStore = useRecipeStore()
const graphStore = useNodeGraphStore()
const preview = usePreviewStore()
const { nodes, selectedNodeId, zoom } = storeToRefs(graphStore)

const recipeId = computed(() => Number(route.params.id))
const recipe = computed(() => recipeStore.current)
const variants = ref<TextureVariant[]>([])
const seedInput = ref<number>(0)
const resolutionInput = ref<number>(512)
const generating = ref(false)
const error = ref<{ code?: string; message: string; detail?: string } | null>(null)
const saveNote = ref('')
const lastVariant = computed(() => variants.value[0] || null)

const graph = useNodeGraph(
  () => nodes.value,
  () => recipeId.value,
  async (items) => {
    await batchUpdateNodes(recipeId.value, items)
  },
)

const selectedNode = computed(() => nodes.value.find((node) => node.id === selectedNodeId.value) || null)

async function load() {
  const detail = await recipeStore.fetchRecipe(recipeId.value)
  if (!detail) return
  graphStore.setNodes(detail.nodes)
  graphStore.select(detail.nodes[0]?.id ?? null)
  seedInput.value = detail.seed
  resolutionInput.value = detail.resolution
  variants.value = (detail.recent_variants || []).map((variant) => ({
    id: variant.id,
    recipe_id: detail.id,
    revision: variant.revision,
    seed_used: variant.seed_used,
    file_paths_json: {},
    preview_path: variant.preview_path,
    generation_ms: variant.generation_ms,
    seam_score: variant.seam_score,
    status: variant.status as TextureVariant['status'],
    checksum: null,
    algo_version: variant.algo_version || 1,
    is_current: variant.is_current,
  })) as TextureVariant[]
  try {
    const quota = await quotaRequest()
    auth.setQuota(quota)
    preview.setQuota(quota)
  } catch {
    /* ignore */
  }
}

onMounted(load)

async function onMove(payload: { id: number; x: number; y: number }) {
  graphStore.moveNode(payload.id, payload.x, payload.y)
}

async function onMoved(payload: { id: number; x: number; y: number }) {
  await graphStore.persistPositions(recipeId.value, [{ id: payload.id, position_x: payload.x, position_y: payload.y }])
  saveNote.value = `坐标已保存 · node ${payload.id}`
}

async function onSelect(id: number) {
  graphStore.select(id)
}

async function onParamUpdate(payload: { nodeId: number; params: Record<string, unknown> }) {
  await graphStore.persistPositions(recipeId.value, [{ id: payload.nodeId, params_json: payload.params }])
  const node = nodes.value.find((item) => item.id === payload.nodeId)
  if (node) node.params_json = { ...node.params_json, ...payload.params }
  saveNote.value = '参数已保存，提交生成以产出新变体'
}

async function addNode(type: NodeType) {
  if (!auth.canWrite) return
  const offset = nodes.value.length * 30
  await createNode(recipeId.value, {
    node_type: type,
    label: defaultLabel(type, nodes.value.length + 1),
    position_x: 120 + offset,
    position_y: 360 + (offset % 120),
    params_json: defaultParams(type),
    input_refs_json: [],
  })
  await load()
  saveNote.value = `已添加节点 ${type}`
}

async function generate() {
  if (!auth.canWrite) return
  generating.value = true
  error.value = null
  try {
    if (seedInput.value !== recipe.value?.seed || resolutionInput.value !== recipe.value?.resolution) {
      await patchRecipe(recipeId.value, { seed: seedInput.value, resolution: resolutionInput.value })
    }
    const response = await generateVariant(recipeId.value, { seed: seedInput.value, resolution: resolutionInput.value })
    const finished = await pollVariant(response.variant.id)
    if (finished?.status === 'failed') {
      error.value = { code: 'TEX-1007', message: '生成失败，已保留上一个成功变体', detail: '请检查节点参数后重试' }
    }
    await load()
    try {
      const quota = await quotaRequest()
      auth.setQuota(quota)
      preview.setQuota(quota)
    } catch {
      /* ignore */
    }
  } catch (err: any) {
    error.value = { code: err?.code, message: err?.message || '生成失败', detail: err?.detail }
  } finally {
    generating.value = false
  }
}
</script>

<template>
  <AppShell section="recipes">
    <div class="editor-head">
      <div class="editor-title-row">
        <button class="btn btn-sm btn-ghost" @click="router.push('/recipes')">← 样本册</button>
        <div>
          <div class="mono-label">/recipes/{{ recipeId }}/editor · 节点编辑器</div>
          <h1 class="editor-title">{{ recipe?.name || '载入中…' }}</h1>
        </div>
        <StatusBadge :status="recipe?.status || 'draft'" />
        <div class="mono-label num head-meta">
          {{ recipe ? formatResolution(recipe.resolution) : '—' }} · {{ nodes.length }} nodes ·
          <template v-if="lastVariant">接缝 {{ formatSeam(lastVariant.seam_score) }} · {{ formatMs(lastVariant.generation_ms) }}</template>
        </div>
      </div>
      <div class="editor-controls">
        <div class="control">
          <label class="field-label">分辨率</label>
          <select v-model="resolutionInput" class="field" :disabled="!auth.canWrite">
            <option :value="256">256</option>
            <option :value="512">512</option>
            <option :value="1024">1024</option>
            <option :value="2048">2048</option>
          </select>
        </div>
        <div class="control">
          <label class="field-label">seed</label>
          <input v-model.number="seedInput" class="field num" type="number" min="0" max="2147483647" :disabled="!auth.canWrite" />
        </div>
        <div class="control-grow">
          <QuotaMeter />
        </div>
        <button class="btn btn-primary" :disabled="!auth.canWrite || generating" @click="generate">
          {{ generating ? '生成中…' : '提交生成' }}
        </button>
      </div>
    </div>

    <PermissionNotice v-if="auth.isViewer" :role="auth.workspaceRole" />
    <ErrorNotice
      v-if="error"
      :code="error.code"
      :message="error.message"
      :detail="error.detail"
      recoverable
      @retry="generate"
    />
    <p v-if="saveNote" class="save-note mono-label">{{ saveNote }}</p>

    <div class="editor-grid">
      <NodePalette @pick="addNode" />
      <NodeCanvas
        :nodes="nodes"
        :selected-id="selectedNodeId"
        :zoom="zoom"
        @select="onSelect"
        @move="onMove"
        @moved="onMoved"
        @zoom="zoom = $event"
      />
      <ParamInspector
        :node="selectedNode"
        :variant="lastVariant"
        :history="graphStore.history"
        :disabled="!auth.canWrite"
        @update="onParamUpdate"
        @generate="generate"
      />
    </div>
  </AppShell>
</template>

<style scoped>
.editor-head {
  padding: 12px 0 10px;
  border-bottom: 1px solid var(--ink);
}
.editor-title-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}
.editor-title {
  font-size: clamp(20px, 2.2vw, 30px);
  line-height: 1.1;
}
.head-meta {
  margin-left: auto;
  font-size: 10px;
}
.editor-controls {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  margin-top: 10px;
  flex-wrap: wrap;
}
.control {
  width: 110px;
}
.control-grow {
  margin-left: auto;
}
.editor-grid {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr) 320px;
  height: calc(100vh - 210px);
  min-height: 520px;
  margin-top: 12px;
  border: 1px solid var(--paper-edge);
}
.save-note {
  margin: 8px 0 0;
  font-size: 10px;
  color: var(--moss);
}
</style>
