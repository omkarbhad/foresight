<template>
  <div ref="containerRef" class="chart-container">
    <svg ref="svgRef"></svg>
    <div
      class="tooltip"
      :style="{ opacity: tooltipVisible ? 1 : 0, left: tooltipX + 'px', top: tooltipY + 'px' }"
    >
      <div class="tooltip-label">{{ tooltipData.label }}</div>
      <div class="tooltip-value">{{ tooltipData.value }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, reactive } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
})

const containerRef = ref(null)
const svgRef = ref(null)
const tooltipVisible = ref(false)
const tooltipX = ref(0)
const tooltipY = ref(0)
const tooltipData = reactive({ label: '', value: '' })

const margin = { top: 30, right: 30, bottom: 50, left: 60 }
let resizeObserver = null

function drawChart() {
  if (!svgRef.value || !containerRef.value || !props.data.length) return

  const containerWidth = containerRef.value.clientWidth
  const containerHeight = 300
  const width = containerWidth - margin.left - margin.right
  const height = containerHeight - margin.top - margin.bottom

  const svg = d3.select(svgRef.value)
  svg.selectAll('*').remove()
  svg.attr('width', containerWidth).attr('height', containerHeight)

  const g = svg.append('g').attr('transform', `translate(${margin.left},${margin.top})`)

  const monitors = props.data.map((d) => String(d.monitor_id))

  // Normalize sentiment to a positive scale for display alongside volume
  // Volume uses left y-axis, sentiment uses right y-axis (-1 to 1)
  const maxMentions = d3.max(props.data, (d) => +d.total_mentions) || 1

  const x0 = d3.scaleBand().domain(monitors).range([0, width]).padding(0.3)

  const x1 = d3
    .scaleBand()
    .domain(['volume', 'sentiment'])
    .range([0, x0.bandwidth()])
    .padding(0.1)

  const yVolume = d3
    .scaleLinear()
    .domain([0, maxMentions * 1.15])
    .nice()
    .range([height, 0])

  const ySentiment = d3.scaleLinear().domain([-1, 1]).range([height, 0])

  const colorVolume = '#6366f1'
  const colorSentiment = '#22c55e'

  // Grid
  g.append('g')
    .attr('class', 'grid')
    .call(d3.axisLeft(yVolume).ticks(5).tickSize(-width).tickFormat(''))

  // Bars for each monitor
  const groups = g
    .selectAll('.monitor-group')
    .data(props.data)
    .join('g')
    .attr('class', 'monitor-group')
    .attr('transform', (d) => `translate(${x0(String(d.monitor_id))},0)`)

  // Volume bars
  groups
    .append('rect')
    .attr('x', x1('volume'))
    .attr('y', (d) => yVolume(+d.total_mentions))
    .attr('width', x1.bandwidth())
    .attr('height', (d) => height - yVolume(+d.total_mentions))
    .attr('fill', colorVolume)
    .attr('rx', 3)
    .attr('ry', 3)
    .style('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      showTooltip(event, `Monitor ${d.monitor_id} - Volume`, `${d.total_mentions} mentions`)
      d3.select(event.currentTarget).attr('opacity', 0.75)
    })
    .on('mousemove', (event) => moveTooltip(event))
    .on('mouseleave', (event) => {
      hideTooltip()
      d3.select(event.currentTarget).attr('opacity', 1)
    })

  // Sentiment bars (mapped to volume y-axis range for visual comparison)
  // We draw sentiment relative to the zero line at the midpoint
  const sentimentBarHeight = (d) => {
    const s = +d.avg_sentiment
    const barTop = ySentiment(Math.max(0, s))
    const barBottom = ySentiment(Math.min(0, s))
    return barBottom - barTop
  }

  groups
    .append('rect')
    .attr('x', x1('sentiment'))
    .attr('y', (d) => ySentiment(Math.max(0, +d.avg_sentiment)))
    .attr('width', x1.bandwidth())
    .attr('height', (d) => sentimentBarHeight(d))
    .attr('fill', (d) => (+d.avg_sentiment >= 0 ? '#22c55e' : '#ef4444'))
    .attr('rx', 3)
    .attr('ry', 3)
    .style('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      showTooltip(
        event,
        `Monitor ${d.monitor_id} - Sentiment`,
        `${(+d.avg_sentiment).toFixed(3)}`
      )
      d3.select(event.currentTarget).attr('opacity', 0.75)
    })
    .on('mousemove', (event) => moveTooltip(event))
    .on('mouseleave', (event) => {
      hideTooltip()
      d3.select(event.currentTarget).attr('opacity', 1)
    })

  // X-axis
  g.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(d3.axisBottom(x0).tickFormat((d) => `Monitor ${d}`))
    .selectAll('text')
    .style('font-size', '11px')

  // Left Y-axis (Volume)
  g.append('g')
    .call(d3.axisLeft(yVolume).ticks(5))
    .selectAll('text')
    .style('font-size', '11px')

  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('y', -margin.left + 14)
    .attr('x', -height / 2)
    .attr('text-anchor', 'middle')
    .attr('fill', colorVolume)
    .style('font-size', '12px')
    .text('Mentions')

  // Right Y-axis (Sentiment)
  g.append('g')
    .attr('transform', `translate(${width},0)`)
    .call(d3.axisRight(ySentiment).ticks(5))
    .selectAll('text')
    .style('font-size', '11px')

  g.append('text')
    .attr('transform', 'rotate(90)')
    .attr('y', -width - margin.right + 14)
    .attr('x', height / 2)
    .attr('text-anchor', 'middle')
    .attr('fill', colorSentiment)
    .style('font-size', '12px')
    .text('Sentiment')

  // Legend
  const legendData = [
    { label: 'Volume', color: colorVolume },
    { label: 'Sentiment', color: colorSentiment },
  ]

  const legend = g.append('g').attr('transform', `translate(${width - 160}, -15)`)

  legendData.forEach((item, i) => {
    const lg = legend.append('g').attr('transform', `translate(${i * 90}, 0)`)
    lg.append('rect').attr('width', 12).attr('height', 12).attr('rx', 3).attr('fill', item.color)
    lg.append('text')
      .attr('x', 16)
      .attr('y', 10)
      .style('font-size', '11px')
      .style('fill', '#6b7280')
      .text(item.label)
  })
}

