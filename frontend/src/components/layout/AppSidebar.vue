<template>
  <nav class="sidebar">
    <div class="nav-section">
      <router-link to="/simulation" class="nav-item" :class="{ active: $route.path === '/simulation' || $route.path === '/' }">
        <span class="nav-icon">&#9881;</span> Simulation
      </router-link>
    </div>
  </nav>
</template>

<style scoped>
.sidebar {
  width: var(--sidebar-width);
  height: calc(100vh - 56px);
  background: var(--surface);
  border-right: 1px solid var(--border);
  position: fixed;
  top: 56px;
  left: 0;
  padding: 16px 0;
  overflow-y: auto;
}
.nav-section { padding: 0 12px; margin-bottom: 16px; }
.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 8px; text-decoration: none;
  color: var(--text-secondary); font-size: 14px; font-weight: 500;
  transition: all 0.15s;
}
.nav-item:hover { background: #f1f5f9; color: var(--text); }
.nav-item.active { background: #eff6ff; color: var(--primary); font-weight: 600; }
.nav-icon { font-size: 16px; width: 20px; text-align: center; }
</style>
