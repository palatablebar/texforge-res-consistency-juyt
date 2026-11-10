<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/authStore'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const email = ref('ta@qike-vision.com')
const password = ref('TexForge@2026')
const error = ref('')

const demoAccounts = [
  { label: 'TA · 林知远', email: 'ta@qike-vision.com', hint: 'owner · 可建可删' },
  { label: '材质美术 · 沈嘉禾', email: 'artist@qike-vision.com', hint: 'editor · 可生成' },
  { label: '外包 PM · 周倩', email: 'pm@qike-vision.com', hint: 'viewer · 只读下载' },
]

async function submit() {
  error.value = ''
  const ok = await auth.login(email.value, password.value)
  if (!ok) {
    error.value = auth.error || '登录失败'
    return
  }
  const redirect = (route.query.redirect as string) || '/recipes'
  router.push(redirect)
}

function fill(account: (typeof demoAccounts)[number]) {
  email.value = account.email
  password.value = 'TexForge@2026'
}
</script>

<template>
  <div class="login-page">
    <div class="login-frame">
      <section class="login-brand">
        <div class="brand-row">
          <span class="brand-mark">TF</span>
          <div>
            <div class="brand-name">TexForge</div>
            <div class="mono-label">过程式材质纹理生成与通道打包工坊</div>
          </div>
        </div>
        <h1 class="login-title">把节点式配方，<br />变成可复现的 PBR 贴图与通道包。</h1>
        <p class="login-lede">
          栖刻视觉的材质组每天要交付多套材质：客户改一次颜色，就要重连节点、重导六张贴图、按 ORM
          命名打包、传网盘给外包。TexForge 把这一段收进一条可复现的配方：锁定 resolution 与 seed，
          同一张节点图逐像素一致，每次生成留一条 TextureVariant 供对比、回滚与打包。
        </p>
        <dl class="role-table">
          <div class="role-row">
            <dt>TA</dt>
            <dd>owner / editor：搭节点图、定通道规范、删除配方</dd>
          </div>
          <div class="role-row">
            <dt>材质美术</dt>
            <dd>editor：改 seed 出变体、对比接缝、回滚</dd>
          </div>
          <div class="role-row">
            <dt>外包 PM</dt>
            <dd>viewer：只读核对版本与下载打包图</dd>
          </div>
        </dl>
        <div class="login-meta num">PRJ-2611 · 3 条配方 · 6 个变体 · 1 条 ORM 打包</div>
      </section>

      <section class="login-form-panel">
        <div class="form-head">
          <span class="mono-label">样本册登录 / Sign in</span>
          <span class="form-stamp num">2026</span>
        </div>
        <h2 class="form-title">材质样本册</h2>
        <p class="form-sub">演示账号密码统一为 <span class="num">TexForge@2026</span></p>

        <form @submit.prevent="submit">
          <div class="field-row">
            <label class="field-label" for="email">邮箱</label>
            <input id="email" v-model="email" class="field" type="email" autocomplete="username" />
          </div>
          <div class="field-row">
            <label class="field-label" for="password">密码</label>
            <input id="password" v-model="password" class="field" type="password" autocomplete="current-password" />
          </div>
          <p v-if="error" class="login-error" role="alert">{{ error }}</p>
          <button class="btn btn-primary login-submit" type="submit" :disabled="auth.loading">
            {{ auth.loading ? '正在核验…' : '登入样本册' }}
          </button>
        </form>

        <div class="demo-block">
          <div class="mono-label">快速切换演示角色</div>
          <button v-for="account in demoAccounts" :key="account.email" class="demo-row" type="button" @click="fill(account)">
            <span class="demo-label">{{ account.label }}</span>
            <span class="demo-email num">{{ account.email }}</span>
            <span class="mono-label">{{ account.hint }}</span>
          </button>
        </div>
        <p class="login-foot mono-label">
          后端 API http://localhost:19111/docs · 前端 http://localhost:18111
        </p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100%;
  display: flex;
  align-items: stretch;
  padding: 32px;
  background:
    repeating-linear-gradient(to right, var(--paper-grid) 0 1px, transparent 1px 4px),
    repeating-linear-gradient(to bottom, var(--paper-grid) 0 1px, transparent 1px 4px),
    var(--paper);
  background-size: 4px 4px;
}
.login-frame {
  display: grid;
  grid-template-columns: 1.25fr 1fr;
  width: 100%;
  max-width: 1240px;
  margin: auto;
  border: 1px solid var(--ink);
  background: var(--paper);
}
.login-brand {
  padding: 38px 44px;
  border-right: 1px solid var(--ink);
}
.brand-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 44px;
}
.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  border: 1px solid var(--ink);
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 19px;
}
.brand-name {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 26px;
  line-height: 1;
}
.login-title {
  font-size: clamp(28px, 3.4vw, 44px);
  line-height: 1.18;
  margin-bottom: 20px;
}
.login-lede {
  color: var(--ink-soft);
  font-size: 13px;
  line-height: 1.8;
  max-width: 520px;
}
.role-table {
  margin: 30px 0;
  border-top: 1px solid var(--paper-edge);
}
.role-row {
  display: grid;
  grid-template-columns: 84px 1fr;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--paper-edge);
}
.role-row dt {
  font-family: 'Instrument Serif', Georgia, serif;
  font-size: 16px;
}
.role-row dd {
  margin: 0;
  color: var(--ink-soft);
  font-size: 12px;
}
.login-meta {
  font-size: 11px;
  color: var(--ink-soft);
  letter-spacing: 0.06em;
}
.login-form-panel {
  padding: 38px 40px;
  display: flex;
  flex-direction: column;
}
.form-head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--paper-edge);
}
.form-stamp {
  font-size: 11px;
  color: var(--ink-soft);
}
.form-title {
  font-size: 30px;
  margin: 18px 0 2px;
}
.form-sub {
  color: var(--ink-soft);
  font-size: 12px;
  margin: 0 0 22px;
}
.field-row {
  margin-bottom: 14px;
}
.login-submit {
  width: 100%;
  justify-content: center;
  margin-top: 4px;
  padding: 9px 12px;
}
.login-error {
  color: var(--vermilion);
  font-size: 12px;
  margin: 0 0 10px;
}
.demo-block {
  margin-top: 26px;
  border-top: 1px solid var(--paper-edge);
  padding-top: 14px;
}
.demo-row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1px;
  width: 100%;
  text-align: left;
  background: none;
  border: none;
  border-bottom: 1px dotted var(--paper-edge);
  padding: 7px 0;
  cursor: pointer;
  color: var(--ink);
}
.demo-row:hover {
  color: var(--vermilion);
}
.demo-label {
  font-size: 13px;
}
.demo-email {
  font-size: 11px;
  color: var(--ink-soft);
}
.login-foot {
  margin-top: auto;
  padding-top: 20px;
  font-size: 9px;
}
@media (max-width: 900px) {
  .login-frame {
    grid-template-columns: 1fr;
  }
  .login-brand {
    border-right: none;
    border-bottom: 1px solid var(--ink);
    padding: 26px 24px;
  }
  .login-form-panel {
    padding: 26px 24px;
  }
}
</style>
