import { computed, ref } from 'vue'
import { NODE_REGISTRY, specFor } from '../constants/nodeRegistry'
import type { InputRef, NodeBatchItem, RecipeNode } from '../types/node'

export function useNodeGraph(nodes: () => RecipeNode[], recipeId: () => number, save: (items: NodeBatchItem[]) => Promise<void>) {
  const selectedId = ref<number | null>(null)
  const undoStack = ref<RecipeNode[][]>([])
  const message = ref('')

  const selected = computed(() => nodes().find((node) => node.id === selectedId.value) || null)

  function select(nodeId: number | null) {
    selectedId.value = nodeId
  }

  function snapshot() {
    undoStack.value.push(JSON.parse(JSON.stringify(nodes())))
    undoStack.value = undoStack.value.slice(-20)
  }

  function undo() {
    const previous = undoStack.value.pop()
    if (!previous) return false
    nodes().splice(0, nodes().length, ...previous)
    return true
  }

  function validateConnection(fromId: number, toId: number, slot: 'a' | 'b'): boolean {
    const target = nodes().find((node) => node.id === toId)
    if (!target) return false
    const slots = specFor(target.node_type)?.inputs || []
    if (!slots.includes(slot)) {
      message.value = `节点 ${target.label} 没有 ${slot} 槽位`
      return false
    }
    // 环检测：从 from 沿输入上溯，若回到 to 则成环
    const byId = new Map(nodes().map((node) => [node.id, node]))
    const stack = [fromId]
    const visited = new Set<number>()
    while (stack.length) {
      const current = stack.pop() as number
      if (current === toId) {
        message.value = '连线会形成环，已拒绝'
        return false
      }
      if (visited.has(current)) continue
      visited.add(current)
      const node = byId.get(current)
      node?.input_refs_json?.forEach((ref) => stack.push(ref.from_node_id))
    }
    return true
  }

  async function connect(fromId: number, toId: number, slot: 'a' | 'b') {
    if (!validateConnection(fromId, toId, slot)) return false
    snapshot()
    const target = nodes().find((node) => node.id === toId)
    if (!target) return false
    const refs: InputRef[] = (target.input_refs_json || []).filter((ref) => ref.slot !== slot)
    refs.push({ slot, from_node_id: fromId })
    target.input_refs_json = refs
    await save([{ id: toId, input_refs_json: refs }])
    message.value = `已连接 ${fromId} → ${toId}（槽位 ${slot}）`
    return true
  }

  function paletteGroups() {
    return ['noise', 'blend', 'operator'].map((group) => ({
      group,
      nodes: NODE_REGISTRY.filter((spec) => spec.group === group),
    }))
  }

  return { selectedId, selected, undoStack, message, select, connect, snapshot, undo, paletteGroups, validateConnection }
}
