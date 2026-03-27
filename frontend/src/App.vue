<template>
  <router-view />
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --primary: #2563eb;
  --primary-light: #3b82f6;
  --danger: #ef4444;
  --warning: #f59e0b;
  --success: #10b981;
  --neutral: #6b7280;
  --bg: #f8fafc;
  --surface: #ffffff;
  --border: #e2e8f0;
  --text: #1e293b;
  --text-secondary: #64748b;
  --sidebar-width: 240px;
}

#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  -webkit-font-smoothing: antialiased;
  color: var(--text);
  background-color: var(--bg);
  min-height: 100vh;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #94a3b8; }

button { font-family: inherit; cursor: pointer; }
input, select, textarea { font-family: inherit; }
</style>
