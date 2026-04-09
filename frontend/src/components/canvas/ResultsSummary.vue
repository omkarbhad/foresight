<template>
  <div v-if="visible" class="results-container" :class="view">

    <!-- SIDEBAR VIEW -->
    <div v-if="view === 'sidebar'" class="sidebar" :style="{ width: sidebarWidth + 'px' }">
      <div class="resize-handle" @mousedown="startResize"></div>
      <div class="panel-header">
        <span class="panel-title">Results</span>
        <div class="header-actions">
          <button class="icon-btn" @click="$emit('toggle-view')" title="Expand to full page">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M8 3H5a2 2 0 00-2 2v3m18 0V5a2 2 0 00-2-2h-3m0 18h3a2 2 0 002-2v-3M3 16v3a2 2 0 002 2h3"/></svg>
          </button>
          <button class="icon-btn" @click="exportResults" title="Export JSON">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4m4-5l5 5 5-5m-5 5V3"/></svg>
          </button>
        </div>
      </div>

      <!-- Stat row -->
      <div class="stat-row">
        <div class="stat" :class="sentimentClass(agg.final_sentiment)">
          <span class="stat-val">{{ (agg.final_sentiment || 0) >= 0 ? '+' : '' }}{{ (agg.final_sentiment || 0).toFixed(2) }}</span>
          <span class="stat-label">sentiment</span>
        </div>
        <div class="stat">
          <span class="stat-val">{{ agg.total_volume || 0 }}</span>
          <span class="stat-label">actions</span>
        </div>
        <div class="stat">
          <span class="stat-val">{{ Object.keys(agentDefs).length }}</span>
          <span class="stat-label">agents</span>
        </div>
        <div class="stat">
          <span class="stat-val">{{ totalRounds }}</span>
          <span class="stat-label">rounds</span>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tab-row">
        <button v-for="tab in tabs" :key="tab.key" class="tab" :class="{ active: activeTab === tab.key }" @click="activeTab = tab.key">
          {{ tab.label }}
        </button>
      </div>

      <div class="sidebar-scroll">

        <!-- TAB: Points (Key Findings + Recommended Actions) -->
        <template v-if="activeTab === 'points'">
          <div v-if="summaryPoints.length" class="section">
            <ul class="point-list">
              <li v-for="(p, i) in summaryPoints" :key="i" class="pt">
                <span class="pt-dot" :class="p.type"></span>
                <span class="pt-text">{{ p.text }}</span>
              </li>
            </ul>
          </div>
          <div v-if="agg.recommended_actions?.length" class="section">
            <h4 class="sec-title">Recommended Actions</h4>
            <ul class="point-list">
              <li v-for="(a, i) in agg.recommended_actions" :key="i" class="pt">
                <span class="pt-num">{{ i + 1 }}</span>
                <span class="pt-text">{{ a }}</span>
              </li>
            </ul>
          </div>
        </template>

        <!-- TAB: Chains (per-round timeline) -->
        <template v-if="activeTab === 'chains'">
          <div class="round-timeline">
            <div v-for="round in roundSummaries" :key="round.num" class="rt-row">
              <div class="rt-rail">
                <span class="rt-dot" :class="sentimentClass(round.sentiment)"></span>
                <span v-if="round.num < totalRounds" class="rt-line"></span>
              </div>
              <div class="rt-body">
                <div class="rt-head">
                  <span class="rt-round">Round {{ round.num }}</span>
                  <span class="rt-time">{{ round.timeLabel }}</span>
                  <span class="rt-sentiment pill sm" :class="sentimentClass(round.sentiment)">{{ round.sentiment >= 0 ? '+' : '' }}{{ round.sentiment.toFixed(2) }}</span>
                </div>
                <p v-if="round.headline" class="rt-headline">{{ round.headline }}</p>
                <div class="rt-agents">
                  <span v-for="agent in round.topAgents" :key="agent.key" class="rt-agent">
                    <span class="rt-agent-dot" :style="{ background: agent.color }"></span>
                    {{ agent.name }}
                  </span>
                  <span v-if="round.moreCount > 0" class="rt-more">+{{ round.moreCount }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- TAB: Timeline (turning points) -->
        <template v-if="activeTab === 'timeline'">
          <div v-if="parsedTurningPoints.length" class="section">
            <ul class="point-list">
              <li v-for="(tp, i) in parsedTurningPoints" :key="i" class="pt">
                <span class="pt-dot timeline"></span>
                <div>
                  <span v-if="tp.label" class="tp-label">{{ tp.label }}</span>
                  <span class="pt-text">{{ tp.text }}</span>
                </div>
              </li>
            </ul>
          </div>
          <div v-else class="empty-state">No turning points detected</div>
        </template>
      </div>
    </div>

    <!-- FULL PAGE VIEW -->
    <div v-if="view === 'fullpage'" class="fullpage">
      <div class="fp-header">
        <div class="fp-metrics">
          <div class="fp-metric" :class="sentimentClass(agg.final_sentiment)">
            <span class="fp-val">{{ (agg.final_sentiment || 0) >= 0 ? '+' : '' }}{{ (agg.final_sentiment || 0).toFixed(2) }}</span>
            <span class="fp-label">sentiment</span>
          </div>
          <div class="fp-metric">
            <span class="fp-val">{{ agg.total_volume || 0 }}</span>
            <span class="fp-label">actions</span>
          </div>
          <div class="fp-metric">
            <span class="fp-val">{{ totalRounds }}</span>
            <span class="fp-label">rounds</span>
          </div>
          <div class="fp-metric">
            <span class="fp-val">{{ Object.keys(agentDefs).length }}</span>
            <span class="fp-label">agents</span>
          </div>
          <div v-if="agg.sentiment_trajectory?.length" class="fp-spark">
            <svg :viewBox="`0 0 ${sparkW} 24`" preserveAspectRatio="none" class="spark-svg">
              <polyline :points="sparkPointsLg" fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-linejoin="round"/>
              <circle v-for="(pt, i) in sparkArrLg" :key="i" :cx="pt.x" :cy="pt.y" r="2" fill="var(--accent)"/>
            </svg>
          </div>
        </div>
        <div class="fp-actions">
          <button class="icon-btn" @click="$emit('toggle-view')" title="Collapse to sidebar">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 14h6v6m10-10h-6V4m0 6L20 4M4 20l6-6"/></svg>
          </button>
          <button class="icon-btn" @click="exportResults" title="Export">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4m4-5l5 5 5-5m-5 5V3"/></svg>
          </button>
        </div>
      </div>
      <div class="fp-body">
        <!-- Left: points + actions -->
        <div class="fp-left">
          <div v-if="summaryPoints.length" class="section">
            <h4 class="sec-title">Key Points</h4>
            <ul class="point-list">
              <li v-for="(p, i) in summaryPoints" :key="i" class="pt">
                <span class="pt-dot" :class="p.type"></span>
                <span class="pt-text">{{ p.text }}</span>
              </li>
            </ul>
          </div>
          <div v-if="parsedTurningPoints.length" class="section">
            <h4 class="sec-title">Turning Points</h4>
            <ul class="point-list">
              <li v-for="(tp, i) in parsedTurningPoints" :key="i" class="pt">
                <span class="pt-dot timeline"></span>
                <div>
                  <span v-if="tp.label" class="tp-label">{{ tp.label }}</span>
                  <span class="pt-text">{{ tp.text }}</span>
                </div>
              </li>
            </ul>
          </div>
          <div v-if="agg.recommended_actions?.length" class="section">
            <h4 class="sec-title">Recommended Actions</h4>
            <ul class="point-list">
              <li v-for="(a, i) in agg.recommended_actions" :key="i" class="pt">
                <span class="pt-num">{{ i + 1 }}</span>
                <span class="pt-text">{{ a }}</span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Right: full round-by-round chain detail -->
        <div class="fp-right">
          <h4 class="sec-title">Round-by-Round</h4>
          <div class="fp-rounds">
            <div v-for="round in roundSummaries" :key="round.num" class="fp-round">
              <div class="fpr-head">
                <span class="fpr-num">R{{ round.num }}</span>
                <span class="fpr-time">{{ round.timeLabel }}</span>
                <span class="pill sm" :class="sentimentClass(round.sentiment)">{{ round.sentiment >= 0 ? '+' : '' }}{{ round.sentiment.toFixed(2) }}</span>
                <span class="fpr-count">{{ round.actionCount }} actions</span>
              </div>
              <p v-if="round.headline" class="fpr-headline">{{ round.headline }}</p>
              <!-- Top 4 actions as compact rows -->
              <div v-for="action in round.actions.slice(0, 4)" :key="action.persona" class="fpr-action">
                <span class="fpr-dot" :style="{ background: action.color }"></span>
                <span class="fpr-name">{{ action.name }}</span>
                <span class="fpr-title">{{ action.title }}</span>
                <span class="pill sm" :class="sentimentClass(action.sentiment)">{{ action.sentimentLabel }}</span>
              </div>
              <div v-if="round.actions.length > 4" class="fpr-more">+{{ round.actions.length - 4 }} more actions</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  visible: Boolean,
  view: { type: String, default: 'sidebar' },
  aggregateMetrics: { type: Object, default: () => ({}) },
  totalRounds: { type: Number, default: 6 },
  agentDefs: { type: Object, default: () => ({}) },
  rounds: { type: Array, default: () => [] },
  influenceLog: { type: Array, default: () => [] },
})
const emit = defineEmits(['toggle-view'])

