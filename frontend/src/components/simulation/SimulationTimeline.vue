<template>
  <div class="sim-timeline">
    <div class="progress-header">
      <div class="progress-info">
        <span class="progress-label">
          Round {{ currentRound }} of {{ totalRounds }}
          <template v-if="currentTimeLabel"> — {{ currentTimeLabel }}</template>
        </span>
        <div class="progress-actions">
          <button
            v-if="status === 'processing' && !cancelling"
            class="btn-stop"
            @click="handleCancel"
          >Stop Simulation</button>
          <span v-if="cancelling" class="cancel-pending">Stopping...</span>
          <span class="progress-status" :class="status">{{ statusText }}</span>
        </div>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPct + '%' }"></div>
      </div>
    </div>

    <LiveInfluenceGraph
      v-if="Object.keys(agentDefs).length > 0"
      :agentDefs="agentDefs"
      :influenceLog="influenceLog"
      :agentTimeline="agentTimeline"
      :currentRound="currentRound"
      :scenarioMap="scenarioMap"
      :agentScenarioMap="agentScenarioMap"
      title="Live Influence Network"
    />

    <div class="rounds-container">
      <template v-for="round in rounds" :key="round.round_number">
        <div class="round-row" :class="{ latest: round.round_number === currentRound }">
          <div class="round-label">
            <span class="round-num">R{{ round.round_number }}</span>
            <span class="round-time">{{ round.time_label }}</span>
          </div>
          <div class="round-actions">
            <PersonaCard v-for="(action, i) in round.actions" :key="i" :action="action" :agentDefs="agentDefs" :showScenario="hasMultipleScenarios" />
          </div>
          <RoundMetrics :metrics="round.metrics" />
        </div>

        <div v-if="newAgentsForRound(round.round_number).length" class="agent-discovery">
          <span class="discovery-icon">+</span>
          <span class="discovery-text">
            New agents discovered:
            <span v-for="(agent, i) in newAgentsForRound(round.round_number)" :key="agent"
                  class="discovery-agent" :style="{ borderColor: agentDefs[agent]?.color || '#6b7280' }">
              {{ agentDefs[agent]?.name || agent }}{{ i < newAgentsForRound(round.round_number).length - 1 ? '' : '' }}
            </span>
          </span>
        </div>
      </template>

      <div v-if="status === 'processing'" class="loading-round">
        <div class="pulse"></div>
        <span>
          <template v-if="phase === 'planning_agents'">Analyzing scenario and selecting agents...</template>
          <template v-else-if="phase === 'ingesting_data'">Fetching fresh media data...</template>
          <template v-else-if="phase === 'graph_init'">Initializing knowledge graph...</template>
          <template v-else-if="phase === 'loading_history'">Loading historical data...</template>
          <template v-else-if="phase === 'creating_agents'">Creating simulation agents...</template>
          <template v-else-if="phase === 'generating_summary'">Generating final analysis...</template>
          <template v-else-if="phase === 'discovering_agents'">Analyzing outputs for emerging entities...</template>
          <template v-else-if="phase === 'fetching_entity_data'">Fetching real-world data for new entities...</template>
          <template v-else-if="phase === 'expanding_agents'">Generating new agent personas...</template>
          <template v-else-if="currentAgent">Agent: {{ agentLabel }} responding...</template>
          <template v-else>Simulating next round...</template>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import PersonaCard from './PersonaCard.vue'
import RoundMetrics from './RoundMetrics.vue'
import LiveInfluenceGraph from './LiveInfluenceGraph.vue'
import { getTaskStatus, cancelTask } from '../../api/simulation'

const props = defineProps({ taskId: String })
const emit = defineEmits(['complete', 'failed', 'cancelled'])

const rounds = ref([])
const currentRound = ref(0)
const totalRounds = ref(6)
const status = ref('processing')
const message = ref('')
const result = ref(null)
const phase = ref('')
const currentAgent = ref('')
const influenceLog = ref([])
const agentDefs = ref({})
const agentTimeline = ref([])
const scenarioMap = ref({})
const agentScenarioMap = ref({})
const cancelling = ref(false)
let pollTimer = null

const hasMultipleScenarios = computed(() => Object.keys(scenarioMap.value).length > 1)

const agentLabel = computed(() => agentDefs.value[currentAgent.value]?.name || currentAgent.value?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || '')

const progressPct = computed(() => {
  if (totalRounds.value === 0) return 0
  return Math.round((currentRound.value / (totalRounds.value + 1)) * 100)
})

const currentTimeLabel = computed(() => {
  if (rounds.value.length === 0) return ''
  return rounds.value[rounds.value.length - 1]?.time_label || ''
})

const statusText = computed(() => {
  if (status.value === 'completed') return 'Complete'
  if (status.value === 'cancelled') return 'Cancelled'
  if (status.value === 'failed') return 'Failed'
  return message.value || 'Running...'
})

function newAgentsForRound(roundNumber) {
  const entry = agentTimeline.value.find(t => t.round === roundNumber)
  return entry?.agents || []
}

