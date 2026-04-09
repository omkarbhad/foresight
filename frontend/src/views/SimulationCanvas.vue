<template>
  <div class="canvas">
    <FloatingAgents v-if="state === 'idle'" />
    <div class="glow-bg" aria-hidden="true">
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="blob blob-3"></div>
    </div>
    <TopBar
      :showNewSim="state === 'results'"
      :running="state === 'running'"
      :cancelling="cancelling"
      :phase="phase"
      :currentRound="currentRound"
      :totalRounds="totalRounds"
      :scenario="currentScenario"
      @open-settings="showSettings = true"
      @toggle-history="showHistory = !showHistory"
      @reset="resetToIdle"
      @cancel="handleCancel"
    />

    <SettingsModal
      :visible="showSettings"
      @close="showSettings = false"
      @saved="onSettingsSaved"
    />

    <!-- Idle: form -->
    <SimulationForm
      v-if="state === 'idle'"
      @submit="handleStart"
    />

    <!-- Running + Results: graph -->
    <InfluenceGraph
      v-if="state === 'running' || state === 'results'"
      :visible="state === 'running' || state === 'results'"
      :agentDefs="agentDefs"
      :influenceLog="influenceLog"
      :agentTimeline="agentTimeline"
      :currentRound="currentRound"
      :scenarioMap="scenarioMap"
      :agentScenarioMap="agentScenarioMap"
      :resultsOpen="state === 'results' && resultsView === 'sidebar'"
    />

    <!-- Running + Results: action feed -->
    <ActionFeed
      v-if="state === 'running' || state === 'results'"
      :visible="state === 'running' || state === 'results'"
      :actions="allActions"
      :agentDefs="agentDefs"
    />

    <!-- Running + Results: bottom bar with everything -->
    <MetricsBar
      v-if="state === 'running' || state === 'results'"
      :visible="state === 'running' || state === 'results'"
      :scenario="currentScenario"
      :status="state === 'results' ? 'done' : (phase === 'cancelled' ? 'cancelled' : 'running')"
      :currentRound="currentRound"
      :totalRounds="totalRounds"
      :metrics="state === 'results' ? (resultData?.aggregate_metrics || computedAggregateMetrics) : latestMetrics"
      :agentCount="Object.keys(agentDefs).length"
      :linkCount="influenceLog.length"
      :currentAgentName="currentAgent ? (agentDefs[currentAgent]?.name || currentAgent) : ''"
      :currentAgentColor="agentDefs[currentAgent]?.color || ''"
      :phase="phase"
      :resultsOpen="state === 'results' && resultsView === 'sidebar'"
    />

    <!-- Results: full-page results view -->
    <ResultsSummary
      :visible="state === 'results'"
      :view="resultsView"
      :aggregateMetrics="resultData?.aggregate_metrics || computedAggregateMetrics"
      :totalRounds="resultData?.total_rounds || totalRounds"
      :agentDefs="agentDefs"
      :rounds="rounds"
      :influenceLog="influenceLog"
      @toggle-view="resultsView = resultsView === 'sidebar' ? 'fullpage' : 'sidebar'"
    />

    <!-- Error state -->
    <div v-if="state === 'error'" class="error-card">
      <h3>Simulation Failed</h3>
      <p>{{ errorMsg }}</p>
      <button class="btn-retry" @click="resetToIdle">Try Again</button>
    </div>

    <!-- History dropdown -->
    <div v-if="showHistory && (state === 'idle' || state === 'results')" class="history-panel">
      <div v-if="history.length === 0" class="history-empty">No past simulations</div>
      <div v-for="sim in history" :key="sim.simulation_id" class="history-item" @click="loadSimulation(sim)">
        <div class="hist-row">
          <span class="hist-scenario">{{ sim.scenario?.slice(0, 60) }}{{ sim.scenario?.length > 60 ? '...' : '' }}</span>
          <span
            v-if="sim.aggregate_metrics?.final_sentiment != null"
            class="hist-sentiment"
            :style="{ color: sim.aggregate_metrics.final_sentiment >= 0 ? 'var(--success)' : 'var(--danger)' }"
          >{{ sim.aggregate_metrics.final_sentiment >= 0 ? '+' : '' }}{{ sim.aggregate_metrics.final_sentiment.toFixed(2) }}</span>
        </div>
        <div class="hist-meta">
          {{ sim.total_rounds }} rounds<span v-if="sim.created_at"> · {{ sim.created_at.slice(0, 10) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import FloatingAgents from '../components/canvas/FloatingAgents.vue'
import TopBar from '../components/canvas/TopBar.vue'
import SettingsModal from '../components/canvas/SettingsModal.vue'
import SimulationForm from '../components/canvas/SimulationForm.vue'
import InfluenceGraph from '../components/canvas/InfluenceGraph.vue'
import ActionFeed from '../components/canvas/ActionFeed.vue'
import MetricsBar from '../components/canvas/MetricsBar.vue'
import ResultsSummary from '../components/canvas/ResultsSummary.vue'
import { createSimulation, listSimulations, getSimulation, getTaskStatus, cancelTask, getSettingsStatus } from '../api/simulation'

// State machine
const state = ref('idle')
const taskId = ref(null)

const resultData = ref(null)
const errorMsg = ref('')
const showSettings = ref(false)
const showHistory = ref(false)
const cancelling = ref(false)
const history = ref([])
const llmConfigured = ref(false)
const currentScenario = ref('')
const resultsView = ref('sidebar') // 'sidebar' or 'fullpage'

// Live simulation data
const rounds = ref([])
const currentRound = ref(0)
const totalRounds = ref(6)
const phase = ref('')
const currentAgent = ref('')
const influenceLog = ref([])
const agentDefs = ref({})
const agentTimeline = ref([])
const scenarioMap = ref({})
const agentScenarioMap = ref({})

let pollTimer = null

// Flatten all actions with round info for the feed
const allActions = computed(() => {
  const out = []
  for (const r of rounds.value) {
    for (const a of (r.actions || [])) {
      out.push({ ...a, _round: r.round_number })
    }
  }
  return out
})


const latestMetrics = computed(() => {
  if (rounds.value.length === 0) return {}
  return rounds.value[rounds.value.length - 1]?.metrics || {}
})

const computedAggregateMetrics = computed(() => {
  if (!rounds.value.length) return {}
  const lastRound = rounds.value[rounds.value.length - 1]
  const allActions = rounds.value.flatMap(r => r.actions || []).filter(a => a.action_type !== 'no_action')
  return {
    final_sentiment: lastRound?.metrics?.avg_sentiment || 0,
    total_volume: allActions.length,
    sentiment_trajectory: rounds.value.map(r => r.metrics?.avg_sentiment || 0),
  }
})

// Lifecycle
onMounted(async () => {
  loadHistory()
  await checkLlmStatus()
})

async function checkLlmStatus() {
  try {
    const res = await getSettingsStatus()
    llmConfigured.value = !!res.data?.llm_configured
    if (!llmConfigured.value) {
      showSettings.value = true
    }
  } catch (e) {
    // settings table may not exist yet
    llmConfigured.value = false
  }
}

onUnmounted(() => { stopPolling() })

// Actions
async function handleStart({ scenarios, config }) {
  // Block if no LLM configured
  if (!llmConfigured.value) {
    showSettings.value = true
    return
  }

  currentScenario.value = scenarios.join(' + ')
  state.value = 'running'
  errorMsg.value = ''
  resetLiveData()
  totalRounds.value = config.total_rounds || 6

  try {
    const res = await createSimulation(scenarios, config)
    taskId.value = res.task_id
    startPolling()
  } catch (e) {
    state.value = 'error'
    errorMsg.value = e.message || 'Failed to start simulation'
  }
}

async function handleCancel() {
  if (!taskId.value || cancelling.value) return
  cancelling.value = true
  try { await cancelTask(taskId.value) } catch (e) { cancelling.value = false }
}

function resetToIdle() {
  stopPolling()
  state.value = 'idle'
  taskId.value = null
  resultData.value = null
  errorMsg.value = ''
  cancelling.value = false
  currentScenario.value = ''
  resetLiveData()
  loadHistory()
}

function resetLiveData() {
  rounds.value = []
  currentRound.value = 0
  phase.value = ''
  currentAgent.value = ''
  influenceLog.value = []
  agentDefs.value = {}
  agentTimeline.value = []
  scenarioMap.value = {}
  agentScenarioMap.value = {}
}

async function loadSimulation(sim) {
  showHistory.value = false

  // Fetch full simulation data (list only returns summary)
  try {
    const res = await getSimulation(sim.simulation_id)
    const full = res.data
    agentDefs.value = full.agent_states?._agent_defs || {}
    influenceLog.value = full.influence_log || []
    agentTimeline.value = full.agent_states?._agent_timeline || []
    scenarioMap.value = full.agent_states?._scenario_map || {}
    agentScenarioMap.value = full.agent_states?._agent_scenario_map || {}
    rounds.value = full.rounds || []
    currentRound.value = full.total_rounds || 0
    totalRounds.value = full.total_rounds || 6
    currentScenario.value = full.scenario || ''
    phase.value = 'completed'
    resultData.value = {
      aggregate_metrics: full.aggregate_metrics,
      total_rounds: full.total_rounds,
    }
    state.value = 'results'
  } catch (e) {
    // Fallback to summary data if full fetch fails
    agentDefs.value = sim.agent_states?._agent_defs || {}
    rounds.value = sim.rounds || []
    currentRound.value = sim.total_rounds || 0
    totalRounds.value = sim.total_rounds || 6
    currentScenario.value = sim.scenario || ''
    phase.value = 'completed'
    resultData.value = {
      aggregate_metrics: sim.aggregate_metrics,
      total_rounds: sim.total_rounds,
    }
    state.value = 'results'
  }
}

async function loadHistory() {
  try {
    const res = await listSimulations()
    history.value = res.data || []
  } catch (e) { /* ignore */ }
}

async function onSettingsSaved() {
  await checkLlmStatus()
}

// Polling
function startPolling() {
  poll()
  pollTimer = setInterval(poll, 2000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

async function poll() {
  if (!taskId.value) return
  try {
    const res = await getTaskStatus(taskId.value)
    const task = res.data

    if (task.progress_detail) {
      const d = task.progress_detail
      rounds.value = d.rounds || []
      currentRound.value = d.current_round || 0
      totalRounds.value = d.total_rounds || totalRounds.value
      phase.value = d.phase || ''
      currentAgent.value = d.current_agent || ''
      if (d.influence_log) influenceLog.value = d.influence_log
      if (d.agent_defs) agentDefs.value = d.agent_defs
      if (d.agent_timeline) agentTimeline.value = d.agent_timeline
      if (d.scenario_map) scenarioMap.value = d.scenario_map
      if (d.agent_scenario_map) agentScenarioMap.value = d.agent_scenario_map
    }

    if (task.status === 'completed') {
      stopPolling()
      resultData.value = task.result
      if (task.result?.agent_defs) agentDefs.value = task.result.agent_defs
      if (task.result?.influence_log) influenceLog.value = task.result.influence_log
      state.value = 'results'
    } else if (task.status === 'cancelled') {
      stopPolling()
      cancelling.value = false
      if (task.result?.rounds?.length > 0) {
        resultData.value = task.result
        state.value = 'results'
      } else {
        errorMsg.value = 'Simulation cancelled before any rounds completed.'
        state.value = 'error'
      }
    } else if (task.status === 'failed') {
      stopPolling()
      errorMsg.value = task.error || 'Simulation failed'
      state.value = 'error'
    }
  } catch (e) {
    // Stop polling if task not found (404) or server error
    if (e?.response?.status === 404 || e?.message?.includes('404')) {
      stopPolling()
      errorMsg.value = 'Simulation task not found. It may have expired.'
      state.value = 'error'
    }
  }
}
</script>

<style scoped>
.canvas {
  position: fixed;
  inset: 0;
  background: #0a0a0b;
  z-index: 1;
}

.glow-bg {
  position: fixed;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  z-index: 0;
}
.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(128px);
  animation: bpulse 8s ease-in-out infinite;
}
.blob-1 { top: 10%; left: 20%; width: 420px; height: 420px; background: rgba(139,92,246,0.12); }
.blob-2 { bottom: 10%; right: 20%; width: 420px; height: 420px; background: rgba(99,102,241,0.12); animation-delay: 2s; }
.blob-3 { top: 30%; right: 30%; width: 300px; height: 300px; background: rgba(232,121,249,0.08); animation-delay: 4s; }
@keyframes bpulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.15); }
}

