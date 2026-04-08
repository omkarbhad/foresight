<template>
  <header class="topbar">
    <div class="topbar-left">
      <span class="logo" @click="$emit('reset')">Foresight</span>
    </div>

    <div v-if="phase" class="topbar-center">
      <span class="sc">{{ scenario?.length > 45 ? scenario.slice(0, 43) + '...' : scenario }}</span>
      <span class="dot">&middot;</span>
      <span class="rd">{{ currentRound }}/{{ totalRounds }}</span>
      <span class="dot">&middot;</span>
      <span v-if="running" class="ph">{{ phaseLabel }}</span>
      <span v-else-if="phase === 'completed'" class="done">Done</span>
      <span v-else-if="phase === 'cancelled'" class="warn">Cancelled</span>
    </div>

    <div class="topbar-right">
      <button v-if="running && !cancelling" class="btn-stop" @click="$emit('cancel')">Stop</button>
      <span v-if="cancelling" class="stop-text">Stopping...</span>
      <button v-if="showNewSim" class="btn-new" @click="$emit('reset')">New</button>
      <button class="btn-icon" @click="$emit('toggle-history')" title="History">
        <component :is="ClockIcon" :size="15" :stroke-width="1.5" />
      </button>
      <button class="btn-icon" @click="$emit('open-settings')" title="Settings">
        <component :is="SettingsIcon" :size="15" :stroke-width="1.5" />
      </button>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { Settings as SettingsIcon, Clock as ClockIcon } from 'lucide-vue-next'

const props = defineProps({
  showNewSim: { type: Boolean, default: false },
  running: { type: Boolean, default: false },
  cancelling: { type: Boolean, default: false },
  phase: { type: String, default: '' },
  currentRound: { type: Number, default: 0 },
  totalRounds: { type: Number, default: 6 },
  scenario: { type: String, default: '' },
})
defineEmits(['open-settings', 'toggle-history', 'reset', 'cancel'])

const phaseLabels = {
  planning_agents: 'Selecting agents',
  fetching_scenario_data: 'Fetching data',
  analyzing_sentiment: 'Analyzing',
  graph_init: 'Init graph',
  creating_agents: 'Creating agents',
  round_execution: 'Simulating',
  discovering_agents: 'Discovering entities',
  fetching_entity_data: 'Fetching entity data',
  expanding_agents: 'Expanding agents',
  generating_summary: 'Generating summary',
}
const phaseLabel = computed(() => phaseLabels[props.phase] || props.phase || '')
</script>

<style scoped>
.topbar {
  position: fixed;
  top: 0; left: 0; right: 0;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  background: #0a0a0b;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  z-index: 100;
}
.topbar-left { flex-shrink: 0; }
.logo {
  font-weight: 500; font-size: 13px;
  color: rgba(255,255,255,0.5);
  cursor: pointer; user-select: none;
  letter-spacing: -0.01em;
  transition: color 150ms ease;
}
.logo:hover {
  color: rgba(255,255,255,0.8);
}
.topbar-center {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: var(--text-secondary);
  min-width: 0; overflow: hidden;
}
.sc { color: var(--text-primary); font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dot { color: var(--text-muted); }
.rd { color: var(--text-primary); font-size: 11px; flex-shrink: 0; }
.ph { color: var(--text-muted); flex-shrink: 0; }
.done { color: var(--success); flex-shrink: 0; }
.warn { color: var(--warning); flex-shrink: 0; }

.topbar-right { display: flex; align-items: center; gap: 4px; flex-shrink: 0; }
.btn-icon {
  display: flex; align-items: center; justify-content: center;
  width: 30px; height: 30px;
  background: transparent; border: none; border-radius: 4px;
  color: rgba(255,255,255,0.3);
  transition: color 150ms ease;
}
.btn-icon:hover { color: rgba(255,255,255,0.6); }
.btn-stop {
  padding: 4px 10px;
  background: transparent;
  border: 1px solid rgba(239,68,68,0.4);
  border-radius: 6px;
  color: #ef4444;
  font-size: 11px; font-weight: 500;
  transition: opacity 150ms ease;
}
.btn-stop:hover { opacity: 0.85; }
.stop-text { font-size: 11px; color: #ef4444; }
.btn-new {
  padding: 4px 10px;
  background: white;
  border: none;
  border-radius: 6px;
  color: #0a0a0b;
  font-size: 11px; font-weight: 500;
  transition: opacity 150ms ease;
}
.btn-new:hover { opacity: 0.85; }
</style>
