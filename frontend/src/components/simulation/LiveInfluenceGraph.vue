<template>
  <div class="live-graph-wrapper">
    <div class="live-graph-header">
      <h3>{{ title }}</h3>
      <div class="graph-controls">
        <select v-if="hasMultipleScenarios" v-model="filterMode" class="filter-select">
          <option value="all">All Scenarios</option>
          <option value="cross">Cross-Scenario Only</option>
          <option v-for="(name, idx) in scenarioMap" :key="idx" :value="String(idx)">
            {{ name.length > 40 ? name.slice(0, 40) + '...' : name }}
          </option>
        </select>
        <div v-if="nodeCount > 0" class="graph-stats">
          <span class="stat">{{ nodeCount }} agents</span>
          <span class="stat">{{ edgeCount }} connections</span>
          <span v-if="crossEdgeCount > 0" class="stat cross-stat">{{ crossEdgeCount }} cross-scenario</span>
        </div>
      </div>
    </div>

    <div v-if="hasMultipleScenarios" class="graph-legend">
      <div v-for="(name, idx) in scenarioMap" :key="idx" class="legend-item">
        <span class="legend-swatch" :style="{ background: getScenarioColor(idx) }"></span>
        <span class="legend-label">{{ name.length > 50 ? name.slice(0, 50) + '...' : name }}</span>
      </div>
      <div class="legend-item">
        <span class="legend-line solid"></span>
        <span class="legend-label">Within scenario</span>
      </div>
      <div class="legend-item">
        <span class="legend-line dashed"></span>
        <span class="legend-label">Cross-scenario</span>
      </div>
    </div>

    <div v-if="tooltip.visible" class="graph-tooltip" :style="tooltipStyle">
      <div class="tooltip-name">{{ tooltip.name }}</div>
      <div class="tooltip-role">{{ tooltip.role }}</div>
      <div v-if="tooltip.scenario" class="tooltip-scenario">{{ tooltip.scenario }}</div>
      <div class="tooltip-stats">Actions: {{ tooltip.actionCount }} &middot; Avg Sentiment: {{ tooltip.avgSentiment }}</div>
    </div>

    <div class="live-graph-container" ref="graphContainer"></div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as d3 from 'd3'

const SCENARIO_COLORS = [
  '#2563eb', '#dc2626', '#059669', '#7c3aed', '#ea580c',
  '#0891b2', '#db2777', '#65a30d',
]

const props = defineProps({
  agentDefs: { type: Object, default: () => ({}) },
  influenceLog: { type: Array, default: () => [] },
  agentTimeline: { type: Array, default: () => [] },
  currentRound: { type: Number, default: 0 },
  title: { type: String, default: 'Influence Network' },
  scenarioMap: { type: Object, default: () => ({}) },
  agentScenarioMap: { type: Object, default: () => ({}) },
})

const graphContainer = ref(null)
const filterMode = ref('all')

let svg = null
let simulation = null
let nodeGroup = null
let linkGroup = null
let labelGroup = null
let linkLabelGroup = null
let hullGroup = null
let resizeObserver = null
let nodePositions = new Map()

const nodeCount = ref(0)
const edgeCount = ref(0)

const tooltip = reactive({
  visible: false,
  name: '',
  role: '',
  scenario: '',
  actionCount: 0,
  avgSentiment: '0.00',
  x: 0,
  y: 0,
})

const tooltipStyle = computed(() => ({
  left: tooltip.x + 'px',
  top: tooltip.y + 'px',
}))

const hasMultipleScenarios = computed(() => Object.keys(props.scenarioMap).length > 1)

const crossEdgeCount = computed(() => {
  if (!hasMultipleScenarios.value) return 0
  const counts = {}
  const agentKeys = new Set(Object.keys(props.agentDefs || {}))
  for (const entry of (props.influenceLog || [])) {
    if (!agentKeys.has(entry.from) || !agentKeys.has(entry.to)) continue
    if (entry.from === entry.to) continue
    const fromSc = props.agentScenarioMap?.[entry.from] || ''
    const toSc = props.agentScenarioMap?.[entry.to] || ''
    if (fromSc && toSc && fromSc !== toSc) {
      const key = `${entry.from}|${entry.to}`
      counts[key] = 1
    }
  }
  return Object.keys(counts).length
})

function getScenarioColor(idx) {
  return SCENARIO_COLORS[Number(idx) % SCENARIO_COLORS.length]
}

function getLabel(key) {
  return props.agentDefs?.[key]?.name || key?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || key
}

