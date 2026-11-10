import http from './http'
import type { ChannelPack, OutputFormat, PackPreset, PackSlot } from '../types/pack'

export async function listPacks(recipeId?: number): Promise<ChannelPack[]> {
  const { data } = await http.get<ChannelPack[]>('/packs', { params: recipeId ? { recipe_id: recipeId } : {} })
  return data
}

export async function presetsRequest(): Promise<{ presets: Record<string, Record<string, string>>; saved: Array<{ name: string; mapping: Record<string, string> }> }> {
  const { data } = await http.get('/packs/presets')
  return data
}

export async function precheckPack(payload: {
  recipe_id: number
  variant_id?: number
  channel_mapping: Partial<Record<PackSlot, string>>
}): Promise<{ ok: boolean; missing_channels: string[]; duplicate_channels: string[]; message: string; resolution: number }> {
  const { data } = await http.post('/packs/precheck', payload)
  return data
}

export async function createPack(payload: {
  recipe_id: number
  variant_id?: number
  name?: string
  channel_mapping: Partial<Record<PackSlot, string>>
  output_format: OutputFormat
  preset: PackPreset
}): Promise<ChannelPack> {
  const { data } = await http.post<ChannelPack>('/packs', payload)
  return data
}

export async function savePreset(name: string, mapping: Record<string, string>) {
  const { data } = await http.post('/packs/presets', { name, mapping })
  return data
}
