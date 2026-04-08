<template>
  <div v-if="action.action_type !== 'no_action'" class="card">
    <div class="card-top">
      <div class="agent-row">
        <span class="agent-dot" :style="{ background: agentColor }"></span>
        <span class="agent-name">{{ personaLabel }}</span>
      </div>
      <span class="action-badge">{{ action.action_type.replace(/_/g, ' ') }}</span>
    </div>

    <p class="headline">{{ action.title }}</p>

    <p class="body" :class="{ expanded }">{{ action.content }}</p>
    <button v-if="action.content?.length > 120" class="more" @click="expanded = !expanded">
      {{ expanded ? 'Less' : 'More' }}
    </button>

    <div class="card-meta">
      <span class="pill" :class="sentimentClass">{{ sentimentLabel }}</span>
      <span v-if="action.reach_estimate" class="pill muted">{{ formatReach(action.reach_estimate) }}</span>
      <span v-if="action.influenced_by?.length" class="pill violet">
        {{ action.influenced_by.length }} {{ action.influenced_by.length === 1 ? 'influence' : 'influences' }}
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  action: Object,
  agentDefs: { type: Object, default: () => ({}) },
})
const expanded = ref(false)

const personaLabel = computed(() =>
  props.agentDefs?.[props.action.persona]?.name
  || props.action.persona?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  || 'Unknown'
)
const agentColor = computed(() => props.agentDefs?.[props.action.persona]?.color || '#666')

const sentimentClass = computed(() => {
  const s = props.action.sentiment_score || 0
  if (s > 0.2) return 'pos'
  if (s < -0.2) return 'neg'
  return 'neu'
})

const sentimentLabel = computed(() => {
  const s = props.action.sentiment_score || 0
  if (s > 0.5) return 'Very positive'
  if (s > 0.2) return 'Positive'
  if (s < -0.5) return 'Very negative'
  if (s < -0.2) return 'Negative'
  return 'Neutral'
})

function formatReach(n) {
  if (!n || n <= 0) return ''
  if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B reach'
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M reach'
  if (n >= 1e3) return (n / 1e3).toFixed(0) + 'K reach'
  return n + ' reach'
}
</script>

<style scoped>
.card {
  padding: 12px 14px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 14px;
  transition: border-color 200ms, background 200ms;
}
.card:hover {
  background: rgba(255,255,255,0.04);
  border-color: rgba(255,255,255,0.1);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.agent-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}
.agent-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.agent-name {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255,255,255,0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.action-badge {
  font-size: 10px;
  color: rgba(255,255,255,0.25);
  text-transform: capitalize;
  flex-shrink: 0;
}

.headline {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255,255,255,0.85);
  line-height: 1.4;
  margin: 0 0 4px;
}
.body {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  line-height: 1.5;
  max-height: 38px;
  overflow: hidden;
  margin: 0;
}
.body.expanded { max-height: none; }
.more {
  background: none;
  border: none;
  padding: 0;
  font-size: 11px;
  color: var(--accent);
  cursor: pointer;
  margin-top: 2px;
  opacity: 0.6;
  transition: opacity 150ms;
}
.more:hover { opacity: 1; }

.card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.pill {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 500;
}
.pill.pos { background: rgba(34,197,94,0.1); color: rgba(34,197,94,0.8); }
.pill.neg { background: rgba(239,68,68,0.1); color: rgba(239,68,68,0.8); }
.pill.neu { background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.3); }
.pill.muted { background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.3); }
.pill.violet { background: rgba(139,92,246,0.1); color: rgba(139,92,246,0.7); }
</style>
