import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listRecipes, getRecipe } from '../api/recipe'
import type { Recipe, RecipeDetail } from '../types/recipe'

export const useRecipeStore = defineStore('recipe', () => {
  const recipes = ref<Recipe[]>([])
  const current = ref<RecipeDetail | null>(null)
  const loading = ref(false)
  const filters = ref<{ status?: string; resolution?: number; q?: string }>({})
  const toast = ref<string>('')

  async function fetchRecipes() {
    loading.value = true
    try {
      recipes.value = await listRecipes(filters.value)
    } finally {
      loading.value = false
    }
  }

  async function fetchRecipe(id: number) {
    loading.value = true
    try {
      current.value = await getRecipe(id)
      return current.value
    } finally {
      loading.value = false
    }
  }

  function notify(message: string) {
    toast.value = message
    window.setTimeout(() => {
      if (toast.value === message) toast.value = ''
    }, 3200)
  }

  return { recipes, current, loading, filters, toast, fetchRecipes, fetchRecipe, notify }
})