function getColor(key) {
  return props.agentDefs?.[key]?.color || '#6b7280'
}

function getScenarioForAgent(key) {
  return props.agentScenarioMap?.[key] || ''
}

function getScenarioIndexForAgent(key) {
  const sc = getScenarioForAgent(key)
  for (const [idx, name] of Object.entries(props.scenarioMap)) {
    if (name === sc) return Number(idx)
  }
  return 0
}

function computeNodes() {
  const keys = Object.keys(props.agentDefs || {})
  return keys.map(key => {
    const saved = nodePositions.get(key)
    const defn = props.agentDefs[key]
    const reach = defn?.reach_multiplier || defn?.reach || 1.0
    return {
      id: key,
      label: getLabel(key),
      color: getColor(key),
      scenario: getScenarioForAgent(key),
      scenarioIndex: getScenarioIndexForAgent(key),
      radius: Math.max(10, Math.min(24, 10 + (reach - 0.5) * 3)),
      x: saved?.x,
      y: saved?.y,
      vx: saved?.vx || 0,
      vy: saved?.vy || 0,
    }
  })
}

function computeLinks() {
  const counts = {}
  const agentKeys = new Set(Object.keys(props.agentDefs || {}))
  for (const entry of (props.influenceLog || [])) {
    if (!agentKeys.has(entry.from) || !agentKeys.has(entry.to)) continue
    if (entry.from === entry.to) continue
    const key = `${entry.from}|${entry.to}`
    counts[key] = (counts[key] || 0) + 1
  }
  return Object.entries(counts).map(([key, count]) => {
    const [source, target] = key.split('|')
    const fromSc = getScenarioForAgent(source)
    const toSc = getScenarioForAgent(target)
    const cross = hasMultipleScenarios.value && fromSc && toSc && fromSc !== toSc
    return { source, target, count, cross, fromScenarioIdx: getScenarioIndexForAgent(source) }
  })
}

function shouldShowNode(node) {
  if (filterMode.value === 'all') return true
  if (filterMode.value === 'cross') {
    // Show nodes that have at least one cross-scenario connection
    return computeLinks().some(l =>
      l.cross && (
        (typeof l.source === 'object' ? l.source.id : l.source) === node.id ||
        (typeof l.target === 'object' ? l.target.id : l.target) === node.id
      )
    )
  }
  // Filter by specific scenario index
  return node.scenarioIndex === Number(filterMode.value)
}

function shouldShowLink(link) {
  if (filterMode.value === 'all') return true
  if (filterMode.value === 'cross') return link.cross
  const idx = Number(filterMode.value)
  const sourceIdx = typeof link.source === 'object' ? link.source.scenarioIndex : getScenarioIndexForAgent(link.source)
  const targetIdx = typeof link.target === 'object' ? link.target.scenarioIndex : getScenarioIndexForAgent(link.target)
  return sourceIdx === idx || targetIdx === idx
}

function initGraph() {
  const container = graphContainer.value
  if (!container) return

  d3.select(container).selectAll('*').remove()

  const width = container.clientWidth || 600
  const height = container.clientHeight || 500

  svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  const defs = svg.append('defs')

  // Within-scenario arrowhead
  defs.append('marker')
    .attr('id', 'arrow-within')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 22)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#94a3b8')

  // Cross-scenario arrowhead
  defs.append('marker')
    .attr('id', 'arrow-cross')
    .attr('viewBox', '0 -5 10 10')
    .attr('refX', 22)
    .attr('refY', 0)
    .attr('markerWidth', 6)
    .attr('markerHeight', 6)
    .attr('orient', 'auto')
    .append('path')
    .attr('d', 'M0,-5L10,0L0,5')
    .attr('fill', '#f59e0b')

  hullGroup = svg.append('g').attr('class', 'hulls')
  linkGroup = svg.append('g').attr('class', 'links')
  linkLabelGroup = svg.append('g').attr('class', 'link-labels')
  nodeGroup = svg.append('g').attr('class', 'nodes')
  labelGroup = svg.append('g').attr('class', 'labels')

  const forces = {
    link: d3.forceLink().id(d => d.id).distance(120),
    charge: d3.forceManyBody().strength(-320),
    center: d3.forceCenter(width / 2, height / 2),
    collision: d3.forceCollide(36),
  }

  simulation = d3.forceSimulation()
    .force('link', forces.link)
    .force('charge', forces.charge)
    .force('center', forces.center)
    .force('collision', forces.collision)
    .on('tick', tick)

  // Scenario clustering forces (weak)
  if (hasMultipleScenarios.value) {
    const scenarioCount = Object.keys(props.scenarioMap).length
    simulation
      .force('x', d3.forceX(d => {
        const col = d.scenarioIndex % scenarioCount
        return (width / (scenarioCount + 1)) * (col + 1)
      }).strength(0.03))
      .force('y', d3.forceY(height / 2).strength(0.01))
  }

  updateGraph()
}

