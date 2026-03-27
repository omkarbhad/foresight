<template>
  <div class="sim-results">
    <h2>Simulation Complete</h2>

    <div class="metrics-row">
      <div class="metric-box">
        <span class="metric-label">Final Sentiment</span>
        <span class="metric-value" :class="sentimentClass(agg.final_sentiment)">
          {{ (agg.final_sentiment || 0).toFixed(2) }}
        </span>
      </div>
      <div class="metric-box">
        <span class="metric-label">Total Volume</span>
        <span class="metric-value">{{ agg.total_volume || 0 }}</span>
      </div>
      <div class="metric-box">
        <span class="metric-label">Rounds</span>
        <span class="metric-value">{{ totalRounds }}</span>
      </div>
      <div class="metric-box">
        <span class="metric-label">Agents</span>
        <span class="metric-value">{{ Object.keys(agentDefs).length }}</span>
      </div>
    </div>

    <!-- Per-Scenario Breakdown (multi-scenario only) -->
    <div v-if="hasMultipleScenarios && Object.keys(perScenarioSummary).length" class="section scenario-breakdown">
      <h3>Per-Scenario Breakdown</h3>
      <div class="scenario-cards">
        <div v-for="(metrics, scenario) in perScenarioSummary" :key="scenario"
             class="scenario-card" :style="{ borderLeftColor: getScenarioColor(scenario) }">
          <h4>{{ scenario }}</h4>
          <div class="scenario-metrics">
            <span>Sentiment: <b :class="sentimentClass(metrics.final_sentiment)">{{ (metrics.final_sentiment || 0).toFixed(2) }}</b></span>
            <span>Volume: <b>{{ metrics.total_volume || 0 }}</b></span>
          </div>
          <p v-if="metrics.key_dynamics" class="scenario-dynamics">{{ metrics.key_dynamics }}</p>
        </div>
      </div>
    </div>

    <div class="trajectories" v-if="agg.sentiment_trajectory?.length">
      <div class="trajectory trajectory-full">
        <h3>Sentiment Trajectory</h3>
        <div class="sparkline">
          <svg :viewBox="`0 0 ${sparkWidth} 60`" preserveAspectRatio="none">
            <line x1="0" :y1="30" :x2="sparkWidth" :y2="30" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="4"/>
            <polyline :points="sentimentPoints" fill="none" stroke="#2563eb" stroke-width="2" stroke-linejoin="round"/>
            <circle v-for="(pt, i) in sentimentPointsArray" :key="i" :cx="pt.x" :cy="pt.y" r="3" fill="#2563eb"/>
          </svg>
          <div class="spark-labels">
            <span v-for="i in agg.sentiment_trajectory.length" :key="i">R{{ i }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Influence Network Graph -->
    <div v-if="Object.keys(agentDefs).length > 1" class="section influence-section">
      <LiveInfluenceGraph
        :agentDefs="agentDefs"
        :influenceLog="influenceLog"
        :agentTimeline="agentTimeline"
        :currentRound="totalRounds"
        :scenarioMap="scenarioMap"
        :agentScenarioMap="agentScenarioMap"
        title="Influence Network"
      />
    </div>

    <!-- Cross-Scenario Dynamics (multi-scenario only) -->
    <div v-if="crossScenarioDynamics" class="section cross-dynamics">
      <h3>Cross-Scenario Interaction Effects</h3>
      <div class="cross-narrative" v-html="formatNarrative(crossScenarioDynamics)"></div>
      <div v-if="interactionEffects?.length" class="effects-list">
        <div v-for="(effect, i) in interactionEffects" :key="i" class="effect-chip">{{ effect }}</div>
      </div>
    </div>

    <div v-if="influenceChains.length" class="section">
      <h3>Influence Chain Summary</h3>
      <div class="influence-chains">
        <div v-for="(chain, i) in influenceChains" :key="i" class="chain-item" :class="{ 'cross-chain': chain.crossScenario }">
          <span class="chain-from">{{ chain.from }}</span>
          <span class="chain-arrow">&rarr;</span>
          <span class="chain-to">{{ chain.to }}</span>
          <span class="chain-count">({{ chain.count }}x)</span>
          <span v-if="chain.crossScenario" class="cross-badge">cross</span>
        </div>
      </div>
    </div>

    <div v-if="agg.key_turning_points?.length" class="section">
      <h3>Key Turning Points</h3>
      <ol class="turning-points">
        <li v-for="(tp, i) in agg.key_turning_points" :key="i">{{ tp }}</li>
      </ol>
    </div>

    <div v-if="agg.recommended_actions?.length" class="section">
      <h3>Recommended Actions</h3>
      <ol class="actions-list">
        <li v-for="(a, i) in agg.recommended_actions" :key="i">{{ a }}</li>
      </ol>
    </div>

    <div v-if="agg.narrative_summary" class="section narrative">
      <h3>Executive Summary</h3>
      <div class="narrative-text" v-html="formatNarrative(agg.narrative_summary)"></div>
    </div>

    <div v-if="agentArcs.length" class="section">
      <h3>Agent Sentiment Arcs</h3>
      <div class="arcs-grid">
        <div v-for="arc in agentArcs" :key="arc.agent" class="arc-item">
          <span class="arc-label">{{ arc.label }}</span>
          <svg viewBox="0 0 120 30" class="arc-spark" preserveAspectRatio="none">
            <line x1="0" y1="15" x2="120" y2="15" stroke="#e2e8f0" stroke-width="0.5" stroke-dasharray="2"/>
            <polyline :points="arc.points" fill="none" :stroke="arc.color" stroke-width="1.5" stroke-linejoin="round"/>
          </svg>
        </div>
      </div>
    </div>

    <button class="btn-secondary" @click="$emit('reset')">Run Another Simulation</button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import LiveInfluenceGraph from './LiveInfluenceGraph.vue'

const SCENARIO_COLORS = [
  '#2563eb', '#dc2626', '#059669', '#7c3aed', '#ea580c',
  '#0891b2', '#db2777', '#65a30d',
]

const props = defineProps({
  aggregateMetrics: { type: Object, default: () => ({}) },
  totalRounds: { type: Number, default: 6 },
  influenceLog: { type: Array, default: () => [] },
  rounds: { type: Array, default: () => [] },
  agentDefs: { type: Object, default: () => ({}) },
  agentTimeline: { type: Array, default: () => [] },
  scenarioMap: { type: Object, default: () => ({}) },
  agentScenarioMap: { type: Object, default: () => ({}) },
})
defineEmits(['reset'])

const agg = computed(() => props.aggregateMetrics || {})
const sparkWidth = computed(() => Math.max((agg.value.sentiment_trajectory?.length || 1) * 40, 120))

const hasMultipleScenarios = computed(() => Object.keys(props.scenarioMap).length > 1)
const perScenarioSummary = computed(() => agg.value.per_scenario_summary || {})
const crossScenarioDynamics = computed(() => agg.value.cross_scenario_dynamics || '')
const interactionEffects = computed(() => agg.value.interaction_effects || [])

function sentimentClass(v) {
  if (v > 0.2) return 'positive'
  if (v < -0.2) return 'negative'
  return 'neutral'
}

function getScenarioColor(scenario) {
  const entries = Object.entries(props.scenarioMap)
  const idx = entries.findIndex(([_, name]) => name === scenario)
  return SCENARIO_COLORS[(idx >= 0 ? idx : 0) % SCENARIO_COLORS.length]
}

function toPoints(data, minVal, maxVal) {
  if (!data?.length) return { str: '', arr: [] }
  const w = sparkWidth.value
  const step = w / Math.max(data.length - 1, 1)
  const arr = data.map((v, i) => ({
    x: i * step,
    y: 60 - ((v - minVal) / (maxVal - minVal)) * 55 - 2.5,
  }))
  return { str: arr.map(p => `${p.x},${p.y}`).join(' '), arr }
}

const sentimentPoints = computed(() => toPoints(agg.value.sentiment_trajectory, -1, 1).str)
const sentimentPointsArray = computed(() => toPoints(agg.value.sentiment_trajectory, -1, 1).arr)

function formatNarrative(text) {
  return (text || '').replace(/\n/g, '<br>')
}

function getLabel(key) {
  return props.agentDefs?.[key]?.name || key?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || key
}
function getColor(key) {
  return props.agentDefs?.[key]?.color || '#6b7280'
}

const influenceChains = computed(() => {
  const counts = {}
  for (const entry of (props.influenceLog || [])) {
    const key = `${entry.from}\u2192${entry.to}`
    if (!counts[key]) {
      const fromSc = entry.from_scenario || props.agentScenarioMap?.[entry.from] || ''
      const toSc = entry.to_scenario || props.agentScenarioMap?.[entry.to] || ''
      counts[key] = { count: 0, crossScenario: fromSc && toSc && fromSc !== toSc }
    }
    counts[key].count++
  }
  return Object.entries(counts)
    .map(([key, data]) => {
      const [from, to] = key.split('\u2192')
      return { from: getLabel(from), to: getLabel(to), count: data.count, crossScenario: data.crossScenario }
    })
    .sort((a, b) => b.count - a.count)
    .slice(0, 12)
})

const agentArcs = computed(() => {
  if (!props.rounds?.length) return []
  const agents = new Set()
  for (const r of props.rounds) {
    for (const a of (r.actions || [])) {
      if (a.persona) agents.add(a.persona)
    }
  }
  return Array.from(agents).map(agent => {
    const sentiments = props.rounds.map(r => {
      const action = (r.actions || []).find(a => a.persona === agent)
      return action ? (action.sentiment_score || 0) : 0
    })
    const step = 120 / Math.max(sentiments.length - 1, 1)
    const points = sentiments.map((s, i) => `${i * step},${15 - s * 13}`).join(' ')
    return {
      agent,
      label: getLabel(agent),
      color: getColor(agent),
      points,
    }
  })
})
</script>

<style scoped>
.sim-results {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 24px; margin-top: 24px;
}
h2 { font-size: 20px; font-weight: 700; margin-bottom: 20px; }
h3 { font-size: 15px; font-weight: 600; margin-bottom: 12px; }
.metrics-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 24px; }
.metric-box {
  padding: 16px; background: #f8fafc; border-radius: 10px; border: 1px solid var(--border);
  text-align: center;
}
.metric-label { display: block; font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; text-transform: uppercase; }
.metric-value { display: block; font-size: 24px; font-weight: 800; }
.metric-value.positive { color: #10b981; }
.metric-value.negative { color: #ef4444; }
.metric-value.neutral { color: #6b7280; }

/* Per-Scenario Breakdown */
.scenario-breakdown { margin-bottom: 24px; }
.scenario-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }
.scenario-card {
  padding: 16px; background: #f8fafc; border: 1px solid var(--border); border-radius: 10px;
  border-left: 4px solid #2563eb;
}
.scenario-card h4 { font-size: 14px; font-weight: 600; margin: 0 0 8px 0; }
.scenario-metrics { display: flex; gap: 16px; font-size: 13px; color: var(--text-secondary); }
.scenario-metrics b { font-weight: 700; }
.scenario-metrics b.positive { color: #10b981; }
.scenario-metrics b.negative { color: #ef4444; }
.scenario-metrics b.neutral { color: #6b7280; }
.scenario-dynamics { font-size: 13px; line-height: 1.6; color: var(--text); margin-top: 8px; }

/* Cross-Scenario Dynamics */
.cross-dynamics {
  padding: 20px; background: #fef3c7; border: 1px solid #fde68a; border-radius: 10px;
  margin-bottom: 20px;
}
.cross-narrative { font-size: 14px; line-height: 1.7; color: var(--text); }
.effects-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.effect-chip {
  padding: 4px 12px; background: #fff; border: 1px solid #fbbf24; border-radius: 6px;
  font-size: 12px; color: #92400e;
}

.trajectories { margin-bottom: 24px; }
.trajectory { padding: 16px; background: #f8fafc; border-radius: 10px; border: 1px solid var(--border); }
.trajectory-full { width: 100%; }
.sparkline svg { width: 100%; height: 60px; }
.spark-labels { display: flex; justify-content: space-between; font-size: 10px; color: var(--text-secondary); margin-top: 4px; }

.section { margin-bottom: 20px; }
.influence-section {
  background: #f8fafc; border: 1px solid var(--border); border-radius: 12px;
  padding: 16px; margin-bottom: 24px;
}
.turning-points, .actions-list { padding-left: 20px; font-size: 14px; line-height: 1.8; }
.narrative {
  padding: 20px; background: #fffbeb; border: 1px solid #fde68a; border-radius: 10px;
}
.narrative-text { font-size: 14px; line-height: 1.7; color: var(--text); }

.btn-secondary {
  padding: 10px 24px; background: var(--surface); color: var(--primary);
  border: 2px solid var(--primary); border-radius: 8px; font-size: 14px;
  font-weight: 600; margin-top: 8px; cursor: pointer;
}
.btn-secondary:hover { background: #eff6ff; }

.influence-chains { display: flex; flex-wrap: wrap; gap: 8px; }
.chain-item {
  display: flex; align-items: center; gap: 4px; padding: 4px 10px;
  background: #f8fafc; border: 1px solid var(--border); border-radius: 6px; font-size: 13px;
}
.chain-item.cross-chain { border-color: #fbbf24; background: #fffbeb; }
.chain-from { font-weight: 600; }
.chain-arrow { color: var(--text-secondary); }
.chain-to { font-weight: 600; }
.chain-count { color: var(--text-secondary); font-size: 11px; }
.cross-badge {
  font-size: 10px; padding: 1px 5px; border-radius: 3px;
  background: #fef3c7; color: #92400e; font-weight: 600; text-transform: uppercase;
}

.arcs-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
.arc-item {
  padding: 8px 12px; background: #f8fafc; border: 1px solid var(--border); border-radius: 8px;
  display: flex; flex-direction: column; gap: 4px;
}
.arc-label { font-size: 12px; font-weight: 600; }
.arc-spark { width: 100%; height: 30px; }
</style>
