<script setup lang="ts">
import { computed, ref } from 'vue'
import { fileUrl } from '../../api/http'
import { formatSeam } from '../../utils/formatters'

const props = withDefaults(
  defineProps<{
    previewPath?: string | null
    channelPath?: string | null
    label?: string
    seam?: number | null
    revision?: number
    compact?: boolean
  }>(),
  { previewPath: null, channelPath: null, label: '', seam: null, revision: undefined, compact: false },
)

const hover = ref(false)
const src = computed(() => {
  if (hover.value && props.channelPath) return fileUrl('artifacts', props.channelPath)
  if (props.previewPath) return fileUrl('previews', props.previewPath)
  if (props.channelPath) return fileUrl('artifacts', props.channelPath)
  return ''
})
const tone = computed(() => {
  if (props.seam === null || props.seam === undefined) return 'var(--ink-soft)'
  if (props.seam >= 75) return 'var(--moss)'
  if (props.seam >= 60) return 'var(--gamboge)'
  return 'var(--vermilion)'
})
</script>

<template>
  <figure class="thumb" :class="{ compact }" @mouseenter="hover = true" @mouseleave="hover = false">
    <div class="thumb-frame">
      <img v-if="src" :src="src" :alt="label || '材质样张'" loading="lazy" />
      <div v-else class="thumb-blank"><span class="mono-label">无样张</span></div>
      <span v-if="seam !== null && seam !== undefined" class="seam-badge num" :style="{ color: tone, borderColor: tone }">
        {{ formatSeam(seam) }}
      </span>
      <span v-if="revision" class="rev-badge num">rev {{ revision }}</span>
    </div>
    <figcaption v-if="label" class="thumb-caption">
      <span>{{ label }}</span>
      <span v-if="channelPath && hover" class="mono-label">单通道</span>
    </figcaption>
  </figure>
</template>

<style scoped>
.thumb {
  margin: 0;
  width: 100%;
}
.thumb-frame {
  position: relative;
  aspect-ratio: 1 / 1;
  border: 1px solid var(--paper-edge);
  background-color: var(--paper-2);
  background-image:
    linear-gradient(45deg, var(--paper-edge) 25%, transparent 25%),
    linear-gradient(-45deg, var(--paper-edge) 25%, transparent 25%),
    linear-gradient(45deg, transparent 75%, var(--paper-edge) 75%),
    linear-gradient(-45deg, transparent 75%, var(--paper-edge) 75%);
  background-size: 12px 12px;
  background-position: 0 0, 0 6px, 6px -6px, -6px 0;
  overflow: hidden;
}
.thumb-frame img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}
.thumb-blank {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
.seam-badge {
  position: absolute;
  right: 5px;
  bottom: 5px;
  background: var(--paper);
  border: 1px solid;
  padding: 0 5px;
  font-size: 10px;
}
.rev-badge {
  position: absolute;
  left: 5px;
  top: 5px;
  background: var(--paper);
  border: 1px solid var(--paper-edge);
  padding: 0 5px;
  font-size: 10px;
  color: var(--ink-soft);
}
.thumb-caption {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  padding-top: 5px;
  font-size: 12px;
  color: var(--ink-soft);
}
.thumb.compact .thumb-caption {
  font-size: 11px;
}
</style>
