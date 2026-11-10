<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '../components/common/AppShell.vue'
import PageHeader from '../components/common/PageHeader.vue'
import EmptyState from '../components/common/EmptyState.vue'
import PermissionNotice from '../components/common/PermissionNotice.vue'
import TextureThumb from '../components/texture/TextureThumb.vue'
import ChannelStrip from '../components/texture/ChannelStrip.vue'
import { useAuthStore } from '../stores/authStore'
import { useRecipeStore } from '../stores/recipeStore'
import { usePackStore } from '../stores/packStore'
import { listVariants } from '../api/variant'
import { fileUrl } from '../api/http'
import { formatBytes } from '../utils/formatBytes'
import { formatDate, formatResolution } from '../utils/formatters'
import { CHANNEL_LABELS, PACK_PRESETS, TextureChannel } from '../constants/channel'
import type { TextureVariant } from '../types/texture'
import type { PackSlot } from '../types/pack'

const router = useRouter()
const auth = useAuthStore()
const recipeStore = useRecipeStore()
const packStore = usePackStore()

const recipes = computed(() => recipeStore.recipes)
const selectedRecipeId = ref<number | null>(null)
const variants = ref<TextureVariant[]>([])
const selectedVariantId = ref<number | null>(null)
const message = ref('')
const messageTone = ref<'ok' | 'error'>('ok')
const savingPreset = ref(false)
const presetName = ref('PRJ-2611-ORM')

const selectedRecipe = computed(() => recipes.value.find((recipe) => recipe.id === selectedRecipeId.value) || null)
const selectedVariant = computed(() => variants.value.find((variant) => variant.id === selectedVariantId.value) || null)
const slots: PackSlot[] = ['r', 'g', 'b', 'a']
const channelOptions = Object.entries(CHANNEL_LABELS) as Array<[TextureChannel, string]>

function mappingSummary(): string {
  return slots
    .map((slot) => `${slot.toUpperCase()}=${packStore.mapping[slot] || '—'}`)
    .join('  ')
}

async function loadVariants() {
  if (!selectedRecipeId.value) return
  variants.value = await listVariants(selectedRecipeId.value)
  selectedVariantId.value = selectedVariant.value?.id && variants.value.some((v) => v.id === selectedVariant.value?.id)
    ? selectedVariant.value.id
    : variants.value[0]?.id ?? null
  await packStore.fetchPacks(selectedRecipeId.value)
}

onMounted(async () => {
  if (!recipeStore.recipes.length) await recipeStore.fetchRecipes()
  // 优先选中已有打包记录的配方（演示剧本里是 PRJ-2611-陶土外墙）
  let preferred: number | null = null
  try {
    const allPacks = await listPacks()
    preferred = allPacks[0]?.recipe_id ?? null
  } catch {
    preferred = null
  }
  selectedRecipeId.value = preferred ?? recipeStore.recipes[0]?.id ?? null
  await loadVariants()
})

async function onRecipeChange() {
  await loadVariants()
  packStore.precheck = null
}

function applyPreset(preset: 'orm' | 'mra' | 'custom') {
  packStore.applyPreset(preset)
  packStore.precheck = null
}

async function precheck() {
  if (!selectedRecipeId.value) return
  const result = await packStore.runPrecheck(selectedRecipeId.value, selectedVariantId.value ?? undefined)
  if (result) {
    message.value = result.message
    messageTone.value = result.ok ? 'ok' : 'error'
  }
}

async function generate() {
  if (!selectedRecipeId.value || !auth.canWrite) return
  const variantId = selectedVariantId.value ?? undefined
  const result = await packStore.runPrecheck(selectedRecipeId.value, variantId)
  if (result && !result.ok) {
    message.value = result.message
    messageTone.value = 'error'
    return
  }
  const pack = await packStore.generate(selectedRecipeId.value, variantId)
  if (pack) {
    message.value = `已生成 ${pack.name}，${pack.status === 'ready' ? '可以下载' : '打包中…'}`
    messageTone.value = 'ok'
  } else {
    message.value = packStore.lastError || '打包失败'
    messageTone.value = 'error'
  }
}

function presetHint() {
  const preset = PACK_PRESETS[packStore.preset]
  if (!preset) return '自定义映射'
  return slots.map((slot) => `${slot.toUpperCase()} ← ${preset[slot] || '未选'}`).join('  ')
}

