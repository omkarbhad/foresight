<template>
  <router-view />
</template>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg-base: #0a0a0b;
  --bg-surface: rgba(255,255,255,0.03);
  --bg-card: rgba(255,255,255,0.04);
  --bg-hover: rgba(255,255,255,0.06);
  --border: rgba(255,255,255,0.07);
  --border-strong: rgba(255,255,255,0.12);
  --text-primary: rgba(255,255,255,0.92);
  --text-secondary: rgba(255,255,255,0.7);
  --text-muted: rgba(255,255,255,0.4);
  --text-placeholder: rgba(255,255,255,0.25);
  --accent: #8b5cf6;
  --accent-hover: #a78bfa;
  --accent-ring: rgba(139,92,246,0.3);
  --btn-active-bg: #ffffff;
  --btn-active-text: #0a0a0b;
  --btn-inactive-bg: rgba(255,255,255,0.05);
  --btn-inactive-text: rgba(255,255,255,0.4);
  --danger: #ef4444;
  --success: #22c55e;
  --warning: #eab308;
}

#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  letter-spacing: -0.01em;
  color: var(--text-primary);
  background: #0a0a0b;
  min-height: 100vh;
}

strong, b { font-weight: 600; }

::selection { background: rgba(139, 92, 246, 0.3); }

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--border-strong); }

button { font-family: inherit; cursor: pointer; }
input, select, textarea { font-family: inherit; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
</style>
