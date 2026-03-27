<template>
  <AppLayout>
    <div class="simulation-page">
      <div class="page-header">
        <h1>Scenario Simulation</h1>
        <p class="subtitle">AI-powered multi-agent scenario simulation with dynamic agents and influence chains</p>
      </div>

      <!-- State: idle — show form -->
      <SimulationForm v-if="state === 'idle'" @submit="handleStart" />

      <!-- State: running — show timeline -->
      <template v-if="state === 'running'">
        <SimulationTimeline :taskId="taskId" @complete="handleComplete" @failed="handleFailed" @cancelled="handleCancelled" />
      </template>

      <!-- State: results — show results -->
      <template v-if="state === 'results'">
        <SimulationResults
          :aggregateMetrics="resultData?.aggregate_metrics"
          :totalRounds="resultData?.total_rounds || 6"
          :influenceLog="resultData?.influence_log || []"
          :rounds="resultData?.rounds || []"
          :agentDefs="resultData?.agent_defs || {}"
          :agentTimeline="resultData?.agent_timeline || []"
          :scenarioMap="resultData?.scenario_map || {}"
          :agentScenarioMap="resultData?.agent_scenario_map || {}"
          @reset="resetToForm"
        />
        <!-- Also show the timeline below results for reference -->
        <div class="past-timeline" v-if="resultData?.rounds?.length">
          <h3>Round-by-Round Detail</h3>
          <div v-for="round in resultData.rounds" :key="round.round_number" class="past-round">
            <div class="past-round-header">
              <span class="round-badge">R{{ round.round_number }}</span>
              <span class="round-time">{{ round.time_label }}</span>
              <span class="round-sentiment" :class="sentimentClass(round.metrics?.avg_sentiment)">
                Sentiment: {{ round.metrics?.avg_sentiment?.toFixed(2) }}
              </span>
            </div>
            <div class="past-actions">
              <PersonaCard v-for="(action, i) in round.actions" :key="i" :action="action" :agentDefs="resultData?.agent_defs || {}" :showScenario="hasMultipleScenarios" />
            </div>
          </div>
        </div>
      </template>

      <!-- State: error -->
      <div v-if="state === 'error'" class="error-state">
        <h3>Simulation Failed</h3>
        <p>{{ errorMsg }}</p>
        <button class="btn-primary" @click="resetToForm">Try Again</button>
      </div>

      <!-- Past simulations -->
      <div v-if="state === 'idle' && history.length > 0" class="history-section">
        <h3>Recent Simulations</h3>
        <div class="history-list">
          <div v-for="sim in history" :key="sim.simulation_id" class="history-card" @click="loadSimulation(sim)">
            <span class="history-scenario">{{ sim.scenario.slice(0, 100) }}{{ sim.scenario.length > 100 ? '...' : '' }}</span>
            <div class="history-meta">
              <span>{{ sim.total_rounds }} rounds</span>
              <span>Sentiment: {{ sim.aggregate_metrics?.final_sentiment?.toFixed(2) }}</span>
              <span>{{ sim.created_at?.slice(0, 16) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import SimulationForm from '../components/simulation/SimulationForm.vue'
import SimulationTimeline from '../components/simulation/SimulationTimeline.vue'
import SimulationResults from '../components/simulation/SimulationResults.vue'
import PersonaCard from '../components/simulation/PersonaCard.vue'
import { createSimulation, listSimulations } from '../api/simulation'

const state = ref('idle') // idle | running | results | error
const taskId = ref(null)
const resultData = ref(null)
const errorMsg = ref('')
const history = ref([])

const hasMultipleScenarios = computed(() => Object.keys(resultData.value?.scenario_map || {}).length > 1)

onMounted(() => {
  loadHistory()
})

async function loadHistory() {
  try {
    const res = await listSimulations()
    history.value = res.data || []
  } catch (e) {}
}

async function handleStart({ scenarios, config }) {
  state.value = 'running'
  errorMsg.value = ''
  try {
    const res = await createSimulation(scenarios, config)
    taskId.value = res.task_id
  } catch (e) {
    state.value = 'error'
    errorMsg.value = e.message || 'Failed to start simulation'
  }
}

function handleComplete(result) {
  resultData.value = result
  state.value = 'results'
}

function handleCancelled(result) {
  if (result && result.rounds && result.rounds.length > 0) {
    resultData.value = result
    state.value = 'results'
  } else {
    errorMsg.value = 'Simulation was cancelled before any rounds completed.'
    state.value = 'error'
  }
}

function handleFailed(error) {
  errorMsg.value = error || 'Simulation failed'
  state.value = 'error'
}

function resetToForm() {
  state.value = 'idle'
  taskId.value = null
  resultData.value = null
  errorMsg.value = ''
  loadHistory()
}

function loadSimulation(sim) {
  resultData.value = {
    simulation_id: sim.simulation_id,
    total_rounds: sim.total_rounds,
    rounds: sim.rounds,
    aggregate_metrics: sim.aggregate_metrics,
    influence_log: sim.influence_log || [],
    agent_defs: sim.agent_states?._agent_defs || {},
    agent_timeline: sim.agent_states?._agent_timeline || [],
    scenario_map: sim.agent_states?._scenario_map || {},
    agent_scenario_map: sim.agent_states?._agent_scenario_map || {},
  }
  state.value = 'results'
}

function sentimentClass(v) {
  if (v > 0.2) return 'positive'
  if (v < -0.2) return 'negative'
  return 'neutral'
}
</script>

<style scoped>
.simulation-page { max-width: 1100px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }

.error-state {
  text-align: center; padding: 40px; background: #fef2f2; border: 1px solid #fecaca;
  border-radius: 12px; margin-top: 24px;
}
.error-state h3 { color: var(--danger); margin-bottom: 8px; }
.error-state p { color: var(--text-secondary); margin-bottom: 16px; }
.btn-primary {
  padding: 10px 24px; background: var(--primary); color: white;
  border: none; border-radius: 8px; font-weight: 600; cursor: pointer;
}

.past-timeline {
  margin-top: 24px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; padding: 20px;
}
.past-timeline h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
.past-round { margin-bottom: 16px; }
.past-round-header {
  display: flex; align-items: center; gap: 12px; margin-bottom: 10px;
}
.round-badge {
  font-size: 14px; font-weight: 800; color: var(--primary);
  background: #eff6ff; padding: 4px 10px; border-radius: 8px;
}
.round-time { font-size: 13px; color: var(--text-secondary); }
.round-sentiment { font-size: 13px; font-weight: 600; margin-left: auto; }
.round-sentiment.positive { color: #10b981; }
.round-sentiment.negative { color: #ef4444; }
.round-sentiment.neutral { color: #6b7280; }
.past-actions { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 4px; }

.history-section { margin-top: 32px; }
.history-section h3 { font-size: 16px; font-weight: 600; margin-bottom: 12px; }
.history-list { display: flex; flex-direction: column; gap: 8px; }
.history-card {
  padding: 14px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 10px; cursor: pointer; transition: border-color 0.15s;
}
.history-card:hover { border-color: var(--primary); }
.history-scenario { font-size: 14px; font-weight: 500; display: block; margin-bottom: 6px; }
.history-meta { display: flex; gap: 16px; font-size: 12px; color: var(--text-secondary); }
</style>