async function poll() {
  if (!props.taskId) return
  try {
    const res = await getTaskStatus(props.taskId)
    const task = res.data
    status.value = task.status
    message.value = task.message

    if (task.progress_detail) {
      rounds.value = task.progress_detail.rounds || []
      currentRound.value = task.progress_detail.current_round || 0
      totalRounds.value = task.progress_detail.total_rounds || 6
      phase.value = task.progress_detail.phase || ''
      currentAgent.value = task.progress_detail.current_agent || ''
      influenceLog.value = task.progress_detail.influence_log || influenceLog.value
      agentDefs.value = task.progress_detail.agent_defs || agentDefs.value
      agentTimeline.value = task.progress_detail.agent_timeline || agentTimeline.value
      if (task.progress_detail.scenario_map) scenarioMap.value = task.progress_detail.scenario_map
      if (task.progress_detail.agent_scenario_map) agentScenarioMap.value = task.progress_detail.agent_scenario_map
    }

    if (task.status === 'completed') {
      stopPolling()
      result.value = task.result
      emit('complete', task.result)
    } else if (task.status === 'cancelled') {
      stopPolling()
      result.value = task.result
      emit('cancelled', task.result)
    } else if (task.status === 'failed') {
      stopPolling()
      emit('failed', task.error)
    }
  } catch (e) {
    console.error('Poll error:', e)
  }
}

async function handleCancel() {
  if (!props.taskId || cancelling.value) return
  cancelling.value = true
  try {
    await cancelTask(props.taskId)
  } catch (e) {
    console.error('Cancel failed:', e)
    cancelling.value = false
  }
}

function startPolling() {
  poll()
  pollTimer = setInterval(poll, 2000)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(startPolling)
onUnmounted(stopPolling)

watch(() => props.taskId, () => {
  stopPolling()
  rounds.value = []
  currentRound.value = 0
  status.value = 'processing'
  agentTimeline.value = []
  cancelling.value = false
  startPolling()
})
</script>

<style scoped>
.sim-timeline { margin-top: 24px; }
.progress-header {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 16px; margin-bottom: 20px;
}
.progress-info { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.progress-label { font-size: 15px; font-weight: 600; }
.progress-status {
  font-size: 13px; font-weight: 600; padding: 4px 12px; border-radius: 8px;
}
.progress-actions { display: flex; align-items: center; gap: 10px; }
.btn-stop {
  padding: 4px 14px; font-size: 12px; font-weight: 600;
  background: #fee2e2; color: #dc2626; border: 1px solid #fca5a5;
  border-radius: 6px; cursor: pointer; transition: all 0.15s;
}
.btn-stop:hover { background: #fca5a5; color: #991b1b; }
.cancel-pending { font-size: 12px; color: #dc2626; font-weight: 500; }
.progress-status.processing { background: #dbeafe; color: #2563eb; }
.progress-status.completed { background: #d1fae5; color: #059669; }
.progress-status.cancelled { background: #fef3c7; color: #d97706; }
.progress-status.failed { background: #fee2e2; color: #dc2626; }
.progress-bar { height: 6px; background: #e2e8f0; border-radius: 3px; overflow: hidden; }
.progress-fill {
  height: 100%; background: var(--primary); border-radius: 3px;
  transition: width 0.5s ease;
}

.rounds-container { display: flex; flex-direction: column; gap: 16px; margin-top: 20px; }
.round-row {
  display: flex; gap: 16px; align-items: flex-start;
  padding: 16px; background: var(--surface); border: 1px solid var(--border);
  border-radius: 12px; animation: fadeIn 0.4s ease;
}
.round-row.latest { border-color: var(--primary); box-shadow: 0 0 0 1px var(--primary); }
.round-label {
  display: flex; flex-direction: column; align-items: center; min-width: 80px; gap: 4px;
}
.round-num {
  font-size: 18px; font-weight: 800; color: var(--primary);
  background: #eff6ff; width: 40px; height: 40px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.round-time { font-size: 11px; color: var(--text-secondary); text-align: center; line-height: 1.3; }
.round-actions {
  display: flex; gap: 10px; flex: 1; overflow-x: auto; padding-bottom: 4px;
}

.agent-discovery {
  display: flex; align-items: center; gap: 10px; padding: 10px 16px;
  background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 10px;
  animation: fadeIn 0.5s ease;
}
.discovery-icon {
  width: 24px; height: 24px; background: #22c55e; color: white;
  border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 14px; font-weight: 800; flex-shrink: 0;
}
.discovery-text {
  font-size: 13px; color: #166534; display: flex; align-items: center;
  gap: 6px; flex-wrap: wrap;
}
.discovery-agent {
  font-weight: 600; padding: 2px 8px; background: white;
  border: 2px solid; border-radius: 6px; font-size: 12px;
}

.loading-round {
  display: flex; align-items: center; gap: 12px; padding: 20px;
  justify-content: center; color: var(--text-secondary); font-size: 14px;
}
.pulse {
  width: 12px; height: 12px; background: var(--primary); border-radius: 50%;
  animation: pulse 1.2s infinite;
}

@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.5; transform: scale(1.3); } }
</style>