function tick() {
  const container = graphContainer.value
  if (!container || !svg) return
  const width = container.clientWidth || 600
  const height = container.clientHeight || 500

  nodeGroup.selectAll('circle.node-circle').each(d => {
    d.x = Math.max(28, Math.min(width - 28, d.x))
    d.y = Math.max(28, Math.min(height - 28, d.y))
    nodePositions.set(d.id, { x: d.x, y: d.y, vx: d.vx, vy: d.vy })
  })

  linkGroup.selectAll('line')
    .attr('x1', d => (typeof d.source === 'object' ? d.source.x : 0))
    .attr('y1', d => (typeof d.source === 'object' ? d.source.y : 0))
    .attr('x2', d => (typeof d.target === 'object' ? d.target.x : 0))
    .attr('y2', d => (typeof d.target === 'object' ? d.target.y : 0))

  linkLabelGroup.selectAll('text')
    .attr('x', d => {
      const sx = typeof d.source === 'object' ? d.source.x : 0
      const tx = typeof d.target === 'object' ? d.target.x : 0
      return (sx + tx) / 2
    })
    .attr('y', d => {
      const sy = typeof d.source === 'object' ? d.source.y : 0
      const ty = typeof d.target === 'object' ? d.target.y : 0
      return (sy + ty) / 2 - 5
    })

  nodeGroup.selectAll('circle.node-circle')
    .attr('cx', d => d.x).attr('cy', d => d.y)
  nodeGroup.selectAll('circle.node-ring')
    .attr('cx', d => d.x).attr('cy', d => d.y)

  labelGroup.selectAll('text')
    .attr('x', d => d.x).attr('y', d => d.y)

  // Update convex hulls
  if (hasMultipleScenarios.value && hullGroup) {
    drawHulls()
  }
}

function drawHulls() {
  if (!hullGroup) return

  const scenarioGroups = {}
  nodeGroup.selectAll('circle.node-circle').each(d => {
    if (!shouldShowNode(d)) return
    const sc = d.scenarioIndex
    if (!scenarioGroups[sc]) scenarioGroups[sc] = []
    scenarioGroups[sc].push([d.x, d.y])
  })

  hullGroup.selectAll('path').remove()

  for (const [idx, points] of Object.entries(scenarioGroups)) {
    if (points.length < 3) continue
    const hull = d3.polygonHull(points)
    if (!hull) continue

    const color = getScenarioColor(idx)
    hullGroup.append('path')
      .attr('d', 'M' + hull.map(p => p.join(',')).join('L') + 'Z')
      .attr('fill', color)
      .attr('fill-opacity', 0.05)
      .attr('stroke', color)
      .attr('stroke-opacity', 0.15)
      .attr('stroke-width', 1.5)
      .attr('rx', 20)
  }
}

