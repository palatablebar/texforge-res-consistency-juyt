<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/authStore'
import QuotaMeter from './QuotaMeter.vue'
import { quotaRequest } from '../../api/auth'
import { usePreviewStore } from '../../stores/previewStore'

const props = defineProps<{ section: string }>()
const auth = useAuthStore()
const router = useRouter()
const preview = usePreviewStore()

const navItems = [
  { key: 'recipes', label: '配方样本册', path: '/recipes' },
  { key: 'preview', label: '材质球预览', path: '/preview' },
  { key: 'variants', label: '版本对比', path: '/variants' },
  { key: 'packs', label: '通道打包', path: '/packs' },
]

const roleText = computed(() => {
  const role = auth.user?.role === 'admin' ? 'TA' : '材质美术'
  const workspace = auth.workspaceRole
  const map: Record<string, string> = { owner: 'owner', editor: 'editor', viewer: '只读 viewer' }
  return auth.workspaceRole === 'viewer' ? '外包 PM' : role
})

onMounted(async () => {
  if (preview.quota) return
  try {
    preview.setQuota(await quotaRequest())
  } catch {
    /* 配额获取失败不阻塞导航 */
  }
})

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="shell">
    <div class="shell-inner">
      <header class="shell-header">
        <div class="brand">
          <span class="brand-mark">TF</span>
          <div>
            <div class="brand-name">TexForge</div>
            <div class="brand-sub">过程式材质样本册 · 栖刻视觉</div>
          </div>
        </div>
        <nav class="nav">
          <RouterLink
            v-for="item in navItems"
            :key="item.key"
            :to="item.path"
            class="nav-link"
            :class="{ active: section === item.key }"
          >
            {{ item.label }}
          </RouterLink>
        </nav>
        <div class="right">
          <QuotaMeter />
          <div class="user">
            <div class="user-name">{{ auth.user?.display_name || '未登录' }}</div>
            <div class="mono-label">{{ roleText }} · {{ auth.workspaceRole }}</div>
          </div>
          <button class="btn btn-sm btn-ghost" @click="logout">退出</button>
        </div>
      </header>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.shell {
  min-height: 100%;
  background: var(--paper);
}
.shell-inner {
  max-width: 1560px;
  margin: 0 auto;
  padding: 0 32px 56px;
}
.shell-header {
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 14px 0;
  border-bottom: 1px solid var(--ink);
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 220px;
}
.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 1px solid var(--ink);
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 15px;
}
.brand-name {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 21px;
  line-height: 1;
}
.brand-sub {
  font-size: 10px;
  letter-spacing: 0.08em;
  color: var(--ink-soft);
}
.nav {
  display: flex;
  gap: 4px;
  flex: 1;
  flex-wrap: wrap;
}
.nav-link {
  padding: 6px 10px;
  color: var(--ink-soft);
  text-decoration: none;
  font-size: 13px;
  border-bottom: 1px solid transparent;
}
.nav-link:hover {
  color: var(--ink);
}
.nav-link.active {
  color: var(--ink);
  border-bottom-color: var(--vermilion);
}
.right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.user {
  text-align: right;
}
.user-name {
  font-size: 13px;
}
@media (max-width: 900px) {
  .shell-inner {
    padding: 0 16px 40px;
  }
  .brand-sub,
  .user {
    display: none;
  }
}
</style>
