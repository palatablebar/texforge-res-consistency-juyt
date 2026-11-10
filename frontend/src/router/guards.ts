import type { Router } from 'vue-router'
import { useAuthStore } from '../stores/authStore'

export function installGuards(router: Router): void {
  router.beforeEach((to) => {
    const auth = useAuthStore()
    if (to.path === '/login') {
      return auth.isAuthenticated ? { path: '/recipes' } : true
    }
    if (!auth.isAuthenticated) {
      return { path: '/login', query: { redirect: to.fullPath } }
    }
    return true
  })
}
