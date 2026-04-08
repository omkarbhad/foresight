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
      <div class="pills-row">
        <span class="pill" :class="sentimentClass(agg.final_sentiment)">
          {{ (agg.final_sentiment || 0) >= 0 ? '+' : '' }}{{ (agg.final_sentiment || 0).toFixed(2) }}
        </span>
        <span class="pill muted">{{ agg.total_volume || 0 }} actions</span>
        <span class="pill muted">{{ Object.keys(agentDefs).length }} agents</span>
        <span class="pill muted">{{ totalRounds }}R</span>
      </div>
      <div v-if="agg.sentiment_trajectory?.length" class="spark-strip">
        <svg :viewBox="`0 0 ${sparkW} 20`" preserveAspectRatio="none" class="spark-svg">
          <polyline :points="sparkPoints" fill="none" stroke="var(--accent)" stroke-width="1.5" stroke-linejoin="round"/>
        </svg>
      </div>
      <div class="sidebar-scroll">
        <template v-for="section in sections" :key="section.key">
          <div v-if="section.items.length" class="section">
            <h4 class="sec-title">{{ section.label }}</h4>
            <component :is="section.component" v-bind="section.props" />
          </div>
        </template>
      </div>
    </div>

    <!-- FULL PAGE VIEW -->
    <div v-if="view === 'fullpage'" class="fullpage">
      <div class="fp-header">
        <div class="fp-metrics">
          <div class="fp-metric">
            <span class="fp-label">Sentiment</span>
            <span class="fp-val" :class="sentimentClass(agg.final_sentiment)">{{ (agg.final_sentiment || 0) >= 0 ? '+' : '' }}{{ (agg.final_sentiment || 0).toFixed(2) }}</span>
          </div>
          <div class="fp-metric">
            <span class="fp-label">Actions</span>
            <span class="fp-val">{{ agg.total_volume || 0 }}</span>
          </div>
          <div class="fp-metric">
            <span class="fp-label">Rounds</span>
            <span class="fp-val">{{ totalRounds }}</span>
          </div>
          <div class="fp-metric">
            <span class="fp-label">Agents</span>
            <span class="fp-val">{{ Object.keys(agentDefs).length }}</span>
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
        <div class="fp-left">
          <div v-if="summaryPoints.length" class="section">
            <h4 class="sec-title">Key Findings</h4>
            <div v-for="(p, i) in summaryPoints" :key="i" class="finding">
              <span class="dot" :class="p.type"></span>
              <span>{{ p.text }}</span>
            </div>
          </div>
          <div v-if="parsedTurningPoints.length" class="section">
            <h4 class="sec-title">Timeline</h4>
            <div v-for="(tp, i) in parsedTurningPoints" :key="i" class="tl-row">
              <span v-if="tp.label" class="tl-label">{{ tp.label }}</span>
              <p class="tl-text">{{ tp.text }}</p>
            </div>
          </div>
          <div v-if="agg.recommended_actions?.length" class="section">
            <h4 class="sec-title">Recommended Actions</h4>
            <div v-for="(a, i) in agg.recommended_actions" :key="i" class="action-row">
              <span class="action-num">{{ i + 1 }}.</span>
              <span>{{ a }}</span>
            </div>
          </div>
        </div>
        <div class="fp-right">
          <h4 class="sec-title">Round Breakdown</h4>
          <div v-for="round in rounds" :key="round.round_number" class="round-block">
            <div class="round-head">
              <span class="rn">R{{ round.round_number }}</span>
              <span class="rt">{{ round.time_label }}</span>
              <span v-if="round.metrics" class="rs" :class="sentimentClass(round.metrics.avg_sentiment)">{{ (round.metrics.avg_sentiment || 0).toFixed(2) }}</span>
            </div>
            <div v-for="(a, j) in activeActions(round)" :key="j" class="mini-card">
              <div class="mc-row">
                <span class="mc-dot" :style="{ background: agentDefs[a.persona]?.color || '#666' }"></span>
                <span class="mc-name">{{ agentDefs[a.persona]?.name || a.persona }}</span>
                <span class="mc-type">{{ a.action_type?.replace(/_/g, ' ') }}</span>
              </div>
              <p class="mc-title">{{ a.title }}</p>
              <p class="mc-body">{{ a.content }}</p>
              <div class="mc-pills">
                <span class="pill sm" :class="sentimentClass(a.sentiment_score)">{{ sentimentLabel(a.sentiment_score) }}</span>
                <span v-if="a.reach_estimate" class="pill sm muted">{{ formatReach(a.reach_estimate) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, defineComponent, h } from 'vue'

const props = defineProps({
  visible: Boolean,
  view: { type: String, default: 'sidebar' },
  aggregateMetrics: { type: Object, default: () => ({}) },
  totalRounds: { type: Number, default: 6 },
  agentDefs: { type: Object, default: () => ({}) },
  rounds: { type: Array, default: () => [] },
})
const emit = defineEmits(['toggle-view'])

const agg = computed(() => props.aggregateMetrics || {})
const sidebarWidth = ref(380)

function startResize(e) {
  const startX = e.clientX, startW = sidebarWidth.value
  function onMove(e2) { sidebarWidth.value = Math.max(300, Math.min(600, startW + (e2.clientX - startX))) }
  function onUp() { document.removeEventListener('mousemove', onMove); document.removeEventListener('mouseup', onUp) }
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

function sentimentClass(v) { return v > 0.2 ? 'pos' : v < -0.2 ? 'neg' : 'neu' }
function sentimentLabel(v) {
  if (v > 0.5) return 'Very positive'
  if (v > 0.2) return 'Positive'
  if (v < -0.5) return 'Very negative'
  if (v < -0.2) return 'Negative'
  return 'Neutral'
}
function formatReach(n) {
  if (!n) return ''
  if (n >= 1e9) return (n / 1e9).toFixed(1) + 'B'
  if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M'
  if (n >= 1e3) return (n / 1e3).toFixed(0) + 'K'
  return String(n)
}
function activeActions(round) { return (round.actions || []).filter(a => a.action_type !== 'no_action') }

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

// Sidebar sections (rendered inline via v-for)
const FindingsList = defineComponent({
  props: ['items'],
  render() { return this.items.map((p, i) => h('div', { class: 'finding', key: i }, [h('span', { class: ['dot', p.type] }), h('span', null, p.text)])) }
})
const TimelineList = defineComponent({
  props: ['items'],
  render() { return this.items.map((tp, i) => h('div', { class: 'tl-row', key: i }, [tp.label ? h('span', { class: 'tl-label' }, tp.label) : null, h('p', { class: 'tl-text' }, tp.text)])) }
})
const ActionsList = defineComponent({
  props: ['items'],
  render() { return this.items.map((a, i) => h('div', { class: 'action-row', key: i }, [h('span', { class: 'action-num' }, `${i+1}.`), h('span', null, a)])) }
})
const RoundsList = defineComponent({
  props: ['items', 'agentDefs'],
  setup(props2) {
    return () => props2.items.map(round => {
      const active = (round.actions || []).filter(a => a.action_type !== 'no_action')
      return h('div', { class: 'round-block', key: round.round_number }, [
        h('div', { class: 'round-head' }, [
          h('span', { class: 'rn' }, `R${round.round_number}`),
          h('span', { class: 'rt' }, round.time_label),
          h('span', { class: 'rs' }, `${active.length} actions`),
        ]),
        ...active.slice(0, 3).map((a, j) => h('div', { class: 'mini-action', key: j }, [
          h('span', { class: 'ma-dot', style: { background: props2.agentDefs[a.persona]?.color || '#666' } }),
          h('span', { class: 'ma-name' }, props2.agentDefs[a.persona]?.name || a.persona),
          h('span', { class: 'ma-title' }, a.title),
        ])),
        active.length > 3 ? h('div', { class: 'ma-more' }, `+${active.length - 3} more`) : null,
      ])
    })
  }
})

const sections = computed(() => [
  { key: 'findings', label: 'Key Findings', items: summaryPoints.value, component: FindingsList, props: { items: summaryPoints.value } },
  { key: 'timeline', label: 'Timeline', items: parsedTurningPoints.value, component: TimelineList, props: { items: parsedTurningPoints.value } },
  { key: 'actions', label: 'Recommended Actions', items: agg.value.recommended_actions || [], component: ActionsList, props: { items: agg.value.recommended_actions || [] } },
  { key: 'rounds', label: 'Round Breakdown', items: props.rounds, component: RoundsList, props: { items: props.rounds, agentDefs: props.agentDefs } },
])

const sparkW = computed(() => Math.max((agg.value.sentiment_trajectory?.length || 1) * 40, 80))
function mkPoints(data, h2) {
  if (!data?.length) return { str: '', arr: [] }
  const w = sparkW.value, step = w / Math.max(data.length - 1, 1)
  const arr = data.map((v, i) => ({ x: i * step, y: h2 - ((v + 1) / 2) * (h2 - 4) - 2 }))
  return { str: arr.map(p => `${p.x},${p.y}`).join(' '), arr }
}
const sparkPoints = computed(() => mkPoints(agg.value.sentiment_trajectory, 20).str)
const sparkPointsLg = computed(() => mkPoints(agg.value.sentiment_trajectory, 24).str)
const sparkArrLg = computed(() => mkPoints(agg.value.sentiment_trajectory, 24).arr)
</script>

<style scoped>
/* SIDEBAR VIEW */
.sidebar {
  position: fixed;
  top: 44px; left: 0; bottom: 30px;
  z-index: 40;
  background: #0c0c0d;
  border-right: 1px solid rgba(255,255,255,0.06);
  border-left: none;
  border-top: none;
  border-bottom: none;
  border-radius: 0;
  display: flex; flex-direction: column;
  overflow: hidden;
}
.resize-handle {
  position: absolute; top: 0; right: -3px; bottom: 0;
  width: 6px; cursor: col-resize; z-index: 10;
}
.resize-handle:hover { background: transparent; }

.panel-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}
.panel-title { font-size: 13px; font-weight: 600; color: rgba(255,255,255,0.8); }
.header-actions { display: flex; gap: 4px; }
.icon-btn {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: none; border: 1px solid rgba(255,255,255,0.06);
  border-radius: 6px; color: rgba(255,255,255,0.3);
  cursor: pointer; transition: color 0.15s, border-color 0.15s;
}
.icon-btn:hover { color: rgba(255,255,255,0.6); border-color: rgba(255,255,255,0.12); }

.pills-row {
  display: flex; gap: 5px; padding: 8px 12px; flex-wrap: wrap;
  border-bottom: 1px solid rgba(255,255,255,0.06); flex-shrink: 0;
}
.pill {
  font-size: 10px; padding: 2px 7px; border-radius: 5px; font-weight: 500;
}
.pill.sm { font-size: 9px; padding: 1px 6px; }
.pill.pos { background: rgba(34,197,94,0.1); color: rgba(34,197,94,0.8); }
.pill.neg { background: rgba(239,68,68,0.1); color: rgba(239,68,68,0.8); }
.pill.neu { background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.35); }
.pill.muted { background: rgba(255,255,255,0.04); color: rgba(255,255,255,0.25); }

