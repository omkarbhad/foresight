<template>
  <div class="graph-wrapper" :class="{ visible, 'results-shifted': resultsOpen }">
    <div v-if="hasMultipleScenarios" class="graph-controls">
      <select v-model="filterMode" class="filter-select">
        <option value="all">All Scenarios</option>
        <option value="cross">Cross-Scenario</option>
        <option v-for="(name, idx) in scenarioMap" :key="idx" :value="String(idx)">
          {{ name.length > 35 ? name.slice(0, 35) + '...' : name }}
        </option>
      </select>
    </div>
    <div v-if="tooltip.visible" class="tooltip" :style="tooltipStyle">
      <div class="tooltip-name">{{ tooltip.name }}</div>
      <div class="tooltip-role">{{ tooltip.role }}</div>
      <div class="tooltip-stat" v-if="tooltip.connections > 0">{{ tooltip.connections }} connection{{ tooltip.connections !== 1 ? 's' : '' }}</div>
      <div class="tooltip-sentiment" v-if="tooltip.sentiment !== null">
        Sentiment: <span :style="{ color: tooltip.sentiment >= 0 ? 'var(--success)' : 'var(--danger)' }">{{ tooltip.sentiment >= 0 ? '+' : '' }}{{ tooltip.sentiment.toFixed(2) }}</span>
      </div>
    </div>
    <div class="graph-container" ref="graphEl"></div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const SCENARIO_COLORS = ['#2563eb','#dc2626','#059669','#7c3aed','#ea580c','#0891b2','#db2777','#65a30d']

// Pixel-art character shapes for nodes
const PIXEL_SHAPES = [
  [[0,0,1,1,1,0,0],[0,1,1,1,1,1,0],[1,1,0,1,0,1,1],[1,1,1,1,1,1,1],[1,0,1,1,1,0,1]], // ghost
  [[0,0,1,0,0,0,1,0,0],[0,0,0,1,0,1,0,0,0],[0,0,1,1,1,1,1,0,0],[0,1,0,1,1,1,0,1,0],[1,1,1,1,1,1,1,1,1],[1,0,1,0,0,0,1,0,1]], // invader
  [[0,0,0,1,1,0,0,0],[0,0,1,1,1,1,0,0],[0,1,1,1,1,1,1,0],[1,1,0,1,1,0,1,1],[1,1,1,1,1,1,1,1]], // squid
  [[0,1,1,1,1,0],[1,1,1,1,1,1],[1,1,1,0,0,0],[1,1,1,1,1,1],[0,1,1,1,1,0]], // pac
  [[0,1,0,1,0],[1,1,1,1,1],[1,1,1,1,1],[0,1,1,1,0],[0,0,1,0,0]], // heart
  [[0,0,1,0,0],[0,1,1,1,0],[1,1,1,1,1],[0,1,1,1,0],[0,0,1,0,0]], // diamond
  [[0,0,1,0,0],[0,1,1,1,0],[1,1,1,1,1],[0,1,1,1,0],[0,1,0,1,0]], // star
  [[1,1,1],[0,1,0],[0,1,0]], // T-tetris
  [[1,0],[1,0],[1,1]], // L-tetris
]
// Assign a shape to each agent key deterministically
const shapeMap = new Map()
function getShape(key) {
  if (!shapeMap.has(key)) {
    let hash = 0
    for (let i = 0; i < key.length; i++) hash = ((hash << 5) - hash) + key.charCodeAt(i)
    shapeMap.set(key, PIXEL_SHAPES[Math.abs(hash) % PIXEL_SHAPES.length])
  }
  return shapeMap.get(key)
}

const props = defineProps({
  agentDefs: { type: Object, default: () => ({}) },
  influenceLog: { type: Array, default: () => [] },
  agentTimeline: { type: Array, default: () => [] },
  currentRound: { type: Number, default: 0 },
  scenarioMap: { type: Object, default: () => ({}) },
  agentScenarioMap: { type: Object, default: () => ({}) },
  visible: { type: Boolean, default: false },
  resultsOpen: { type: Boolean, default: false },
})

const graphEl = ref(null)
const filterMode = ref('all')
const nodeCount = ref(0)
const edgeCount = ref(0)

let svg, simulation, nodeGroup, linkGroup, labelGroup
let nodePositions = new Map()
let resizeObserver

