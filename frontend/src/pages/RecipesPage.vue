<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '../components/common/AppShell.vue'
import PageHeader from '../components/common/PageHeader.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import EmptyState from '../components/common/EmptyState.vue'
import PermissionNotice from '../components/common/PermissionNotice.vue'
import ConfirmDialog from '../components/common/ConfirmDialog.vue'
import ActivityTrail from '../components/common/ActivityTrail.vue'
import TextureThumb from '../components/texture/TextureThumb.vue'
import { useAuthStore } from '../stores/authStore'
import { useRecipeStore } from '../stores/recipeStore'
import { usePreviewStore } from '../stores/previewStore'
import { quotaRequest } from '../api/auth'
import { deleteRecipe, duplicateRecipe } from '../api/recipe'
import { CHANNEL_LABELS, TextureChannel } from '../constants/channel'
import { formatDate, formatResolution, formatSeam } from '../utils/formatters'
import type { Recipe } from '../types/recipe'

const router = useRouter()
const auth = useAuthStore()
const store = useRecipeStore()
const preview = usePreviewStore()

const search = ref('')
const statusFilter = ref('')
const resolutionFilter = ref<number | ''>('')
const busyId = ref<number | null>(null)
const confirmTarget = ref<Recipe | null>(null)
const message = ref('')

const filtered = computed(() => {
  let rows = store.recipes
  if (statusFilter.value) rows = rows.filter((row) => row.status === statusFilter.value)
  if (resolutionFilter.value) rows = rows.filter((row) => row.resolution === Number(resolutionFilter.value))
  if (search.value.trim()) {
    const needle = search.value.trim().toLowerCase()
    rows = rows.filter((row) => row.name.toLowerCase().includes(needle))
  }
  return rows
})

const indexGroups = computed(() => {
  const groups = new Map<string, Recipe[]>()
  for (const row of filtered.value) {
    const key = `${row.resolution}px · ${row.status}`
    if (!groups.has(key)) groups.set(key, [])
    groups.get(key)?.push(row)
  }
  return Array.from(groups.entries())
})

const fileCounts = computed(() => ({
  ready: store.recipes.filter((row) => row.status === 'ready').length,
  total: store.recipes.length,
}))

async function load() {
  await store.fetchRecipes()
  try {
    const quota = await quotaRequest()
    auth.setQuota(quota)
    preview.setQuota(quota)
  } catch {
    /* quota 失败不阻塞列表 */
  }
}

onMounted(load)

function openEditor(recipe: Recipe) {
  router.push(`/recipes/${recipe.id}/editor`)
}

function openPreview(recipe: Recipe) {
  router.push({ path: '/preview', query: { recipe: String(recipe.id) } })
}

async function copy(recipe: Recipe) {
  busyId.value = recipe.id
  try {
    const copyRow = await duplicateRecipe(recipe.id)
    await load()
    store.notify(`已复制为 ${copyRow.name}，节点坐标已随配方复制`)
    message.value = `已复制为 ${copyRow.name}`
  } catch (error: any) {
    message.value = error?.message || '复制失败'
  } finally {
    busyId.value = null
  }
}

async function confirmDelete() {
  if (!confirmTarget.value) return
  busyId.value = confirmTarget.value.id
  try {
    await deleteRecipe(confirmTarget.value.id)
    confirmTarget.value = null
    await load()
    store.notify('配方已删除，操作已记录到审计日志')
  } catch (error: any) {
    message.value = error?.message || '删除失败'
  } finally {
    busyId.value = null
  }
}

const channelOrder = Object.entries(CHANNEL_LABELS) as Array<[TextureChannel, string]>
</script>