const agg = computed(() => props.aggregateMetrics || {})
const sidebarWidth = ref(380)
const activeTab = ref('points')

function startResize(e) {
  const startX = e.clientX, startW = sidebarWidth.value
  function onMove(e2) { sidebarWidth.value = Math.max(300, Math.min(600, startW + (e2.clientX - startX))) }
  function onUp() { document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp) }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

function sentimentClass(v) { return v > 0.2 ? 'pos' : v < -0.2 ? 'neg' : 'neu' }
function sentimentLabel(v) {
  if (v > 0.5) return 'Very +ve'
  if (v > 0.2) return 'Positive'
  if (v < -0.5) return 'Very -ve'
  if (v < -0.2) return 'Negative'
  return 'Neutral'
}

function exportResults() {
  const data = { metrics: agg.value, agents: Object.keys(props.agentDefs).length, rounds: props.rounds, exported_at: new Date().toISOString() }
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `foresight-${new Date().toISOString().slice(0, 10)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

// Key findings as bullet points
const summaryPoints = computed(() => {
  const text = agg.value.narrative_summary || ''
  if (!text) return []
  const paras = text.split(/\n+/).filter(p => p.trim().length > 10)
  const points = []
  for (const para of paras) {
    if (para.length < 200) points.push(para.trim())
    else points.push(...para.split(/(?<=[.!?])\s+(?=[A-Z])/).filter(s => s.length > 15).map(s => s.trim()))
  }
  return points.map(s => {
    const l = s.toLowerCase()
    let type = 'neutral'
    if (l.match(/\b(negative|crisis|fail|collapse|risk|decline|drop|loss|damage|threat)\b/)) type = 'negative'
    else if (l.match(/\b(positive|opportunit|recover|support|growth|gain|improve|success|stabiliz)\b/)) type = 'positive'
    return { text: s, type }
  })
})

const parsedTurningPoints = computed(() => (agg.value.key_turning_points || []).map(tp => {
  const m = tp.match(/^(.+?\)):\s*(.+)$/)
  if (m) return { label: m[1], text: m[2] }
  const ci = tp.indexOf(':')
  if (ci > 0 && ci < 50) return { label: tp.slice(0, ci).trim(), text: tp.slice(ci + 1).trim() }
  return { label: '', text: tp }
}))

// Per-round summaries for the chain/timeline view
const roundSummaries = computed(() => {
  const defs = props.agentDefs || {}
  return (props.rounds || []).map(round => {
    const rn = round.round_number
    const active = (round.actions || []).filter(a => a.action_type !== 'no_action')
    const sentiment = round.metrics?.avg_sentiment || 0
    const maxAgents = 3
    const topAgents = active.slice(0, maxAgents).map(a => ({
      key: a.persona,
      name: defs[a.persona]?.name || a.persona?.replace(/_/g, ' '),
      color: defs[a.persona]?.color || '#666',
    }))
    // Pick the most impactful action title as headline
    const sorted = [...active].sort((a, b) => Math.abs(b.sentiment_score || 0) - Math.abs(a.sentiment_score || 0))
    const headline = sorted[0]?.title || ''
    return {
      num: rn,
      timeLabel: round.time_label || '',
      sentiment,
      headline,
      actionCount: active.length,
      topAgents,
      moreCount: Math.max(0, active.length - maxAgents),
      actions: active.map(a => ({
        persona: a.persona,
        name: defs[a.persona]?.name || a.persona?.replace(/_/g, ' '),
        color: defs[a.persona]?.color || '#666',
        title: a.title || '',
        sentiment: a.sentiment_score || 0,
        sentimentLabel: sentimentLabel(a.sentiment_score || 0),
        actionType: a.action_type?.replace(/_/g, ' ') || '',
      })),
    }
  })
})

const tabs = computed(() => [
  { key: 'points', label: 'Summary' },
  { key: 'chains', label: 'Rounds' },
  { key: 'timeline', label: 'Events' },
])

const sparkW = computed(() => Math.max((agg.value.sentiment_trajectory?.length || 1) * 40, 80))
function mkPoints(data, h2) {
  if (!data?.length) return { str: '', arr: [] }
  const w = sparkW.value, step = w / Math.max(data.length - 1, 1)
  const arr = data.map((v, i) => ({ x: i * step, y: h2 - ((v + 1) / 2) * (h2 - 4) - 2 }))
  return { str: arr.map(p => `${p.x},${p.y}`).join(' '), arr }
}
const sparkPointsLg = computed(() => mkPoints(agg.value.sentiment_trajectory, 24).str)
const sparkArrLg = computed(() => mkPoints(agg.value.sentiment_trajectory, 24).arr)
</script>

<style scoped>
/* SIDEBAR */
.sidebar {
  position: fixed;
  top: 44px; left: 0; bottom: 0;
  z-index: 40;
  background: #0c0c0d;
  border-right: 1px solid rgba(255,255,255,0.08);
  display: flex; flex-direction: column;
  overflow: hidden;
}
.resize-handle {
  position: absolute; top: 0; right: -3px; bottom: 0;
  width: 6px; cursor: col-resize; z-index: 10;
}

.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}
.panel-title { font-size: 13px; font-weight: 500; color: rgba(255,255,255,0.8); letter-spacing: -0.02em; }
.header-actions { display: flex; gap: 4px; }
.icon-btn {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: none; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 6px; color: rgba(255,255,255,0.3);
  cursor: pointer; transition: color 0.15s, border-color 0.15s;
}
.icon-btn:hover { color: rgba(255,255,255,0.6); border-color: rgba(255,255,255,0.12); }

/* Stats */
.stat-row {
  display: flex; padding: 8px 12px; gap: 2px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}
.stat {
  flex: 1; display: flex; flex-direction: column; align-items: center; gap: 1px;
  padding: 4px 0;
}
.stat-val { font-size: 15px; font-weight: 500; color: rgba(255,255,255,0.7); letter-spacing: -0.02em; }
.stat-label { font-size: 10px; color: rgba(255,255,255,0.3); }
.stat.pos .stat-val { color: rgba(34,197,94,0.9); }
.stat.neg .stat-val { color: rgba(239,68,68,0.9); }

/* Tabs */
.tab-row {
  display: flex; padding: 0 12px; gap: 0;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  flex-shrink: 0;
}
.tab {
  flex: 1; padding: 9px 0;
  font-size: 11px; font-weight: 500;
  color: rgba(255,255,255,0.25);
  background: none; border: none;
  cursor: pointer; transition: color 150ms;
  text-align: center;
  letter-spacing: -0.01em;
  position: relative;
}
.tab:hover { color: rgba(255,255,255,0.45); }
.tab.active { color: rgba(255,255,255,0.75); }
.tab.active::after {
  content: '';
  position: absolute; bottom: 0; left: 20%; right: 20%;
  height: 1px; background: rgba(255,255,255,0.3);
}

.sidebar-scroll { flex: 1; overflow-y: auto; padding: 10px 12px; }

/* SHARED */
.section { margin-bottom: 14px; }
.sec-title {
  font-size: 11px; font-weight: 500; color: rgba(255,255,255,0.3);
  margin-bottom: 6px;
}
.pill { font-size: 10px; padding: 2px 7px; border-radius: 5px; font-weight: 500; }
.pill.sm { font-size: 9px; padding: 1px 5px; }
.pill.pos { background: rgba(34,197,94,0.1); color: rgba(34,197,94,0.8); }
.pill.neg { background: rgba(239,68,68,0.1); color: rgba(239,68,68,0.8); }
.pill.neu { background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.3); }

/* Point list */
.point-list { list-style: none; margin: 0; padding: 0; }
.pt {
  display: flex; gap: 8px; align-items: flex-start;
  padding: 5px 0;
}
.pt + .pt { border-top: 1px solid rgba(255,255,255,0.05); }
.pt-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: rgba(255,255,255,0.12); flex-shrink: 0; margin-top: 6px;
}
.pt-dot.positive { background: rgba(34,197,94,0.7); }
.pt-dot.negative { background: rgba(239,68,68,0.7); }
.pt-dot.timeline { background: var(--accent); opacity: 0.5; }
.pt-text { font-size: 12px; line-height: 1.5; color: rgba(255,255,255,0.55); }
.pt-num {
  width: 16px; height: 16px;
  display: flex; align-items: center; justify-content: center;
  font-size: 9px; font-weight: 700;
  color: rgba(255,255,255,0.25);
  background: rgba(255,255,255,0.04);
  border-radius: 3px; flex-shrink: 0; margin-top: 3px;
}
.tp-label {
  font-size: 10px; color: var(--accent); opacity: 0.5;
  display: block; margin-bottom: 1px;
}

.empty-state {
  text-align: center; padding: 24px 0;
  font-size: 12px; color: rgba(255,255,255,0.15);
}

/* Round timeline (chains tab) */
.round-timeline { padding: 0; }
.rt-row {
  display: flex; gap: 10px;
}
.rt-rail {
  display: flex; flex-direction: column; align-items: center;
  width: 12px; flex-shrink: 0; padding-top: 2px;
}
.rt-dot {
  width: 8px; height: 8px; border-radius: 50%;
  background: rgba(255,255,255,0.12); flex-shrink: 0;
}
.rt-dot.pos { background: rgba(34,197,94,0.6); }
.rt-dot.neg { background: rgba(239,68,68,0.6); }
.rt-line {
  width: 1px; flex: 1; min-height: 16px;
  background: rgba(255,255,255,0.06);
}
.rt-body {
  flex: 1; padding-bottom: 12px; min-width: 0;
}
.rt-head {
  display: flex; align-items: center; gap: 6px; margin-bottom: 3px;
}
.rt-round { font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.5); }
.rt-time { font-size: 10px; color: rgba(255,255,255,0.5); }
.rt-sentiment { margin-left: auto; }
.rt-headline {
  font-size: 12px; line-height: 1.4; color: rgba(255,255,255,0.4);
  margin: 0 0 4px;
}
.rt-agents {
  display: flex; flex-wrap: wrap; gap: 4px; align-items: center;
}
.rt-agent {
  display: inline-flex; align-items: center; gap: 3px;
  font-size: 10px; color: rgba(255,255,255,0.3);
}
.rt-agent-dot {
  width: 4px; height: 4px; border-radius: 50%; flex-shrink: 0;
}
.rt-more {
  font-size: 9px; color: rgba(255,255,255,0.15);
}

/* FULL PAGE */
.fullpage {
  position: fixed; top: 44px; left: 0; right: 0; bottom: 30px;
  z-index: 150;
  background: #0a0a0b;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.fp-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}
.fp-metrics { display: flex; align-items: center; gap: 24px; }
.fp-metric { display: flex; flex-direction: column; align-items: center; gap: 1px; }
.fp-val { font-size: 18px; font-weight: 500; color: rgba(255,255,255,0.8); letter-spacing: -0.02em; }
.fp-metric.pos .fp-val { color: rgba(34,197,94,0.9); }
.fp-metric.neg .fp-val { color: rgba(239,68,68,0.9); }
.fp-label { font-size: 10px; color: rgba(255,255,255,0.25); }
.fp-spark { margin-left: auto; width: 120px; height: 24px; }
.fp-actions { display: flex; gap: 4px; }

.fp-body {
  display: flex; flex: 1; min-height: 0; overflow: hidden;
}
.fp-left {
  flex: 1; overflow-y: auto; padding: 20px 24px;
  border-right: 1px solid rgba(255,255,255,0.06);
}
.fp-right {
  width: 480px; flex-shrink: 0; overflow-y: auto; padding: 16px 20px;
}

/* Full page rounds */
.fp-rounds { display: flex; flex-direction: column; gap: 2px; }
.fp-round {
  padding: 10px 12px;
  background: rgba(255,255,255,0.015);
  border: 1px solid rgba(255,255,255,0.03);
  border-radius: 8px;
}
.fpr-head {
  display: flex; align-items: center; gap: 8px; margin-bottom: 4px;
}
.fpr-num {
  font-size: 11px; font-weight: 700; color: rgba(255,255,255,0.5);
  background: rgba(255,255,255,0.04);
  padding: 1px 5px; border-radius: 3px;
}
.fpr-time { font-size: 10px; color: rgba(255,255,255,0.5); }
.fpr-count { font-size: 10px; color: rgba(255,255,255,0.15); margin-left: auto; }
.fpr-headline {
  font-size: 12px; line-height: 1.4; color: rgba(255,255,255,0.4);
  margin: 0 0 6px;
}
.fpr-action {
  display: flex; align-items: center; gap: 6px;
  padding: 3px 0;
  font-size: 11px;
}
.fpr-action + .fpr-action { border-top: 1px solid rgba(255,255,255,0.05); }
.fpr-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.fpr-name { color: rgba(255,255,255,0.45); font-weight: 500; flex-shrink: 0; max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fpr-title { color: rgba(255,255,255,0.25); flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.fpr-more { font-size: 10px; color: rgba(255,255,255,0.12); padding: 4px 0 0; }
</style>
