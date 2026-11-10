<script setup lang="ts">
import { computed } from 'vue'
import { fileUrl } from '../../api/http'
import { CHANNEL_LABELS, CHANNEL_ORDER, TextureChannel } from '../../constants/channel'
import type { TextureVariant } from '../../types/texture'

const props = defineProps<{ variant: TextureVariant | null; active?: string }>()
const emit = defineEmits<{ (event: 'select', channel: TextureChannel): void }>()

const channels = computed(() => {
  const paths = props.variant?.file_paths_json || {}
  return CHANNEL_ORDER.map((channel, index) => ({
    channel,
    label: CHANNEL_LABELS[channel],
    url: paths[channel] ? fileUrl('artifacts', paths[channel] as string) : '',
    delay: index * 60,
  }))
})
</script>

<template>
  <div class="strip">
    <button
      v-for="item in channels"
      :key="item.channel"
      class="channel stagger-item"
      :class="{ active: props.active === item.channel }"
      :style="{ animationDelay: item.delay + 'ms' }"
      @click="emit('select', item.channel)"
    >
      <img v-if="item.url" :src="item.url" :alt="item.label" />
      <span v-else class="channel-blank" />
      <span class="channel-label mono-label">{{ item.label }}</span>
    </button>
  </div>
</template>

<style scoped>
.strip {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 6px;
}
.channel {
  border: 1px solid var(--paper-edge);
  background: var(--paper-2);
  padding: 0;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  text-align: center;
}
.channel img {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  display: block;
  border-bottom: 1px solid var(--paper-edge);
}
.channel.active {
  border-color: var(--vermilion);
}
.channel.active .channel-label {
  color: var(--vermilion);
}
.channel-blank {
  display: block;
  aspect-ratio: 1 / 1;
  background: var(--paper-2);
}
.channel-label {
  display: block;
  padding: 3px 0;
  font-size: 9px;
}
</style>
