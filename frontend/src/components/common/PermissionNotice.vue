<script setup lang="ts">
defineProps<{ role: string }>()
</script>

<template>
  <div class="permission">
    <span class="mono-label">只读账号</span>
    <span class="permission-text">
      当前工作区角色为 <span class="num">{{ role }}</span>，可以查看与下载，但生成、编辑与删除按钮已被禁用。
    </span>
  </div>
</template>

<style scoped>
.permission {
  display: flex;
  align-items: baseline;
  gap: 10px;
  border: 1px dashed var(--paper-edge);
  padding: 8px 12px;
  font-size: 12px;
  color: var(--ink-soft);
}
.permission-text {
  color: var(--ink);
}
</style>
