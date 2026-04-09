<template>
  <div v-if="visible" class="bar">
    <div class="bar-left">
      <span class="item">Sentiment <strong :class="sc">{{ sentiment }}</strong></span>
      <span class="sep">&middot;</span>
      <span class="item">Volume <strong>{{ volume }}</strong></span>
      <span class="sep">&middot;</span>
      <span class="item"><strong>{{ agentCount }}</strong> agents</span>
      <span class="sep">&middot;</span>
      <span class="item"><strong>{{ linkCount }}</strong> links</span>
    </div>
    <div class="bar-right">
      <span v-if="currentAgentName && status === 'running'" class="agent-active">
        <span class="agent-dot" :style="{ background: currentAgentColor || 'var(--accent)' }"></span>
        {{ currentAgentName }}
      </span>
      <span v-if="currentAgentName && status === 'running'" class="sep">&middot;</span>
      <span class="item">Round <strong>{{ currentRound }}/{{ totalRounds }}</strong></span>
      <span class="sep">&middot;</span>
      <span v-if="status === 'done'" class="status done">Done</span>
      <span v-else-if="status === 'cancelled'" class="status warn">Cancelled</span>
      <span v-else-if="phaseLabel" class="status">{{ phaseLabel }}</span>
      <span v-else class="status">Running</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: Boolean,
  scenario: { type: String, default: '' },
  status: { type: String, default: 'running' },
  currentRound: { type: Number, default: 0 },
  totalRounds: { type: Number, default: 6 },
  metrics: { type: Object, default: () => ({}) },
  agentCount: { type: Number, default: 0 },
  linkCount: { type: Number, default: 0 },
  currentAgentName: { type: String, default: '' },
  currentAgentColor: { type: String, default: '' },
  phase: { type: String, default: '' },
  resultsOpen: { type: Boolean, default: false },
})

const sentiment = computed(() => (props.metrics.final_sentiment ?? props.metrics.avg_sentiment ?? 0).toFixed(2))
const volume = computed(() => props.metrics.total_volume || 0)
const sc = computed(() => {
  const s = props.metrics.final_sentiment ?? props.metrics.avg_sentiment ?? 0
  return s > 0.2 ? 'pos' : s < -0.2 ? 'neg' : ''
})

const phaseLabels = {
  planning_agents: 'Selecting agents',
  fetching_scenario_data: 'Fetching data',
  analyzing_sentiment: 'Analyzing',
  creating_agents: 'Creating agents',
  round_execution: 'Simulating',
  discovering_agents: 'Discovering entities',
  fetching_entity_data: 'Fetching entity data',
  expanding_agents: 'Expanding agents',
  generating_summary: 'Writing analysis',
}
const phaseLabel = computed(() => phaseLabels[props.phase] || '')
</script>

<style scoped>
.bar {
  position: fixed;
  bottom: 0; left: 0; right: 0;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px;
  background: #0a0a0b;
  border-top: 1px solid rgba(255,255,255,0.08);
  z-index: 60;
  font-size: 11px;
  color: rgba(255,255,255,0.3);
}
.bar-left { display: flex; align-items: center; gap: 3px; }
.bar-right { display: flex; align-items: center; gap: 3px; }
.item { display: flex; gap: 3px; white-space: nowrap; }
.item strong { color: rgba(255,255,255,0.55); font-weight: 500; }
.item strong.pos { color: var(--success); }
.item strong.neg { color: var(--danger); }
.sep { margin: 0 5px; color: rgba(255,255,255,0.08); }
.agent-active {
  display: flex; align-items: center; gap: 4px;
  color: rgba(255,255,255,0.5); font-weight: 500; white-space: nowrap;
}
.agent-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.status { color: rgba(255,255,255,0.2); }
.status.done { color: var(--success); }
.status.warn { color: var(--warning); }
</style>
