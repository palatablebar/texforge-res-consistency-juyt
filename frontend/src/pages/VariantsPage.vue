<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '../components/common/AppShell.vue'
import PageHeader from '../components/common/PageHeader.vue'
import StatusBadge from '../components/common/StatusBadge.vue'
import EmptyState from '../components/common/EmptyState.vue'
import PermissionNotice from '../components/common/PermissionNotice.vue'
import TextureThumb from '../components/texture/TextureThumb.vue'
import SeamScoreBar from '../components/texture/SeamScoreBar.vue'
import { useAuthStore } from '../stores/authStore'
import { useRecipeStore } from '../stores/recipeStore'
import { listVariants, setCurrentVariant, deleteVariant } from '../api/variant'
import { fileUrl } from '../api/http'
import { CHANNEL_LABELS, TextureChannel } from '../constants/channel'
import { formatMs, formatSeam } from '../utils/formatters'
import type { TextureVariant } from '../types/texture'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const recipeStore = useRecipeStore()

const recipes = computed(() => recipeStore.recipes)
const selectedRecipeId = ref<number | null>(null)
const variants = ref<TextureVariant[]>([])
const leftId = ref<number | null>(null)
const rightId = ref<number | null>(null)
const split = ref(50)
const channel = ref<TextureChannel>(TextureChannel.BASE_COLOR)
const message = ref('')
const busy = ref(false)

const selectedRecipe = computed(() => recipes.value.find((recipe) => recipe.id === selectedRecipeId.value) || null)
const leftVariant = computed(() => variants.value.find((variant) => variant.id === leftId.value) || null)
const rightVariant = computed(() => variants.value.find((variant) => variant.id === rightId.value) || null)

function imageFor(variant: TextureVariant | null) {
  const path = variant?.file_paths_json?.[channel.value]
  return path ? fileUrl('artifacts', path) : variant?.preview_path ? fileUrl('previews', variant.preview_path) : ''
}

async function load() {
  if (!selectedRecipeId.value) return
  variants.value = await listVariants(selectedRecipeId.value)
  const ready = variants.value.filter((variant) => variant.status === 'ready')
  leftId.value = ready[0]?.id ?? null
  rightId.value = ready[1]?.id ?? ready[0]?.id ?? null
}

onMounted(async () => {
  if (!recipeStore.recipes.length) await recipeStore.fetchRecipes()
  const queryId = Number(route.query.recipe)
  selectedRecipeId.value = recipeStore.recipes.some((recipe) => recipe.id === queryId)
    ? queryId
    : recipeStore.recipes[0]?.id ?? null
  await load()
})

watch(selectedRecipeId, load)

async function setCurrent(id: number) {
  busy.value = true
  try {
    await setCurrentVariant(id)
    await load()
    message.value = '已设为当前版本，样本册角标同步更新'
  } catch (error: any) {
    message.value = error?.message || '操作失败'
  } finally {
    busy.value = false
  }
}

async function removeVariant(id: number) {
  if (!auth.canWrite) return
  busy.value = true
  try {
    await deleteVariant(id)
    await load()
    message.value = '变体已删除，共享卷文件已清理'
  } catch (error: any) {
    message.value = error?.message || '删除失败'
  } finally {
    busy.value = false
  }
}

function swap() {
  const left = leftId.value
  leftId.value = rightId.value
  rightId.value = left
}
</script>

