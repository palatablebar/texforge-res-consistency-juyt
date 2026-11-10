import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { loginRequest, meRequest } from '../api/auth'
import type { QuotaSnapshot, User } from '../types/user'

const TOKEN_KEY = 'texforge_token'
const USER_KEY = 'texforge_user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref<User | null>(JSON.parse(localStorage.getItem(USER_KEY) || 'null'))
  const quota = ref<QuotaSnapshot | null>(null)
  const loading = ref(false)
  const error = ref<string>('')

  const isAuthenticated = computed(() => Boolean(token.value))
  const workspaceRole = computed(() => user.value?.workspace_role || 'viewer')
  const canWrite = computed(() => user.value?.role === 'admin' || ['owner', 'editor'].includes(workspaceRole.value))
  const canDeleteRecipe = computed(() => user.value?.role === 'admin' || workspaceRole.value === 'owner')
  const isViewer = computed(() => !canWrite.value)

  async function login(email: string, password: string) {
    loading.value = true
    error.value = ''
    try {
      const data = await loginRequest(email, password)
      token.value = data.access_token
      user.value = data.user
      quota.value = data.quota
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))
      return true
    } catch (err: any) {
      error.value = err?.message || '登录失败'
      return false
    } finally {
      loading.value = false
    }
  }

  async function refreshMe() {
    if (!token.value) return
    try {
      user.value = await meRequest()
      localStorage.setItem(USER_KEY, JSON.stringify(user.value))
    } catch {
      logout()
    }
  }

  function setQuota(next: QuotaSnapshot | null) {
    quota.value = next
  }

  function logout() {
    token.value = ''
    user.value = null
    quota.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  return {
    token, user, quota, loading, error,
    isAuthenticated, workspaceRole, canWrite, canDeleteRecipe, isViewer,
    login, refreshMe, setQuota, logout,
  }
})
