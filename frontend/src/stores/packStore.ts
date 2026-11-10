import { defineStore } from 'pinia'
import { ref } from 'vue'
import { createPack, listPacks, precheckPack } from '../api/pack'
import type { ChannelPack, PackPreset, PackSlot } from '../types/pack'

export const usePackStore = defineStore('pack', () => {
  const packs = ref<ChannelPack[]>([])
  const mapping = ref<Partial<Record<PackSlot, string>>>({ r: 'roughness', g: 'metallic', b: 'ao', a: 'height' })
  const preset = ref<PackPreset>('orm')
  const outputFormat = ref<'png' | 'tga'>('png')
  const precheck = ref<{ ok: boolean; message: string; missing: string[]; duplicate: string[] } | null>(null)
  const loading = ref(false)
  const lastError = ref('')

  async function fetchPacks(recipeId?: number) {
    packs.value = await listPacks(recipeId)
  }

  function applyPreset(next: PackPreset) {
    preset.value = next
    if (next === 'orm') mapping.value = { r: 'roughness', g: 'metallic', b: 'ao', a: 'height' }
    if (next === 'mra') mapping.value = { r: 'metallic', g: 'roughness', b: 'ao', a: 'height' }
  }

  async function runPrecheck(recipeId: number, variantId?: number) {
    loading.value = true
    try {
      const result = await precheckPack({ recipe_id: recipeId, variant_id: variantId, channel_mapping: mapping.value })
      precheck.value = {
        ok: result.ok,
        message: result.message,
        missing: result.missing_channels,
        duplicate: result.duplicate_channels,
      }
      return result
    } catch (error: any) {
      lastError.value = error?.message || '预检失败'
      return null
    } finally {
      loading.value = false
    }
  }

  async function generate(recipeId: number, variantId?: number, name?: string) {
    loading.value = true
    lastError.value = ''
    try {
      const pack = await createPack({
        recipe_id: recipeId,
        variant_id: variantId,
        name,
        channel_mapping: mapping.value,
        output_format: outputFormat.value,
        preset: preset.value,
      })
      packs.value = [pack, ...packs.value]
      return pack
    } catch (error: any) {
      lastError.value = error?.message || '打包失败'
      return null
    } finally {
      loading.value = false
    }
  }

  return { packs, mapping, preset, outputFormat, precheck, loading, lastError, fetchPacks, applyPreset, runPrecheck, generate }
})