async function saveProjectPreset() {
  savingPreset.value = true
  try {
    const { savePreset } = await import('../api/pack')
    await savePreset(presetName.value, packStore.mapping as Record<string, string>)
    message.value = `通道映射已另存为项目预设「${presetName.value}」`
    messageTone.value = 'ok'
  } catch (error: any) {
    message.value = error?.message || '预设保存失败'
    messageTone.value = 'error'
  } finally {
    savingPreset.value = false
  }
}
</script>

<template>
  <AppShell section="packs">
    <PageHeader
      title="通道打包"
      kicker="打包 / Channel Packs"
      subtitle="把六张单通道贴图按 ORM / MRA 约定压进 RGBA 四槽，输出 8bit PNG；预检会拦下重复占用与缺失通道。"
      :index="`${packStore.packs.length} PACKS`"
    />

    <PermissionNotice v-if="auth.isViewer" :role="auth.workspaceRole" class="mb-3" />

    <div class="packs-toolbar">
      <div class="control-block">
        <label class="field-label">配方</label>
        <select v-model="selectedRecipeId" class="field" @change="onRecipeChange">
          <option v-for="recipe in recipes" :key="recipe.id" :value="recipe.id">{{ recipe.name }}</option>
        </select>
      </div>
      <div class="control-block">
        <label class="field-label">打包来源变体</label>
        <select v-model="selectedVariantId" class="field">
          <option v-for="variant in variants" :key="variant.id" :value="variant.id">
            rev {{ variant.revision }} · seam {{ variant.seam_score }} · {{ variant.status }}
          </option>
        </select>
      </div>
      <div class="control-block">
        <label class="field-label">输出格式</label>
        <select v-model="packStore.outputFormat" class="field">
          <option value="png">png</option>
          <option value="tga">tga</option>
        </select>
      </div>
      <div class="mono-label toolbar-meta num">
        {{ selectedRecipe ? formatResolution(selectedRecipe.resolution) : '' }}
      </div>
    </div>

    <div v-if="recipes.length" class="packs-layout">
      <section class="pack-builder">
        <div class="preset-row">
          <span class="mono-label">预设 / preset</span>
          <button class="btn btn-sm" :class="{ 'btn-primary': packStore.preset === 'orm' }" @click="applyPreset('orm')">ORM</button>
          <button class="btn btn-sm" :class="{ 'btn-primary': packStore.preset === 'mra' }" @click="applyPreset('mra')">MRA</button>
          <button class="btn btn-sm" :class="{ 'btn-primary': packStore.preset === 'custom' }" @click="applyPreset('custom')">自定义</button>
          <span class="preset-hint mono-label num">{{ presetHint() }}</span>
        </div>

        <div class="slot-grid">
          <div v-for="slot in slots" :key="slot" class="slot">
            <label class="field-label slot-label">{{ slot.toUpperCase() }} 槽</label>
            <select v-model="packStore.mapping[slot]" class="field" :disabled="!auth.canWrite">
              <option value="">未选</option>
              <option v-for="[value, label] in channelOptions" :key="value" :value="value">
                {{ value }} · {{ label }}
              </option>
            </select>
          </div>
        </div>

        <div class="precheck-row">
          <div class="mono-label">映射预检 / channelMath.ts + 后端 pack_service</div>
          <button class="btn btn-sm" :disabled="packStore.loading" @click="precheck">预检通道</button>
          <button class="btn btn-primary" :disabled="!auth.canWrite || packStore.loading" @click="generate">生成通道包</button>
          <button class="btn btn-sm" :disabled="!auth.canWrite || savingPreset" @click="saveProjectPreset">另存为预设</button>
        </div>
        <div class="preset-save">
          <label class="field-label">项目预设名</label>
          <input v-model="presetName" class="field preset-input" />
        </div>

        <div
          v-if="packStore.precheck"
          class="precheck-result"
          :class="{ ok: packStore.precheck.ok }"
        >
          <span class="mono-label">预检结果</span>
          <span>{{ packStore.precheck.message }}</span>
          <span v-if="packStore.precheck.duplicate.length" class="num error-text">
            重复：{{ packStore.precheck.duplicate.join(' / ') }}
          </span>
          <span v-if="packStore.precheck.missing.length" class="num error-text">
            缺失：{{ packStore.precheck.missing.join(' / ') }}
          </span>
        </div>

        <p v-if="message" class="message" :class="messageTone">{{ message }}</p>

        <div class="builder-preview">
          <ChannelStrip :variant="selectedVariant" />
          <div class="mono-label mt-1">{{ mappingSummary() }}</div>
        </div>

        <p class="hint">
          预检会把同一通道被两个槽占用、或所选变体缺通道的情况拦在后端（TEX-1006 / TEX-1005）；
          打包文件写入共享卷 artifact_data，下载走 Nginx 反代。
        </p>
      </section>

      <aside class="pack-history">
        <div class="mono-label history-title">打包记录 / ChannelPack</div>
        <article v-for="pack in packStore.packs" :key="pack.id" class="pack-row">
          <div class="pack-thumb">
            <TextureThumb
              :channel-path="pack.file_path"
              :label="pack.name"
              compact
            />
          </div>
          <div class="pack-main">
            <div class="pack-name">{{ pack.name }}</div>
            <div class="mono-label num">
              {{ pack.preset }} · {{ pack.output_format }} · {{ formatBytes(pack.byte_size) }} ·
              {{ pack.status }}
            </div>
            <div class="mono-label num">{{ formatDate(pack.created_at) }}</div>
            <div class="pack-mapping num">
              {{ Object.entries(pack.channel_mapping_json).map(([slot, channel]) => `${slot.toUpperCase()}=${channel}`).join('  ') }}
            </div>
            <a
              v-if="pack.status === 'ready'"
              class="btn btn-sm pack-download"
              :href="`/api/packs/${pack.id}/download`"
            >
              下载 {{ pack.name }}.png
            </a>
            <span v-else class="mono-label">打包中…</span>
          </div>
        </article>
        <p v-if="!packStore.packs.length" class="hint">还没有打包记录。选 ORM 预设后点「生成通道包」。</p>
      </aside>
    </div>

    <EmptyState
      v-else
      title="没有可打包的配方"
      body="打包需要一条已生成的配方与可用变体。先回样本册打开编辑器，提交一次生成。"
      action-label="去生成一版"
      @action="router.push('/recipes')"
    />

    <div class="pack-note">
      <span class="mono-label">演示交付文件名</span>
      <span class="num">terracotta_wall_orm_1024.png</span>
      <span class="mono-label">·</span>
      <span class="mono-label">R=roughness / G=metallic / B=ao / A=height</span>
    </div>
  </AppShell>
