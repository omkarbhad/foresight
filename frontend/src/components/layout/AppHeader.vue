<template>
  <header class="app-header">
    <div class="header-left">
      <router-link to="/" class="logo">
        <span class="logo-icon">F</span>
        <span class="logo-text">Foresight</span>
      </router-link>
    </div>
    <div class="header-right">
      <span class="status-badge" :class="{ active: connected }">
        {{ connected ? 'Live' : 'Offline' }}
      </span>
    </div>
  </header>
</template>

<script setup>
import { ref } from 'vue'
const connected = ref(true)
</script>

<style scoped>
.app-header {
  height: 56px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.logo { display: flex; align-items: center; gap: 8px; text-decoration: none; color: var(--text); }
.logo-icon {
  width: 32px; height: 32px; background: var(--primary); color: white;
  border-radius: 8px; display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 16px;
}
.logo-text { font-weight: 700; font-size: 18px; }
.status-badge {
  font-size: 12px; padding: 4px 10px; border-radius: 12px;
  background: #fee2e2; color: var(--danger);
}
.status-badge.active { background: #d1fae5; color: var(--success); }
</style>
