import { defineStore } from 'pinia'
import { ref } from 'vue'
import { batchUpdateNodes } from '../api/recipe'
import type { NodeBatchItem, RecipeNode } from '../types/node'

export const useNodeGraphStore = defineStore('nodeGraph', () => {
  const nodes = ref<RecipeNode[]>([])
  const selectedNodeId = ref<number | null>(null)
  const zoom = ref(1)
  const saving = ref(false)
  const history = ref<string[]>([])

  function setNodes(next: RecipeNode[]) {
    nodes.value = next
    if (next.length && selectedNodeId.value === null) selectedNodeId.value = next[0].id
  }

  function selectedNode() {
    return nodes.value.find((node) => node.id === selectedNodeId.value) || null
  }

  function select(nodeId: number) {
    selectedNodeId.value = nodeId
  }

  function moveNode(nodeId: number, x: number, y: number) {
    const node = nodes.value.find((item) => item.id === nodeId)
    if (!node) return
    node.position_x = x
    node.position_y = y
  }

  async function persistPositions(recipeId: number, changed: NodeBatchItem[]) {
    saving.value = true
    try {
      await batchUpdateNodes(recipeId, changed)
      history.value.unshift(`${new Date().toLocaleTimeString('zh-CN', { hour12: false })} 保存 ${changed.length} 个节点`)
      history.value = history.value.slice(0, 20)
    } finally {
      saving.value = false
    }
  }

  async function saveParams(recipeId: number, nodeId: number, params: Record<string, unknown>) {
    return persistPositions(recipeId, [{ id: nodeId, params_json: params }])
  }

  return { nodes, selectedNodeId, zoom, saving, history, setNodes, selectedNode, select, moveNode, persistPositions, saveParams }
})
