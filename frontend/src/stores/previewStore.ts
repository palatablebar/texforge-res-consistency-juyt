import { defineStore } from 'pinia'
import { computed, ref, watch } from 'vue'
import type { QuotaSnapshot } from '../types/quota'

const SETTINGS_KEY = 'texforge_preview_settings'

export interface PreviewSettings {
  envIntensity: number
  rotation: number
  exposure: number
  tiling: number
  normalScale: number
}

const defaults: PreviewSettings = {
  envIntensity: 1.1,
  rotation: 24,
  exposure: 1.0,
  tiling: 1,
  normalScale: 1.0,
}

export const usePreviewStore = defineStore('preview', () => {
  const stored = JSON.parse(localStorage.getItem(SETTINGS_KEY) || 'null') as PreviewSettings | null
  const settings = ref<PreviewSettings>({ ...defaults, ...(stored || {}) })
  const quota = ref<QuotaSnapshot | null>(null)
  const polling = ref(false)
  const lastError = ref<string>('')

  watch(
    settings,
    (value) => localStorage.setItem(SETTINGS_KEY, JSON.stringify(value)),
    { deep: true },
  )

  const remaining = computed(() => quota.value?.remaining ?? null)

  function setQuota(next: QuotaSnapshot | null) {
    quota.value = next
  }

  return { settings, quota, polling, lastError, remaining, setQuota }
})