function updateGraph() {
  if (!svg || !simulation) return

  const newNodes = computeNodes()
  const newLinks = computeLinks()

  const container = graphContainer.value
  const width = container?.clientWidth || 600
  const height = container?.clientHeight || 500

  for (const nn of newNodes) {
    if (nn.x == null) {
      if (hasMultipleScenarios.value) {
        const scenarioCount = Object.keys(props.scenarioMap).length
        const col = nn.scenarioIndex % scenarioCount
        nn.x = (width / (scenarioCount + 1)) * (col + 1) + (Math.random() - 0.5) * 80
        nn.y = height / 2 + (Math.random() - 0.5) * 120
      } else {
        nn.x = width / 2 + (Math.random() - 0.5) * 120
        nn.y = height / 2 + (Math.random() - 0.5) * 120
      }
    }
  }

  nodeCount.value = newNodes.filter(shouldShowNode).length
  edgeCount.value = newLinks.filter(shouldShowLink).length

  const maxCount = Math.max(...newLinks.map(l => l.count), 1)

  // --- Links ---
  linkGroup.selectAll('line').remove()
  linkGroup.selectAll('line')
    .data(newLinks, d => `${d.source}|${d.target}`)
    .enter().append('line')
    .attr('stroke', d => {
      if (d.cross) return '#f59e0b'
      if (hasMultipleScenarios.value) return getScenarioColor(d.fromScenarioIdx)
      return '#94a3b8'
    })
    .attr('stroke-opacity', d => d.cross ? 0.7 : 0.5)
    .attr('stroke-width', d => 1 + (d.count / maxCount) * 3)
    .attr('stroke-dasharray', d => d.cross ? '5,3' : null)
    .attr('marker-end', d => d.cross ? 'url(#arrow-cross)' : 'url(#arrow-within)')
    .style('display', d => shouldShowLink(d) ? null : 'none')

  // --- Link labels ---
  linkLabelGroup.selectAll('text').remove()
  linkLabelGroup.selectAll('text')
    .data(newLinks.filter(l => l.count > 1), d => `${d.source}|${d.target}`)
    .enter().append('text')
    .text(d => `${d.count}x`)
    .attr('font-size', 9)
    .attr('fill', d => d.cross ? '#f59e0b' : '#94a3b8')
    .attr('text-anchor', 'middle')
    .style('display', d => shouldShowLink(d) ? null : 'none')

  // --- Nodes ---
  const nodeSel = nodeGroup.selectAll('g.node-group').data(newNodes, d => d.id)

  nodeSel.exit().transition().duration(300).attr('opacity', 0).remove()

  const nodeEnter = nodeSel.enter().append('g')
    .attr('class', 'node-group')
    .call(d3.drag()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x; d.fy = d.y
      })
      .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null; d.fy = null
      })
    )
    .on('mouseenter', (event, d) => {
      showTooltip(event, d)
      highlightConnections(d)
    })
    .on('mouseleave', () => {
      hideTooltip()
      resetHighlight()
    })

  // Scenario ring (outer circle)
  nodeEnter.append('circle')
    .attr('class', 'node-ring')
    .attr('r', 0)
    .attr('fill', 'none')
    .attr('stroke', d => hasMultipleScenarios.value ? getScenarioColor(d.scenarioIndex) : '#fff')
    .attr('stroke-width', hasMultipleScenarios.value ? 3 : 2)
    .transition().duration(600).ease(d3.easeElasticOut.amplitude(1).period(0.5))
    .attr('r', d => d.radius + 3)

  // Agent circle (inner)
  nodeEnter.append('circle')
    .attr('class', 'node-circle')
    .attr('r', 0)
    .attr('fill', d => d.color)
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .transition().duration(600).ease(d3.easeElasticOut.amplitude(1).period(0.5))
    .attr('r', d => d.radius)

  // Update existing
  const merged = nodeSel.merge(nodeEnter)
  merged.select('circle.node-circle').attr('fill', d => d.color)
  merged.select('circle.node-ring')
    .attr('stroke', d => hasMultipleScenarios.value ? getScenarioColor(d.scenarioIndex) : '#fff')
  merged.style('display', d => shouldShowNode(d) ? null : 'none')

  // --- Labels ---
  const labelSel = labelGroup.selectAll('text').data(newNodes, d => d.id)

  labelSel.exit().transition().duration(300).attr('opacity', 0).remove()

  const labelEnter = labelSel.enter().append('text')
    .text(d => d.label)
    .attr('font-size', 11)
    .attr('font-weight', 600)
    .attr('fill', '#334155')
    .attr('text-anchor', 'middle')
    .attr('dy', d => -(d.radius + 8))
    .attr('opacity', 0)

  labelEnter.transition().duration(500).attr('opacity', 1)

  labelSel.merge(labelEnter)
    .text(d => d.label)
    .attr('dy', d => -(d.radius + 8))
    .style('display', d => shouldShowNode(d) ? null : 'none')

  // Restart simulation
  simulation.nodes(newNodes)
  simulation.force('link').links(newLinks)
  simulation.alpha(0.4).restart()
}

function showTooltip(event, d) {
  const container = graphContainer.value
  if (!container) return
  const rect = container.getBoundingClientRect()

  // Compute stats from influence log
  const actions = (props.influenceLog || []).filter(
    e => e.from === d.id || e.to === d.id
  )
  const sentiments = (props.influenceLog || [])
  // Get avg sentiment from rounds data (not available here, use a simple count)
  tooltip.name = d.label
  tooltip.role = props.agentDefs?.[d.id]?.role || ''
  tooltip.scenario = hasMultipleScenarios.value ? d.scenario : ''
  tooltip.actionCount = actions.length
  tooltip.avgSentiment = '—'
  tooltip.x = event.clientX - rect.left + 12
  tooltip.y = event.clientY - rect.top - 10
  tooltip.visible = true
}

