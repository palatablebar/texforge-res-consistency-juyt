import { storeToRefs } from 'pinia'
import { usePreviewStore } from '../stores/previewStore'

export function usePreviewSettings() {
  const store = usePreviewStore()
  const { settings } = storeToRefs(store)
  return { settings, store }
}
