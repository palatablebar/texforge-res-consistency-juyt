import http from './http'
import type { Recipe, RecipeDetail } from '../types/recipe'
import type { RecipeNode } from '../types/node'

export interface RecipeFilters {
  status?: string
  resolution?: number
  q?: string
}

export async function listRecipes(filters: RecipeFilters = {}): Promise<Recipe[]> {
  const { data } = await http.get<Recipe[]>('/recipes', { params: filters })
  return data
}

export async function getRecipe(id: number): Promise<RecipeDetail> {
  const { data } = await http.get<RecipeDetail>(`/recipes/${id}`)
  return data
}

export async function createRecipe(payload: {
  name: string
  description?: string
  resolution: number
  seed?: number
  palette?: string
}): Promise<Recipe> {
  const { data } = await http.post<Recipe>('/recipes', payload)
  return data
}

export async function patchRecipe(id: number, payload: Partial<Pick<Recipe, 'name' | 'description' | 'resolution' | 'seed'>>): Promise<Recipe> {
  const { data } = await http.patch<Recipe>(`/recipes/${id}`, payload)
  return data
}

export async function duplicateRecipe(id: number, name?: string): Promise<Recipe> {
  const { data } = await http.post<Recipe>(`/recipes/${id}/duplicate`, { name })
  return data
}

export async function deleteRecipe(id: number): Promise<void> {
  await http.delete(`/recipes/${id}`)
}

export async function generateVariant(id: number, payload: { seed?: number; resolution?: number } = {}) {
  const { data } = await http.post(`/recipes/${id}/generate`, payload)
  return data as { variant: import('../types/texture').TextureVariant; message: string }
}

export interface NodeBatchItemPayload {
  id: number
  position_x?: number
  position_y?: number
  params_json?: Record<string, unknown>
  input_refs_json?: RecipeNode['input_refs_json']
  is_disabled?: boolean
}

export async function batchUpdateNodes(recipeId: number, nodes: NodeBatchItemPayload[]) {
  const { data } = await http.put(`/recipes/${recipeId}/nodes`, { nodes })
  return data
}