function hideTooltip() {
  tooltip.visible = false
}

function highlightConnections(d) {
  const connectedIds = new Set([d.id])
  linkGroup.selectAll('line').each(function(l) {
    const sourceId = typeof l.source === 'object' ? l.source.id : l.source
    const targetId = typeof l.target === 'object' ? l.target.id : l.target
    if (sourceId === d.id || targetId === d.id) {
      connectedIds.add(sourceId)
      connectedIds.add(targetId)
      d3.select(this).attr('stroke-opacity', 1).attr('stroke-width', function() {
        return parseFloat(d3.select(this).attr('stroke-width')) + 1
      })
    } else {
      d3.select(this).attr('stroke-opacity', 0.1)
    }
  })

  nodeGroup.selectAll('g.node-group').attr('opacity', nd =>
    connectedIds.has(nd.id) ? 1 : 0.2
  )
  labelGroup.selectAll('text').attr('opacity', nd =>
    connectedIds.has(nd.id) ? 1 : 0.15
  )
}

function resetHighlight() {
  const links = computeLinks()
  const maxCount = Math.max(...links.map(l => l.count), 1)

  linkGroup.selectAll('line')
    .attr('stroke-opacity', d => d.cross ? 0.7 : 0.5)
    .attr('stroke-width', d => 1 + (d.count / maxCount) * 3)

  nodeGroup.selectAll('g.node-group').attr('opacity', 1)
  labelGroup.selectAll('text').attr('opacity', 1)
}

onMounted(() => {
  nextTick(initGraph)
  resizeObserver = new ResizeObserver(() => {
    if (!svg || !graphContainer.value) return
    const w = graphContainer.value.clientWidth || 600
    const h = graphContainer.value.clientHeight || 500
    svg.attr('width', w).attr('height', h)
    simulation?.force('center', d3.forceCenter(w / 2, h / 2))
    simulation?.alpha(0.2).restart()
  })
  if (graphContainer.value) resizeObserver.observe(graphContainer.value)
})

onUnmounted(() => {
  if (simulation) simulation.stop()
  if (resizeObserver) resizeObserver.disconnect()
})

watch([() => props.agentDefs, () => props.influenceLog, () => props.scenarioMap], () => {
  nextTick(updateGraph)
}, { deep: true })

watch(filterMode, () => {
  nextTick(updateGraph)
})
</script>

<style scoped>
.live-graph-wrapper {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  overflow: hidden; position: relative;
}
.live-graph-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 16px; border-bottom: 1px solid var(--border); flex-wrap: wrap; gap: 8px;
}
.live-graph-header h3 { font-size: 15px; font-weight: 600; margin: 0; }
.graph-controls { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.filter-select {
  padding: 4px 8px; border: 1px solid var(--border); border-radius: 6px;
  font-size: 12px; background: var(--surface); color: var(--text);
}
.graph-stats { display: flex; gap: 8px; }
.stat {
  font-size: 11px; color: var(--text-secondary); font-weight: 500;
  background: #f1f5f9; padding: 2px 8px; border-radius: 4px;
}
.cross-stat { background: #fef3c7; color: #92400e; }

.graph-legend {
  display: flex; flex-wrap: wrap; gap: 12px; padding: 8px 16px;
  border-bottom: 1px solid var(--border); background: #fafbfc;
}
.legend-item { display: flex; align-items: center; gap: 5px; font-size: 11px; color: var(--text-secondary); }
.legend-swatch { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.legend-label { white-space: nowrap; }
.legend-line {
  width: 20px; height: 0; border-top: 2px solid #94a3b8; flex-shrink: 0;
}
.legend-line.dashed { border-top-style: dashed; border-color: #f59e0b; }

.graph-tooltip {
  position: absolute; z-index: 10; pointer-events: none;
  background: rgba(15, 23, 42, 0.92); color: #fff; border-radius: 8px;
  padding: 8px 12px; font-size: 12px; line-height: 1.5;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-width: 240px;
}
.tooltip-name { font-weight: 700; font-size: 13px; }
.tooltip-role { color: #94a3b8; }
.tooltip-scenario { color: #fbbf24; font-size: 11px; margin-top: 2px; }
.tooltip-stats { margin-top: 4px; color: #cbd5e1; font-size: 11px; }

.live-graph-container {
  width: 100%; min-height: 500px; height: 500px; background: #f8fafc;
}
.live-graph-container :deep(svg) { display: block; }
</style>