.spark-strip {
  padding: 6px 12px; border-bottom: 1px solid rgba(255,255,255,0.06); flex-shrink: 0;
}
.spark-svg { width: 100%; height: 20px; display: block; }

.sidebar-scroll { flex: 1; overflow-y: auto; padding: 10px 12px; }

/* FULL PAGE VIEW */
.fullpage {
  position: fixed; top: 44px; left: 0; right: 0; bottom: 0;
  z-index: 40;
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
.fp-metric { display: flex; flex-direction: column; gap: 2px; }
.fp-label { font-size: 10px; color: rgba(255,255,255,0.25); }
.fp-val { font-size: 16px; font-weight: 600; color: rgba(255,255,255,0.8); }
.fp-val.pos { color: var(--success); }
.fp-val.neg { color: var(--danger); }
.fp-spark { margin-left: auto; width: 100px; height: 24px; }
.fp-actions { display: flex; gap: 4px; }

.fp-body {
  display: flex; flex: 1; min-height: 0; overflow: hidden;
}
.fp-left {
  flex: 1; overflow-y: auto; padding: 20px 24px;
  border-right: 1px solid rgba(255,255,255,0.06);
}
.fp-right {
  width: 440px; flex-shrink: 0; overflow-y: auto; padding: 20px 20px;
}

/* SHARED STYLES */
.section { margin-bottom: 16px; }
.sec-title {
  font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.35);
  margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.03em;
}