<template>
  <AppShell section="recipes">
    <PageHeader
      title="配方样本册"
      kicker="PRJ-2611 · 栖刻视觉材质组"
      subtitle="每条配方锁定 resolution 与 seed；缩略样张、节点数、接缝评分都是后端真实生成的记录。"
      :index="`${fileCounts.ready}/${fileCounts.total} READY`"
    >
      <template #actions>
        <button class="btn btn-sm" @click="router.push('/packs')">通道打包</button>
        <button class="btn btn-sm btn-primary" @click="router.push('/recipes/' + (store.recipes[0]?.id || 1) + '/editor')">
          打开编辑器
        </button>
      </template>
    </PageHeader>

    <PermissionNotice v-if="auth.isViewer" :role="auth.workspaceRole" class="readonly-notice" />

    <div class="toolbar">
      <div class="search-field">
        <span class="mono-label">搜索 / 配方名</span>
        <input v-model="search" class="field" placeholder="输入配方名，例如 陶土外墙" />
      </div>
      <div class="filter-field">
        <label class="field-label">状态</label>
        <select v-model="statusFilter" class="field">
          <option value="">全部</option>
          <option value="ready">就绪</option>
          <option value="generating">生成中</option>
          <option value="draft">草稿</option>
          <option value="failed">失败</option>
        </select>
      </div>
      <div class="filter-field">
        <label class="field-label">分辨率</label>
        <select v-model="resolutionFilter" class="field">
          <option value="">全部</option>
          <option :value="256">256</option>
          <option :value="512">512</option>
          <option :value="1024">1024</option>
          <option :value="2048">2048</option>
        </select>
      </div>
      <div class="toolbar-note mono-label">
        共 {{ filtered.length }} 条 · 变更会写入 audit_logs
      </div>
    </div>

    <p v-if="message" class="inline-message">{{ message }}</p>

    <div v-if="filtered.length" class="catalog">
      <aside class="catalog-index">
        <div class="mono-label index-title">索引 / by status &amp; resolution</div>
        <div v-for="[key, rows] in indexGroups" :key="key" class="index-group">
          <div class="index-key">{{ key }}</div>
          <button
            v-for="row in rows"
            :key="row.id"
            class="index-item"
            @click="openEditor(row)"
          >
            <span class="index-name">{{ row.name }}</span>
            <span class="mono-label num">{{ row.variant_count }} v</span>
          </button>
        </div>
        <div class="index-foot mono-label">样本册编号 · TF-2611</div>
      </aside>

      <div class="catalog-rows">
        <article v-for="recipe in filtered" :key="recipe.id" class="sample-row">
          <div class="sample-thumb">
            <TextureThumb
              :preview-path="recipe.thumbnail_path"
              label=""
              :seam="recipe.last_seam_score"
              compact
            />
          </div>
          <div class="sample-main">
            <div class="sample-head">
              <h2 class="sample-name" @click="openEditor(recipe)">{{ recipe.name }}</h2>
              <StatusBadge :status="recipe.status" />
            </div>
            <p class="sample-desc">{{ recipe.description }}</p>
            <div class="sample-meta num">
              <span>{{ formatResolution(recipe.resolution) }}</span>
              <span>seed {{ recipe.seed }}</span>
              <span>{{ recipe.node_count }} nodes</span>
              <span>{{ recipe.variant_count }} variants</span>
              <span>接缝 {{ formatSeam(recipe.last_seam_score) }}</span>
              <span>{{ recipe.owner_name }}</span>
            </div>
          </div>
          <div class="sample-side">
            <div class="mono-label">更新 · {{ formatDate(recipe.updated_at) }}</div>
            <div class="sample-actions">
              <button class="btn btn-sm" @click="openEditor(recipe)">编辑器</button>
              <button class="btn btn-sm" @click="openPreview(recipe)">材质球</button>
              <button class="btn btn-sm" :disabled="!auth.canWrite || busyId === recipe.id" @click="copy(recipe)">复制</button>
              <button
                class="btn btn-sm"
                :disabled="!auth.canDeleteRecipe || busyId === recipe.id"
                @click="confirmTarget = recipe"
              >
                删除
              </button>
            </div>
          </div>
        </article>
        <div class="channel-note">
          <span class="mono-label">通道约定</span>
          <span v-for="[key, label] in channelOrder" :key="key" class="channel-chip num">
            {{ key }} · {{ label }}
          </span>
        </div>
      </div>
    </div>

    <EmptyState
      v-else
      title="样本册还是空的"
      body="先建一条配方：选 512 分辨率与一个 seed，再从 value 噪声起步。也可以直接从现有示例配方复制一条。"
      action-label="从示例配方复制"
      @action="router.push('/recipes')"
    />

    <ActivityTrail />

    <ConfirmDialog
      :open="Boolean(confirmTarget)"
      title="删除这条配方？"
      :body="`「${confirmTarget?.name}」将被软删，变体与打包记录保留在数据库用于审计。`"
      @cancel="confirmTarget = null"
      @confirm="confirmDelete"
    />
  </AppShell>