const tooltip = reactive({ visible: false, name: '', role: '', connections: 0, sentiment: null, x: 0, y: 0 })
const tooltipStyle = computed(() => ({ left: tooltip.x + 'px', top: tooltip.y + 'px' }))
const hasMultipleScenarios = computed(() => Object.keys(props.scenarioMap).length > 1)

function getColor(key) { return props.agentDefs?.[key]?.color || '#6B7194' }
function getLabel(key) { return props.agentDefs?.[key]?.name || key?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || key }
function getScenarioColor(idx) { return SCENARIO_COLORS[Number(idx) % SCENARIO_COLORS.length] }
function getScenarioIdx(key) {
  const sc = props.agentScenarioMap?.[key] || ''
  for (const [idx, name] of Object.entries(props.scenarioMap)) { if (name === sc) return Number(idx) }
  return 0
}

function computeNodes() {
  return Object.keys(props.agentDefs || {}).map(key => {
    const saved = nodePositions.get(key)
    const d = props.agentDefs[key]
    const r = Math.max(8, Math.min(18, 8 + ((d?.reach_multiplier || 1) - 0.5) * 2))
    return { id: key, label: getLabel(key), color: getColor(key), scenarioIndex: getScenarioIdx(key), radius: r, x: saved?.x, y: saved?.y, vx: saved?.vx || 0, vy: saved?.vy || 0 }
  })
}

function computeLinks() {
  const counts = {}
  const keys = new Set(Object.keys(props.agentDefs || {}))
  for (const e of (props.influenceLog || [])) {
    if (!keys.has(e.from) || !keys.has(e.to) || e.from === e.to) continue
    const k = `${e.from}|${e.to}`
    counts[k] = (counts[k] || 0) + 1
  }
  return Object.entries(counts).map(([k, count]) => {
    const [source, target] = k.split('|')
    const cross = hasMultipleScenarios.value && (props.agentScenarioMap?.[source] || '') !== (props.agentScenarioMap?.[target] || '')
    return { source, target, count, cross }
  })
}

function initGraph() {
  const el = graphEl.value
  if (!el) return
  d3.select(el).selectAll('*').remove()
  const w = el.clientWidth || 600, h = el.clientHeight || 500

  svg = d3.select(el).append('svg').attr('width', w).attr('height', h)

  const zoomBehavior = d3.zoom()
    .scaleExtent([0.3, 3])
    .on('zoom', (event) => {
      linkGroup.attr('transform', event.transform)
      nodeGroup.attr('transform', event.transform)
      labelGroup.attr('transform', event.transform)
    })
  svg.call(zoomBehavior)

  const defs = svg.append('defs')

  // Arrow markers — slim open chevron style
  const addArrow = (id, color) => {
    defs.append('marker')
      .attr('id', id)
      .attr('viewBox', '0 0 10 10')
      .attr('refX', 18)
      .attr('refY', 5)
      .attr('markerWidth', 5)
      .attr('markerHeight', 5)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M2,2 L8,5 L2,8')
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', 1.5)
      .attr('stroke-linecap', 'round')
      .attr('stroke-linejoin', 'round')
  }
  addArrow('arrow', 'rgba(255,255,255,0.1)')
  addArrow('arrow-cross', '#eab308')
  addArrow('arrow-hover', 'rgba(255,255,255,0.4)')

  linkGroup = svg.append('g')
  nodeGroup = svg.append('g')
  labelGroup = svg.append('g')

  simulation = d3.forceSimulation()
    .force('link', d3.forceLink().id(d => d.id).distance(80))
    .force('charge', d3.forceManyBody().strength(-200))
    .force('center', d3.forceCenter(w / 2, h / 2))
    .force('collision', d3.forceCollide(20))
    .on('tick', () => {
      const w2 = el.clientWidth || 600, h2 = el.clientHeight || 500
      nodeGroup.selectAll('g.node').each(d => {
        d.x = Math.max(30, Math.min(w2 - 30, d.x))
        d.y = Math.max(30, Math.min(h2 - 30, d.y))
        nodePositions.set(d.id, { x: d.x, y: d.y, vx: d.vx, vy: d.vy })
      })
      linkGroup.selectAll('path').attr('d', d => {
        const dx = d.target.x - d.source.x, dy = d.target.y - d.source.y
        const dr = Math.sqrt(dx * dx + dy * dy) * 1.2
        return `M${d.source.x},${d.source.y}A${dr},${dr} 0 0,1 ${d.target.x},${d.target.y}`
      })
      nodeGroup.selectAll('g.node').attr('transform', d => `translate(${d.x},${d.y})`)
      labelGroup.selectAll('text').attr('x', d => d.x).attr('y', d => d.y)
    })

  updateGraph()
}

