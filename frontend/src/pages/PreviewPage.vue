<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from '../components/common/AppShell.vue'
import PageHeader from '../components/common/PageHeader.vue'
import EmptyState from '../components/common/EmptyState.vue'
import PermissionNotice from '../components/common/PermissionNotice.vue'
import MaterialSphere from '../components/texture/MaterialSphere.vue'
import ChannelStrip from '../components/texture/ChannelStrip.vue'
import SeamScoreBar from '../components/texture/SeamScoreBar.vue'
import { useAuthStore } from '../stores/authStore'
import { useRecipeStore } from '../stores/recipeStore'
import { usePreviewStore } from '../stores/previewStore'
import { listVariants } from '../api/variant'
import { fileUrl } from '../api/http'
import { CHANNEL_LABELS, CHANNEL_ORDER, TextureChannel } from '../constants/channel'
import { formatMs, formatResolution, formatSeam } from '../utils/formatters'
import type { TextureVariant } from '../types/texture'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const recipeStore = useRecipeStore()
const preview = usePreviewStore()

const recipes = computed(() => recipeStore.recipes)
const selectedRecipeId = ref<number | null>(null)
const variants = ref<TextureVariant[]>([])
const selectedVariantId = ref<number | null>(null)
const activeChannel = ref<TextureChannel>(TextureChannel.BASE_COLOR)
const loading = ref(false)
const usingFallback = ref(false)

const selectedRecipe = computed(() => recipes.value.find((recipe) => recipe.id === selectedRecipeId.value) || null)
const selectedVariant = computed(() => variants.value.find((variant) => variant.id === selectedVariantId.value) || null)
const activeChannelUrl = computed(() => {
  const path = selectedVariant.value?.file_paths_json?.[activeChannel.value]
  return path ? fileUrl('artifacts', path) : ''
})

async function loadVariants() {
  if (!selectedRecipeId.value) return
  loading.value = true
  try {
    variants.value = await listVariants(selectedRecipeId.value)
    const preferred = selectedVariantId.value && variants.value.some((variant) => variant.id === selectedVariantId.value)
      ? selectedVariantId.value
      : variants.value[0]?.id ?? null
    selectedVariantId.value = preferred
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (!recipeStore.recipes.length) await recipeStore.fetchRecipes()
  const queryId = Number(route.query.recipe)
  selectedRecipeId.value = recipeStore.recipes.some((recipe) => recipe.id === queryId)
    ? queryId
    : recipeStore.recipes[0]?.id ?? null
  await loadVariants()
})

watch(selectedRecipeId, async () => {
  selectedVariantId.value = null
  await loadVariants()
  if (selectedRecipeId.value) router.replace({ query: { recipe: String(selectedRecipeId.value) } })
})

watch(selectedVariant, (variant) => {
  if (variant) activeChannel.value = TextureChannel.BASE_COLOR
})

function updateSetting(key: keyof typeof preview.settings, value: number) {
  preview.settings[key] = value
}
</script>

