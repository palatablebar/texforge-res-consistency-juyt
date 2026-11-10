import { CHANNEL_LABELS, TextureChannel } from '../constants/channel'
import { RECIPE_STATUS_LABELS } from '../constants/recipeStatus'
import type { RecipeStatus } from '../types/recipe'

export function formatResolution(resolution: number): string {
  return `${resolution} × ${resolution}`
}

export function formatMs(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return value < 1000 ? `${value} ms` : `${(value / 1000).toFixed(2)} s`
}

export function formatSeam(score: number | null | undefined): string {
  if (score === null || score === undefined) return '—'
  return `${score} · ${seamGrade(score)}`
}

export function seamGrade(score: number): string {
  if (score >= 88) return '优'
  if (score >= 75) return '良'
  if (score >= 60) return '可接受'
  return '需修补'
}

export function channelLabel(channel: string): string {
  return CHANNEL_LABELS[channel as TextureChannel] || channel
}

export function statusLabel(status: string): string {
  return RECIPE_STATUS_LABELS[status as RecipeStatus] || status
}

export function formatDate(value?: string | null): string {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString('zh-CN', { hour12: false })
}
