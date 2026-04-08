<template>
  <div v-if="visible" class="bar">
    <div class="bar-left">
      <span class="item">Round <strong>{{ currentRound }}/{{ totalRounds }}</strong></span>
      <span class="sep">&middot;</span>
      <span class="item">Sentiment <strong :class="sc">{{ sentiment }}</strong></span>
      <span class="sep">&middot;</span>
      <span class="item">Volume <strong>{{ volume }}</strong></span>
      <span class="sep">&middot;</span>
      <span class="item"><strong>{{ agentCount }}</strong> agents</span>
      <span class="sep">&middot;</span>
      <span class="item"><strong>{{ linkCount }}</strong> links</span>
    </div>
    <div v-if="currentAgentName || phaseLabel" class="bar-right">
      <span v-if="currentAgentName" class="agent-status">
        <span class="agent-pulse"></span>
        <span class="agent-name">{{ currentAgentName }}</span>
      </span>
      <span v-if="phaseLabel" class="phase">{{ phaseLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: Boolean,
  currentRound: { type: Number, default: 0 },
  totalRounds: { type: Number, default: 6 },
  metrics: { type: Object, default: () => ({}) },
  agentCount: { type: Number, default: 0 },
  linkCount: { type: Number, default: 0 },
  currentAgentName: { type: String, default: '' },
  currentAgentColor: { type: String, default: '' },
  phase: { type: String, default: '' },
})

const sentiment = computed(() => (props.metrics.avg_sentiment || 0).toFixed(2))
const volume = computed(() => props.metrics.total_volume || 0)
const sc = computed(() => {
  const s = props.metrics.avg_sentiment || 0
  return s > 0.2 ? 'pos' : s < -0.2 ? 'neg' : ''
})

const phaseLabels = {
  planning_agents: 'Selecting agents',
  fetching_scenario_data: 'Fetching data',
  analyzing_sentiment: 'Analyzing',
  creating_agents: 'Creating agents',
  round_execution: '',
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
  border-top: 1px solid rgba(255,255,255,0.06);
  z-index: 50;
  font-size: 11px;
  color: rgba(255,255,255,0.3);
}
.bar-left { display: flex; align-items: center; gap: 3px; }
.bar-right { display: flex; align-items: center; gap: 8px; }
.item { display: flex; gap: 3px; }
.item strong { color: rgba(255,255,255,0.55); font-weight: 500; }
.item strong.pos { color: var(--success); }
.item strong.neg { color: var(--danger); }
.sep { margin: 0 5px; color: rgba(255,255,255,0.1); }
.agent-status {
  display: flex; align-items: center; gap: 5px;
  color: rgba(255,255,255,0.5);
}
.agent-pulse {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent);
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.agent-name { font-weight: 500; }
.phase { color: rgba(255,255,255,0.2); }
</style>
