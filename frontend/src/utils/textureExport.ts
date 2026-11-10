import { CHANNEL_LABELS, TextureChannel } from '../constants/channel'
import type { TextureVariant } from '../types/texture'

export function channelFileName(slug: string, revision: number, channel: TextureChannel): string {
  const short = CHANNEL_LABELS[channel] || channel
  return `${slug}_rev${revision}_${channel}_${short}.png`
}

export function channelDownloadList(variant: TextureVariant): Array<{ channel: TextureChannel; url: string; name: string }> {
  const entries = Object.entries(variant.file_paths_json || {}) as Array<[TextureChannel, string]>
  return entries.map(([channel, rel]) => ({
    channel,
    url: `/api/files/artifacts/${rel}`,
    name: channelFileName(`recipe-${variant.recipe_id}`, variant.revision, channel),
  }))
}

export function packDownloadUrl(packId: number): string {
  return `/api/packs/${packId}/download`
}