.error-card {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 20;
  padding: 32px;
  background: rgba(0,0,0,0.8);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  text-align: center;
  max-width: 400px;
}
.error-card h3 { color: var(--danger); margin-bottom: 8px; font-size: 18px; }
.error-card p { color: var(--text-secondary); margin-bottom: 16px; font-size: 14px; }
.btn-retry {
  padding: 8px 24px;
  background: var(--accent);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.history-panel {
  position: fixed;
  top: 48px;
  right: 8px;
  width: 320px;
  max-height: 400px;
  background: #0a0a0b;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  padding: 4px;
  overflow-y: auto;
  z-index: 110;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}
.history-empty {
  color: var(--text-muted);
  font-size: 12px;
  padding: 24px 10px;
  text-align: center;
}
.history-item {
  padding: 8px 10px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 150ms;
}
.history-item:hover { background: rgba(255,255,255,0.04); }
.history-item + .history-item { border-top: 1px solid rgba(255,255,255,0.03); }
.hist-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}
.hist-scenario {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255,255,255,0.7);
  line-height: 1.4;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.hist-sentiment {
  font-size: 11px;
  font-weight: 500;
  flex-shrink: 0;
  letter-spacing: -0.01em;
}
.hist-meta {
  font-size: 10px;
  color: rgba(255,255,255,0.2);
  margin-top: 2px;
}
</style>