</template>

<style scoped>
.mb-3 {
  margin: 12px 0;
}
.packs-toolbar {
  display: flex;
  align-items: flex-end;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid var(--paper-edge);
  flex-wrap: wrap;
}
.control-block {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 160px;
}
.toolbar-meta {
  margin-left: auto;
  padding-bottom: 8px;
}
.packs-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
  gap: 32px;
  margin-top: 18px;
}
.pack-builder {
  min-width: 0;
}
.preset-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--paper-edge);
}
.preset-hint {
  margin-left: auto;
  font-size: 10px;
}
.slot-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 16px 0;
}
.slot-label {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 18px;
  letter-spacing: 0;
  color: var(--ink);
}
.precheck-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  padding: 12px 0;
  border-top: 1px solid var(--paper-edge);
}
.precheck-result {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  border: 1px solid var(--vermilion);
  padding: 8px 12px;
  font-size: 12px;
  margin-bottom: 8px;
}
.precheck-result.ok {
  border-color: var(--moss);
}
.error-text {
  color: var(--vermilion);
}
.preset-save {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  margin: 8px 0 12px;
}
.preset-input {
  max-width: 220px;
}
.message {
  font-size: 12px;
  margin: 8px 0;
}
.message.ok {
  color: var(--moss);
}
.message.error {
  color: var(--vermilion);
}
.builder-preview {
  border-top: 1px solid var(--paper-edge);
  padding-top: 12px;
}
.hint {
  font-size: 11px;
  color: var(--ink-soft);
  line-height: 1.7;
  margin-top: 16px;
}
.pack-history {
  border-left: 1px solid var(--paper-edge);
  padding-left: 24px;
}
.history-title {
  padding-bottom: 8px;
  border-bottom: 1px solid var(--paper-edge);
}
.pack-row {
  display: grid;
  grid-template-columns: 72px 1fr;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px dotted var(--paper-edge);
}
.pack-thumb {
  width: 72px;
}
.pack-name {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 17px;
}
.pack-mapping {
  font-size: 10px;
  color: var(--ink-soft);
  margin: 4px 0;
}
.pack-download {
  margin-top: 6px;
}
.pack-note {
  margin-top: 28px;
  border-top: 1px solid var(--ink);
  padding: 10px 0;
  display: flex;
  gap: 10px;
  align-items: baseline;
  font-size: 12px;
}
.mt-1 {
  margin-top: 4px;
}
@media (max-width: 1100px) {
  .packs-layout {
    grid-template-columns: 1fr;
  }
  .pack-history {
    border-left: none;
    border-top: 1px solid var(--paper-edge);
    padding: 16px 0 0;
  }
  .slot-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