</template>

<style scoped>
.readonly-notice {
  margin: 12px 0 0;
}
.toolbar {
  display: flex;
  gap: 16px;
  align-items: flex-end;
  padding: 14px 0;
  border-bottom: 1px solid var(--paper-edge);
  flex-wrap: wrap;
}
.search-field {
  flex: 1;
  min-width: 220px;
}
.search-field .mono-label {
  display: block;
  margin-bottom: 4px;
}
.filter-field {
  width: 120px;
}
.toolbar-note {
  margin-left: auto;
  padding-bottom: 8px;
  font-size: 10px;
}
.inline-message {
  font-size: 12px;
  color: var(--moss);
  margin: 10px 0 0;
}
.catalog {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 28px;
  margin-top: 8px;
}
.catalog-index {
  border-right: 1px solid var(--paper-edge);
  padding-right: 18px;
  min-height: 320px;
}
.index-title {
  padding-bottom: 6px;
  border-bottom: 1px solid var(--paper-edge);
  margin-bottom: 10px;
}
.index-group {
  margin-bottom: 14px;
}
.index-key {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 15px;
  margin-bottom: 4px;
}
.index-item {
  display: flex;
  justify-content: space-between;
  gap: 6px;
  width: 100%;
  background: none;
  border: none;
  border-bottom: 1px dotted var(--paper-edge);
  padding: 4px 0;
  cursor: pointer;
  text-align: left;
  font-size: 12px;
  color: var(--ink);
}
.index-item:hover {
  color: var(--vermilion);
}
.index-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.index-foot {
  margin-top: 28px;
  font-size: 9px;
  color: var(--ink-soft);
}
.catalog-rows {
  min-width: 0;
}
.sample-row {
  display: grid;
  grid-template-columns: 92px 1fr 220px;
  gap: 18px;
  padding: 16px 0;
  border-bottom: 1px solid var(--paper-edge);
}
.sample-thumb {
  width: 92px;
}
.sample-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.sample-name {
  font-size: 25px;
  cursor: pointer;
}
.sample-name:hover {
  color: var(--vermilion);
}
.sample-desc {
  margin: 4px 0 8px;
  color: var(--ink-soft);
  font-size: 12px;
  line-height: 1.6;
}
.sample-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 11px;
  color: var(--ink-soft);
}
.sample-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  justify-content: space-between;
  gap: 10px;
}
.sample-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  justify-content: flex-end;
}
.channel-note {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 14px;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid var(--paper-edge);
}
.channel-chip {
  font-size: 10px;
  color: var(--ink-soft);
  border: 1px solid var(--paper-edge);
  padding: 1px 6px;
}
@media (max-width: 1100px) {
  .catalog {
    grid-template-columns: 1fr;
  }
  .catalog-index {
    border-right: none;
    border-bottom: 1px solid var(--paper-edge);
    padding: 0 0 14px;
  }
  .sample-row {
    grid-template-columns: 72px 1fr;
  }
  .sample-side {
    grid-column: 1 / -1;
    align-items: flex-start;
  }
}
</style>
