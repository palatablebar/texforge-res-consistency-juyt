import http from './http'
import type { RecipeNode } from '../types/node'

export async function listNodes(recipeId: number): Promise<RecipeNode[]> {
  const { data } = await http.get<RecipeNode[]>(`/recipes/${recipeId}/nodes`)
  return data
}

export async function createNode(recipeId: number, payload: Partial<RecipeNode>): Promise<RecipeNode> {
  const { data } = await http.post<RecipeNode>(`/recipes/${recipeId}/nodes`, payload)
  return data
}

export async function patchNode(nodeId: number, payload: Partial<RecipeNode>): Promise<RecipeNode> {
  const { data } = await http.patch<RecipeNode>(`/nodes/${nodeId}`, payload)
  return data
}
