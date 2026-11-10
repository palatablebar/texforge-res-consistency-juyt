import http from './http'
import type { TextureVariant } from '../types/texture'

export async function listVariants(recipeId: number): Promise<TextureVariant[]> {
  const { data } = await http.get<TextureVariant[]>(`/recipes/${recipeId}/variants`)
  return data
}

export async function getVariant(id: number): Promise<TextureVariant> {
  const { data } = await http.get<TextureVariant>(`/variants/${id}`)
  return data
}

export async function setCurrentVariant(id: number): Promise<TextureVariant> {
  const { data } = await http.post(`/variants/${id}/current`)
  return data.variant as TextureVariant
}

export async function deleteVariant(id: number): Promise<void> {
  await http.delete(`/variants/${id}`)
}
