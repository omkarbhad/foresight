<template>
  <header class="topbar" :class="{ seamless: !scenario }">
    <div class="topbar-left" @click="$emit('reset')">
      <ForesightLogo :size="18" />
      <span class="logo">Foresight</span>
    </div>

    <span v-if="scenario" class="topbar-scenario">{{ scenario.length > 50 ? scenario.slice(0, 48) + '...' : scenario }}</span>

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
import ForesightLogo from './ForesightLogo.vue'

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
  border-bottom: 1px solid rgba(255,255,255,0.08);
  z-index: 100;
  transition: background 150ms, border-color 150ms;
}
.topbar.seamless {
  background: transparent;
  border-bottom-color: transparent;
}
.topbar-left {
  flex-shrink: 0;
  display: flex; align-items: center; gap: 7px;
  cursor: pointer; user-select: none;
}
.topbar-left:hover .logo { color: rgba(255,255,255,0.8); }
.topbar-left:hover :deep(.foresight-logo) { opacity: 1; }
.logo {
  font-weight: 500; font-size: 13px;
  color: rgba(255,255,255,0.5);
  letter-spacing: -0.02em;
  transition: color 150ms;
}
.topbar-scenario {
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  min-width: 0;
}
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