<template>
  <AppShell section="preview">
    <PageHeader
      title="材质球预览"
      kicker="预览 / Preview"
      subtitle="材质球只消费后端算出的贴图：切换变体、调环境光与 tiling，检查法线强度与重复感。"
      :index="selectedRecipe ? `REV ${variants.length}` : 'NO RECIPE'"
    />

    <PermissionNotice v-if="auth.isViewer" :role="auth.workspaceRole" class="mb-3" />

    <div v-if="recipes.length" class="preview-layout">
      <section class="sphere-column">
        <MaterialSphere
          :variant="selectedVariant"
          :env-intensity="preview.settings.envIntensity"
          :rotation="preview.settings.rotation"
          :exposure="preview.settings.exposure"
          :tiling="preview.settings.tiling"
          :normal-scale="preview.settings.normalScale"
        />
        <div class="channel-row">
          <ChannelStrip :variant="selectedVariant" :active="activeChannel" @select="activeChannel = $event" />
        </div>
        <div class="channel-single">
          <div class="mono-label">单通道 · {{ CHANNEL_LABELS[activeChannel] }}</div>
          <img v-if="activeChannelUrl" :src="activeChannelUrl" :alt="activeChannel" class="channel-image" />
        </div>
      </section>

      <aside class="preview-controls">
        <div class="control-block">
          <label class="field-label">配方</label>
          <select v-model="selectedRecipeId" class="field">
            <option v-for="recipe in recipes" :key="recipe.id" :value="recipe.id">{{ recipe.name }}</option>
          </select>
          <div class="mono-label num mt-1">
            {{ selectedRecipe ? formatResolution(selectedRecipe.resolution) : '' }} · {{ selectedRecipe?.node_count }} nodes
          </div>
        </div>
        <div class="control-block">
          <label class="field-label">变体 / revision</label>
          <select v-model="selectedVariantId" class="field" :disabled="loading">
            <option v-for="variant in variants" :key="variant.id" :value="variant.id">
              rev {{ variant.revision }} · seed {{ variant.seed_used }} · seam {{ variant.seam_score }}
            </option>
          </select>
        </div>

        <SeamScoreBar :score="selectedVariant?.seam_score ?? null" show-threshold />

        <div class="mono-label controls-title">预览参数 / 写入 localStorage</div>
        <div class="slider-row">
          <label class="field-label">环境光强度 <span class="num">{{ preview.settings.envIntensity.toFixed(2) }}</span></label>
          <input type="range" min="0" max="2.5" step="0.01" :value="preview.settings.envIntensity" @input="updateSetting('envIntensity', Number(($event.target as HTMLInputElement).value))" />
        </div>
        <div class="slider-row">
          <label class="field-label">旋转角 <span class="num">{{ preview.settings.rotation }}°</span></label>
          <input type="range" min="0" max="360" step="1" :value="preview.settings.rotation" @input="updateSetting('rotation', Number(($event.target as HTMLInputElement).value))" />
        </div>
        <div class="slider-row">
          <label class="field-label">曝光 <span class="num">{{ preview.settings.exposure.toFixed(2) }}</span></label>
          <input type="range" min="0.4" max="2" step="0.01" :value="preview.settings.exposure" @input="updateSetting('exposure', Number(($event.target as HTMLInputElement).value))" />
        </div>
        <div class="slider-row">
          <label class="field-label">tiling 次数 <span class="num">×{{ preview.settings.tiling }}</span></label>
          <input type="range" min="1" max="6" step="1" :value="preview.settings.tiling" @input="updateSetting('tiling', Number(($event.target as HTMLInputElement).value))" />
        </div>
        <div class="slider-row">
          <label class="field-label">法线强度 <span class="num">{{ preview.settings.normalScale.toFixed(2) }}</span></label>
          <input type="range" min="0" max="2.5" step="0.01" :value="preview.settings.normalScale" @input="updateSetting('normalScale', Number(($event.target as HTMLInputElement).value))" />
        </div>

        <div class="variant-meta num">
          <div><span class="mono-label">generation_ms</span> {{ formatMs(selectedVariant?.generation_ms) }}</div>
          <div><span class="mono-label">seam_score</span> {{ formatSeam(selectedVariant?.seam_score) }}</div>
          <div><span class="mono-label">checksum</span> {{ selectedVariant?.checksum?.slice(0, 16) || '—' }}</div>
          <div><span class="mono-label">算法版本</span> v{{ selectedVariant?.algo_version || 1 }}</div>
          <div><span class="mono-label">预览图</span> 后端 numpy 球体着色</div>
        </div>

        <div class="channel-links">
          <div class="mono-label">单通道下载</div>
          <a
            v-for="channel in CHANNEL_ORDER"
            :key="channel"
            class="channel-link num"
            :href="selectedVariant?.file_paths_json?.[channel] ? fileUrl('artifacts', selectedVariant.file_paths_json[channel]) : '#'"
            target="_blank"
            rel="noreferrer"
          >
            {{ channel }} · {{ CHANNEL_LABELS[channel] }}
          </a>
        </div>
      </aside>
    </div>

    <EmptyState
      v-else
      title="还没有可预览的配方"
      body="先到样本册里建一条配方并提交生成，材质球会读取后端产出的六张通道贴图。"
      action-label="去样本册"
      @action="router.push('/recipes')"
    />
  </AppShell>
</template>

<style scoped>
.mb-3 {
  margin: 12px 0;
}
.preview-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 28px;
  margin-top: 8px;
}
.sphere-column {
  min-width: 0;
}
.channel-row {
  margin-top: 14px;
}
.channel-single {
  margin-top: 18px;
  border-top: 1px solid var(--paper-edge);
  padding-top: 12px;
}
.channel-image {
  margin-top: 8px;
  width: 100%;
  max-width: 420px;
  border: 1px solid var(--paper-edge);
  display: block;
}
.preview-controls {
  border-left: 1px solid var(--paper-edge);
  padding-left: 22px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.control-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.controls-title {
  padding-top: 12px;
  border-top: 1px solid var(--paper-edge);
}
.slider-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.variant-meta {
  border-top: 1px solid var(--paper-edge);
  padding-top: 10px;
  font-size: 11px;
  display: flex;
  flex-direction: column;
  gap: 3px;
  color: var(--ink-soft);
}
.channel-links {
  display: flex;
  flex-direction: column;
  gap: 3px;
  border-top: 1px solid var(--paper-edge);
  padding-top: 10px;
}
.channel-link {
  font-size: 11px;
  color: var(--ink-soft);
}
.channel-link:hover {
  color: var(--vermilion);
}
.mt-1 {
  margin-top: 4px;
}
@media (max-width: 1100px) {
  .preview-layout {
    grid-template-columns: 1fr;
  }
  .preview-controls {
    border-left: none;
    border-top: 1px solid var(--paper-edge);
    padding: 18px 0 0;
  }
}
</style>