function showTooltip(event, label, value) {
  tooltipVisible.value = true
  const rect = containerRef.value.getBoundingClientRect()
  tooltipX.value = event.clientX - rect.left + 12
  tooltipY.value = event.clientY - rect.top - 10
  tooltipData.label = label
  tooltipData.value = value
}

function moveTooltip(event) {
  const rect = containerRef.value.getBoundingClientRect()
  tooltipX.value = event.clientX - rect.left + 12
  tooltipY.value = event.clientY - rect.top - 10
}

function hideTooltip() {
  tooltipVisible.value = false
}

onMounted(() => {
  drawChart()
  resizeObserver = new ResizeObserver(() => drawChart())
  if (containerRef.value) resizeObserver.observe(containerRef.value)
})

onBeforeUnmount(() => {
  if (resizeObserver) resizeObserver.disconnect()
})

watch(() => props.data, drawChart, { deep: true })
</script>

<style scoped>
.chart-container {
  position: relative;
  width: 100%;
  height: 300px;
}

.chart-container svg {
  display: block;
}

.chart-container :deep(.grid line) {
  stroke: #e5e7eb;
  stroke-opacity: 0.5;
}

.chart-container :deep(.grid .domain) {
  stroke: none;
}

.chart-container :deep(.domain) {
  stroke: #d1d5db;
}

.chart-container :deep(.tick line) {
  stroke: #d1d5db;
}

.tooltip {
  position: absolute;
  pointer-events: none;
  background: rgba(17, 24, 39, 0.9);
  color: #f9fafb;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  line-height: 1.5;
  transition: opacity 0.15s ease;
  white-space: nowrap;
  z-index: 10;
}

.tooltip-label {
  font-weight: 600;
  margin-bottom: 2px;
}

.tooltip-value {
  color: #d1d5db;
}
</style>
