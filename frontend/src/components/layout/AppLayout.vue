<template>
  <div class="app-layout">
    <AppHeader />
    <AppSidebar />
    <main class="main-content">
      <slot />
    </main>
  </div>
</template>

<script setup>
import AppHeader from './AppHeader.vue'
import AppSidebar from './AppSidebar.vue'
</script>

<style scoped>
.app-layout { min-height: 100vh; }
.main-content {
  margin-left: var(--sidebar-width);
  margin-top: 56px;
  padding: 24px;
  min-height: calc(100vh - 56px);
}
</style>