.finding {
  display: flex; gap: 10px; align-items: flex-start;
  margin-bottom: 10px;
  padding: 8px 10px;
  background: rgba(255,255,255,0.015);
  border: 1px solid rgba(255,255,255,0.03);
  border-radius: 8px;
}
.dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: rgba(255,255,255,0.15); flex-shrink: 0; margin-top: 5px;
}
.dot.positive { background: var(--success); }
.dot.negative { background: var(--danger); }
.finding span:last-child { font-size: 12px; line-height: 1.6; color: rgba(255,255,255,0.5); }

.tl-row { margin-bottom: 8px; }
.tl-label { font-size: 10px; color: var(--accent); opacity: 0.6; display: block; margin-bottom: 2px; }
.tl-text { font-size: 12px; line-height: 1.5; color: rgba(255,255,255,0.4); margin: 0; }

.action-row { display: flex; gap: 6px; margin-bottom: 4px; font-size: 12px; line-height: 1.5; color: rgba(255,255,255,0.4); }
.action-num { color: rgba(255,255,255,0.2); flex-shrink: 0; }

.round-block { margin-bottom: 14px; }
.round-head {
  display: flex; align-items: center; gap: 8px;
  padding-bottom: 4px; margin-bottom: 4px;
  border-bottom: 1px solid rgba(255,255,255,0.04);
}
.rn { font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.5); }
.rt { font-size: 10px; color: rgba(255,255,255,0.2); }
.rs { font-size: 10px; color: rgba(255,255,255,0.2); margin-left: auto; }
.rs.pos { color: var(--success); }
.rs.neg { color: var(--danger); }

/* Mini cards in full page */
.mini-card {
  padding: 10px 12px; margin-bottom: 6px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.05);
  border-radius: 10px;
}
.mc-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.mc-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.mc-name { font-size: 11px; font-weight: 600; color: rgba(255,255,255,0.6); }
.mc-type { font-size: 10px; color: rgba(255,255,255,0.2); margin-left: auto; text-transform: capitalize; }
.mc-title { font-size: 12px; font-weight: 500; color: rgba(255,255,255,0.75); margin: 0 0 2px; line-height: 1.3; }
.mc-body { font-size: 11px; color: rgba(255,255,255,0.3); line-height: 1.4; margin: 0; max-height: 40px; overflow: hidden; }
.mc-pills { display: flex; gap: 5px; margin-top: 6px; }

/* Mini actions in sidebar */
.mini-action {
  display: flex; align-items: center; gap: 5px;
  padding: 2px 0; font-size: 11px;
}
.ma-dot { width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }
.ma-name { color: rgba(255,255,255,0.45); font-weight: 500; flex-shrink: 0; }
.ma-title { color: rgba(255,255,255,0.25); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.ma-more { font-size: 10px; color: rgba(255,255,255,0.15); padding-left: 10px; }
</style>
