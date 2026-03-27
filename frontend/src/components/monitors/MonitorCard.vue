<template>
  <div class="monitor-card" :class="{ 'monitor-card--inactive': !monitor.is_active }">
    <div class="card-header">
      <h3 class="card-name">{{ monitor.name }}</h3>
      <button
        class="toggle-btn"
        :class="{ 'toggle-btn--active': monitor.is_active }"
        :title="monitor.is_active ? 'Deactivate' : 'Activate'"
        @click="$emit('toggle-active', monitor)"
      >
        <span class="toggle-track">
          <span class="toggle-thumb"></span>
        </span>
        <span class="toggle-label">{{ monitor.is_active ? 'Active' : 'Inactive' }}</span>
      </button>
    </div>

    <div v-if="monitor.keywords && monitor.keywords.length" class="card-section">
      <span class="section-label">Keywords</span>
      <div class="pills">
        <span v-for="kw in monitor.keywords" :key="kw" class="pill">{{ kw }}</span>
      </div>
    </div>

    <div v-if="monitor.sources && monitor.sources.length" class="card-section">
      <span class="section-label">Sources</span>
      <div class="badges">
        <span
          v-for="src in monitor.sources"
          :key="src"
          class="badge"
          :class="'badge--' + src"
        >
          {{ src }}
        </span>
      </div>
    </div>

    <div class="card-actions">
      <button class="action-btn" title="Edit" @click="$emit('edit', monitor)">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M11.5 1.5l3 3L5 14H2v-3L11.5 1.5z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span>Edit</span>
      </button>
      <button class="action-btn" title="View Mentions" @click="$emit('view-mentions', monitor)">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 4h12M2 8h12M2 12h8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
        <span>Mentions</span>
      </button>
      <button class="action-btn" title="View Trends" @click="$emit('view-trends', monitor)">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 14l4-5 3 3 5-7" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span>Trends</span>
      </button>
      <button class="action-btn action-btn--danger" title="Delete" @click="$emit('delete', monitor)">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M3 4h10M6 4V3a1 1 0 011-1h2a1 1 0 011 1v1M5 4v9a1 1 0 001 1h4a1 1 0 001-1V4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
        <span>Delete</span>
      </button>
    </div>
  </div>
</template>

<script setup>
defineProps({
  monitor: {
    type: Object,
    required: true,
  },
})

defineEmits(['edit', 'delete', 'toggle-active', 'view-mentions', 'view-trends'])
</script>

<style scoped>
.monitor-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s ease, transform 0.2s ease, opacity 0.2s ease;
}

.monitor-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
  transform: translateY(-1px);
}

.monitor-card--inactive {
  opacity: 0.6;
}

/* Header */
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-name {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin: 0;
}

/* Toggle */
.toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.toggle-track {
  width: 36px;
  height: 20px;
  background: var(--border);
  border-radius: 10px;
  position: relative;
  transition: background 0.2s ease;
  display: block;
}

.toggle-btn--active .toggle-track {
  background: var(--success);
}

.toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.15);
}

.toggle-btn--active .toggle-thumb {
  transform: translateX(16px);
}

.toggle-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
}

/* Sections */
.card-section {
  margin-bottom: 14px;
}

.section-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

/* Pills */
.pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pill {
  display: inline-block;
  padding: 3px 10px;
  font-size: 12px;
  font-weight: 500;
  color: var(--primary);
  background: color-mix(in srgb, var(--primary) 12%, transparent);
  border-radius: 16px;
}

/* Badges */
.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.badge {
  display: inline-block;
  padding: 3px 10px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border-radius: 6px;
}

.badge--news {
  color: var(--primary);
  background: color-mix(in srgb, var(--primary) 12%, transparent);
}

.badge--reddit {
  color: var(--warning);
  background: color-mix(in srgb, var(--warning) 12%, transparent);
}

.badge--twitter {
  color: #1da1f2;
  background: color-mix(in srgb, #1da1f2 12%, transparent);
}

/* Actions */
.card-actions {
  display: flex;
  gap: 4px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: color-mix(in srgb, var(--primary) 8%, transparent);
  color: var(--primary);
  border-color: color-mix(in srgb, var(--primary) 30%, transparent);
}

.action-btn--danger:hover {
  background: color-mix(in srgb, var(--danger) 8%, transparent);
  color: var(--danger);
  border-color: color-mix(in srgb, var(--danger) 30%, transparent);
}
</style>