function updateGraph() {
  if (!svg || !simulation) return
  const nodes = computeNodes()
  const links = computeLinks()
  const el = graphEl.value
  const w = el?.clientWidth || 600, h = el?.clientHeight || 500

  for (const n of nodes) {
    if (n.x == null) {
      n.x = w / 2 + (Math.random() - 0.5) * Math.min(w * 0.6, 400)
      n.y = h / 2 + (Math.random() - 0.5) * Math.min(h * 0.6, 300)
    }
  }

  nodeCount.value = nodes.length
  edgeCount.value = links.length
  const maxCount = Math.max(...links.map(l => l.count), 1)

  // Links — thin curved paths
  // Scale opacity down when there are many links
  const linkOpacity = links.length > 100 ? 0.03 : links.length > 50 ? 0.05 : 0.08
  linkGroup.selectAll('path').remove()
  linkGroup.selectAll('path').data(links).enter().append('path')
    .attr('stroke', d => d.cross ? 'rgba(234,179,8,0.15)' : 'rgba(255,255,255,0.04)')
    .attr('stroke-opacity', 1)
    .attr('stroke-width', d => 0.3 + (d.count / maxCount) * 0.7)
    .attr('fill', 'none')
    .attr('stroke-dasharray', d => d.cross ? '4,2' : null)
    .attr('marker-end', d => d.cross ? 'url(#arrow-cross)' : 'url(#arrow)')

  // Nodes as pixel characters
  const nodeSel = nodeGroup.selectAll('g.node').data(nodes, d => d.id)
  nodeSel.exit().remove()

  const nodeEnter = nodeSel.enter().append('g')
    .attr('class', 'node')
    .attr('cursor', 'grab')
    .call(d3.drag()
      .on('start', (e, d) => { if (!e.active) simulation.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y })
      .on('drag', (e, d) => { d.fx = e.x; d.fy = e.y })
      .on('end', (e, d) => { if (!e.active) simulation.alphaTarget(0); d.fx = null; d.fy = null })
    )

  // Draw pixel character for each new node
  nodeEnter.each(function(d) {
    const g = d3.select(this)
    const shape = getShape(d.id)
    const px = 2.5 // pixel size
    const rows = shape.length
    const cols = shape[0].length
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (shape[r][c]) {
          g.append('rect')
            .attr('x', (c - cols/2) * px)
            .attr('y', (r - rows/2) * px)
            .attr('width', px - 0.3)
            .attr('height', px - 0.3)
            .attr('fill', d.color)
        }
      }
    }
    // Invisible larger circle for hover/drag hit area
    g.append('circle')
      .attr('r', d.radius)
      .attr('fill', 'transparent')
      .attr('stroke', 'none')
  })

  nodeEnter.on('mouseenter', (e, d) => {
      tooltip.name = d.label
      tooltip.role = props.agentDefs?.[d.id]?.role || ''
      // Count influence connections for this agent
      const connectionCount = (props.influenceLog || []).filter(
        entry => entry.from === d.id || entry.to === d.id
      ).length
      tooltip.connections = connectionCount
      // Get latest sentiment from agentTimeline or rounds
      let latestSentiment = null
      const timeline = props.agentTimeline || []
      for (let i = timeline.length - 1; i >= 0; i--) {
        const entry = timeline[i]
        if (entry?.agent_key === d.id && entry?.sentiment != null) {
          latestSentiment = entry.sentiment
          break
        }
      }
      tooltip.sentiment = latestSentiment
      const rect = el.getBoundingClientRect()
      tooltip.x = e.clientX - rect.left + 12
      tooltip.y = e.clientY - rect.top - 10
      tooltip.visible = true
      highlightNode(d)
    })
    .on('mouseleave', () => { tooltip.visible = false; resetHighlight() })
    .transition().duration(300)
    .attr('r', d => d.radius)

  // Update existing node colors
  nodeSel.selectAll('rect').attr('fill', function() { return d3.select(this.parentNode).datum()?.color })

  // Labels — always visible, small, truncated
  const lblSel = labelGroup.selectAll('text').data(nodes, d => d.id)
  lblSel.exit().remove()
  lblSel.enter().append('text')
    .text(d => d.label.length > 16 ? d.label.slice(0, 14) + '..' : d.label)
    .attr('font-size', 9)
    .attr('font-weight', 400)
    .attr('font-family', 'Inter, sans-serif')
    .attr('fill', 'rgba(255,255,255,0.4)')
    .attr('text-anchor', 'middle')
    .attr('dy', d => -(d.radius + 6))
    .attr('opacity', 0.7)
  lblSel.text(d => d.label.length > 16 ? d.label.slice(0, 14) + '..' : d.label).attr('dy', d => -(d.radius + 6))

  simulation.nodes(nodes)
  simulation.force('link').links(links)
  simulation.alpha(0.35).restart()
}

