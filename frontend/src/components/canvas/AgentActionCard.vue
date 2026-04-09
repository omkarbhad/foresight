<template>
  <div v-if="action.action_type !== 'no_action'" class="card">
    <div class="card-top">
      <span class="agent-dot" :style="{ background: agentColor }"></span>
      <span class="agent-name">{{ personaLabel }}</span>
      <span class="action-type">{{ action.action_type.replace(/_/g, ' ') }}</span>
    </div>

    <p class="title">{{ action.title }}</p>

    <p class="body" :class="{ expanded }">{{ action.content }}</p>
    <button v-if="action.content?.length > 120" class="more" @click="expanded = !expanded">
      {{ expanded ? 'Less' : 'More' }}
    </button>

    <div class="card-footer">
      <span class="sentiment" :class="sentimentClass">{{ sentimentLabel }}</span>
      <span v-if="action.reach_estimate" class="meta">{{ formatReach(action.reach_estimate) }} reach</span>
      <span v-if="action.influenced_by?.length" class="meta">{{ action.influenced_by.length }} {{ action.influenced_by.length === 1 ? 'influence' : 'influences' }}</span>
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
  if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B'
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M'
  if (n >= 1e3) return (n / 1e3).toFixed(0) + 'K'
  return String(n)
}
</script>

<style scoped>
.card {
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.card:last-child { border-bottom: none; }

.card-top {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.agent-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.agent-name {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255,255,255,0.7);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.01em;
}
.action-type {
  font-size: 10px;
  color: rgba(255,255,255,0.2);
  text-transform: capitalize;
  flex-shrink: 0;
  margin-left: auto;
}

.title {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255,255,255,0.85);
  line-height: 1.4;
  margin: 0 0 3px;
  letter-spacing: -0.01em;
}
.body {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  line-height: 1.5;
  max-height: 36px;
  overflow: hidden;
  margin: 0;
}
.body.expanded { max-height: none; }
.more {
  background: none;
  border: none;
  padding: 0;
  font-size: 11px;
  color: rgba(255,255,255,0.3);
  cursor: pointer;
  margin-top: 2px;
  transition: color 150ms;
}
.more:hover { color: rgba(255,255,255,0.6); }

.card-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
  font-size: 11px;
}
.sentiment { font-weight: 500; }
.sentiment.pos { color: rgba(34,197,94,0.7); }
.sentiment.neg { color: rgba(239,68,68,0.7); }
.sentiment.neu { color: rgba(255,255,255,0.2); }
.meta { color: rgba(255,255,255,0.2); }
</style>