<template>
  <AppShell section="variants">
    <PageHeader
      title="版本对比"
      kicker="对比 / Variants"
      subtitle="按 revision 左右对比两版：看接缝评分与生成耗时，确认后设为当前版本；反例版本留档不删。"
      :index="`${variants.length} REVISIONS`"
    />

    <PermissionNotice v-if="auth.isViewer" :role="auth.workspaceRole" class="mb-3" />

    <div v-if="recipes.length" class="variants-layout">
      <div class="variants-toolbar">
        <div class="control-block">
          <label class="field-label">配方</label>
          <select v-model="selectedRecipeId" class="field">
            <option v-for="recipe in recipes" :key="recipe.id" :value="recipe.id">{{ recipe.name }}</option>
          </select>
        </div>
        <div class="control-block">
          <label class="field-label">左版</label>
          <select v-model="leftId" class="field">
            <option v-for="variant in variants" :key="variant.id" :value="variant.id">
              rev {{ variant.revision }} · seam {{ variant.seam_score }}
            </option>
          </select>
        </div>
        <div class="control-block">
          <label class="field-label">右版</label>
          <select v-model="rightId" class="field">
            <option v-for="variant in variants" :key="variant.id" :value="variant.id">
              rev {{ variant.revision }} · seam {{ variant.seam_score }}
            </option>
          </select>
        </div>
        <button class="btn btn-sm" @click="swap">⇄ 交换</button>
        <div class="control-block">
          <label class="field-label">通道</label>
          <select v-model="channel" class="field">
            <option v-for="(label, key) in CHANNEL_LABELS" :key="key" :value="key">{{ label }}</option>
          </select>
        </div>
      </div>

      <p v-if="message" class="inline-message">{{ message }}</p>

      <div class="compare-grid">
        <section class="compare-panel">
          <header class="compare-head">
            <h3 class="compare-title">
              rev {{ leftVariant?.revision ?? '—' }}
              <StatusBadge v-if="leftVariant" :status="leftVariant.status" />
            </h3>
            <span class="mono-label num">seed {{ leftVariant?.seed_used ?? '—' }}</span>
          </header>
          <TextureThumb
            :preview-path="leftVariant?.preview_path"
            :channel-path="leftVariant?.file_paths_json?.[channel]"
            :label="leftVariant ? `rev ${leftVariant.revision}` : '—'"
            :seam="leftVariant?.seam_score ?? null"
          />
          <SeamScoreBar :score="leftVariant?.seam_score ?? null" show-threshold />
          <div class="variant-detail num">
            <span>generation_ms {{ formatMs(leftVariant?.generation_ms) }}</span>
            <span>checksum {{ leftVariant?.checksum?.slice(0, 12) || '—' }}</span>
            <span>当前版本 {{ leftVariant?.is_current ? '是' : '否' }}</span>
          </div>
          <div class="compare-actions">
            <button class="btn btn-sm" :disabled="!auth.canWrite || busy || leftVariant?.is_current === 1" @click="leftVariant && setCurrent(leftVariant.id)">
              设为当前版本
            </button>
            <button class="btn btn-sm" :disabled="!auth.canWrite || busy" @click="leftVariant && removeVariant(leftVariant.id)">删除</button>
          </div>
        </section>

        <section class="compare-stage">
          <div class="mono-label">擦除对比 · {{ channel }}</div>
          <div class="stage">
            <img v-if="imageFor(leftVariant)" :src="imageFor(leftVariant)" alt="左版" class="stage-img" />
            <div class="stage-right" :style="{ clipPath: `inset(0 0 0 ${split}%)` }">
              <img v-if="imageFor(rightVariant)" :src="imageFor(rightVariant)" alt="右版" class="stage-img" />
            </div>
            <div class="stage-divider" :style="{ left: split + '%' }" />
          </div>
          <input v-model.number="split" type="range" min="0" max="100" step="1" class="split-range" />
          <div class="split-legend mono-label">
            <span>左 rev {{ leftVariant?.revision ?? '—' }}</span>
            <span>右 rev {{ rightVariant?.revision ?? '—' }}</span>
          </div>
        </section>

        <section class="compare-panel">
          <header class="compare-head">
            <h3 class="compare-title">
              rev {{ rightVariant?.revision ?? '—' }}
              <StatusBadge v-if="rightVariant" :status="rightVariant.status" />
            </h3>
            <span class="mono-label num">seed {{ rightVariant?.seed_used ?? '—' }}</span>
          </header>
          <TextureThumb
            :preview-path="rightVariant?.preview_path"
            :channel-path="rightVariant?.file_paths_json?.[channel]"
            :label="rightVariant ? `rev ${rightVariant.revision}` : '—'"
            :seam="rightVariant?.seam_score ?? null"
          />
          <SeamScoreBar :score="rightVariant?.seam_score ?? null" show-threshold />
          <div class="variant-detail num">
            <span>generation_ms {{ formatMs(rightVariant?.generation_ms) }}</span>
            <span>checksum {{ rightVariant?.checksum?.slice(0, 12) || '—' }}</span>
            <span>当前版本 {{ rightVariant?.is_current ? '是' : '否' }}</span>
          </div>
          <div class="compare-actions">
            <button class="btn btn-sm" :disabled="!auth.canWrite || busy || rightVariant?.is_current === 1" @click="rightVariant && setCurrent(rightVariant.id)">
              设为当前版本
            </button>
            <button class="btn btn-sm" :disabled="!auth.canWrite || busy" @click="rightVariant && removeVariant(rightVariant.id)">删除</button>
          </div>
        </section>
      </div>

      <p class="hint">
        不同 revision 的 seed 与配方记录都能在 <code>/api/variants/{id}</code> 的 checksum 中复现；
        同一 resolution + seed + 节点图两次生成的校验和一致。
      </p>
    </div>

    <EmptyState
      v-else
      title="还没有配方可以对比"
      body="改完参数点生成，这里会按 revision 排列；左右两版可以并排或擦除对比。"
      action-label="去样本册"
      @action="router.push('/recipes')"
    />
  </AppShell>
</template>

<style scoped>
.mb-3 {
  margin: 12px 0;
}
.variants-layout {
  margin-top: 8px;
}
.variants-toolbar {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--paper-edge);
  flex-wrap: wrap;
}
.control-block {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 140px;
}
.inline-message {
  font-size: 12px;
  color: var(--moss);
  margin: 10px 0 0;
}
.compare-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr) minmax(0, 1fr);
  gap: 24px;
  margin-top: 18px;
}
.compare-panel {
  border-top: 1px solid var(--ink);
  padding-top: 10px;
}
.compare-panel :deep(.thumb-frame) {
  aspect-ratio: 4 / 3;
}
.compare-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 8px;
}
.compare-title {
  font-size: 20px;
  display: flex;
  align-items: baseline;
  gap: 8px;
}
.variant-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 11px;
  color: var(--ink-soft);
  padding: 8px 0;
}
.compare-actions {
  display: flex;
  gap: 6px;
}
.compare-stage {
  border-top: 1px solid var(--ink);
  padding-top: 10px;
}
.stage {
  position: relative;
  aspect-ratio: 1 / 1;
  margin-top: 8px;
  border: 1px solid var(--paper-edge);
  overflow: hidden;
  background: var(--paper-2);
}
.stage-img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.stage-right {
  position: absolute;
  inset: 0;
}
.stage-divider {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 1px;
  background: var(--vermilion);
}
.split-range {
  margin-top: 10px;
}
.split-legend {
  display: flex;
  justify-content: space-between;
  font-size: 9px;
  margin-top: 4px;
}
.hint {
  margin-top: 24px;
  font-size: 11px;
  color: var(--ink-soft);
  border-top: 1px solid var(--paper-edge);
  padding-top: 10px;
}
code {
  font-family: ui-monospace, monospace;
  font-size: 10px;
}
@media (max-width: 1100px) {
  .compare-grid {
    grid-template-columns: 1fr;
  }
}
</style>