function highlightNode(d) {
  const connected = new Set([d.id])
  linkGroup.selectAll('path').each(function(l) {
    const s = l.source.id || l.source, t = l.target.id || l.target
    if (s === d.id || t === d.id) {
      connected.add(s); connected.add(t)
      d3.select(this)
        .attr('stroke', l.cross ? 'rgba(234,179,8,0.4)' : 'rgba(255,255,255,0.15)')
        .attr('stroke-opacity', 0.5)
        .attr('stroke-width', 1.2)
        .attr('marker-end', l.cross ? 'url(#arrow-cross)' : 'url(#arrow-hover)')
    } else {
      d3.select(this).attr('stroke-opacity', 0.03)
    }
  })
  nodeGroup.selectAll('g.node').attr('opacity', n => connected.has(n.id) ? 1 : 0.12)
  labelGroup.selectAll('text')
    .attr('opacity', n => connected.has(n.id) ? 1 : 0.1)
    .attr('font-weight', n => n.id === d.id ? 600 : 400)
}

function resetHighlight() {
  const maxCount = Math.max(...computeLinks().map(l => l.count), 1)
  linkGroup.selectAll('path')
    .attr('stroke', d => d.cross ? 'rgba(234,179,8,0.15)' : 'rgba(255,255,255,0.04)')
    .attr('stroke-opacity', 1)
    .attr('stroke-width', d => 0.5 + (d.count / maxCount) * 1)
    .attr('marker-end', d => d.cross ? 'url(#arrow-cross)' : 'url(#arrow)')
  nodeGroup.selectAll('g.node').attr('opacity', 1)
  labelGroup.selectAll('text').attr('opacity', 0.7).attr('font-weight', 400)
}

onMounted(() => {
  nextTick(initGraph)
  resizeObserver = new ResizeObserver(() => {
    if (!svg || !graphEl.value) return
    const w = graphEl.value.clientWidth || 600, h = graphEl.value.clientHeight || 500
    svg.attr('width', w).attr('height', h)
    simulation?.force('center', d3.forceCenter(w / 2, h / 2))
    simulation?.alpha(0.15).restart()
  })
  if (graphEl.value) resizeObserver.observe(graphEl.value)
})

onUnmounted(() => {
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
})

watch([() => props.agentDefs, () => props.influenceLog], () => { nextTick(updateGraph) }, { deep: true })
watch(filterMode, () => { nextTick(updateGraph) })
</script>

<style scoped>
.graph-wrapper {
  position: fixed;
  top: 44px;
  left: 0;
  right: 320px;
  bottom: 28px;
  z-index: 10;
  background: transparent;
  opacity: 0;
  transition: opacity 0.15s ease, left 0.15s ease;
  pointer-events: none;
}
.graph-wrapper.visible { opacity: 1; pointer-events: all; }
.graph-wrapper.results-shifted { left: 340px; }
.graph-controls {
  position: absolute;
  top: 12px;
  left: 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  z-index: 5;
}
.filter-select {
  padding: 4px 8px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  color: var(--text-secondary);
  font-size: 11px;
}
.stat {
  font-size: 11px;
  color: rgba(255,255,255,0.2);
}
.tooltip {
  position: absolute;
  z-index: 20;
  pointer-events: none;
  background: rgba(0,0,0,0.8);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 10px;
  backdrop-filter: blur(8px);
  padding: 8px 10px;
  max-width: 220px;
}
.tooltip-name { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.tooltip-role { font-size: 11px; color: var(--text-secondary); }
.tooltip-stat { font-size: 11px; color: var(--text-muted); margin-top: 4px; }
.tooltip-sentiment { font-size: 11px; color: var(--text-muted); margin-top: 2px; }
.graph-container { width: 100%; height: 100%; background: transparent; }
.graph-container :deep(svg) { display: block; }
</style>
