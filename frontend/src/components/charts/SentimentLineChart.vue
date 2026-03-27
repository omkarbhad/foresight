<template>
  <div ref="containerRef" class="chart-container">
    <svg ref="svgRef"></svg>
    <div
      ref="tooltipRef"
      class="tooltip"
      :style="{ opacity: tooltipVisible ? 1 : 0, left: tooltipX + 'px', top: tooltipY + 'px' }"
    >
      <div class="tooltip-date">{{ tooltipData.date }}</div>
      <div class="tooltip-sentiment">Sentiment: {{ tooltipData.sentiment }}</div>
      <div class="tooltip-count">Mentions: {{ tooltipData.count }}</div>
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
const tooltipRef = ref(null)
const tooltipVisible = ref(false)
const tooltipX = ref(0)
const tooltipY = ref(0)
const tooltipData = reactive({ date: '', sentiment: '', count: '' })

const margin = { top: 20, right: 30, bottom: 40, left: 50 }
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

  const parsed = props.data.map((d) => ({
    date: new Date(d.date),
    avg_sentiment: +d.avg_sentiment,
    count: +d.count,
  }))

  const x = d3
    .scaleTime()
    .domain(d3.extent(parsed, (d) => d.date))
    .range([0, width])

  const y = d3.scaleLinear().domain([-1, 1]).range([height, 0])

  // Grid lines
  g.append('g')
    .attr('class', 'grid')
    .call(d3.axisLeft(y).ticks(5).tickSize(-width).tickFormat(''))

  // Zero line
  g.append('line')
    .attr('x1', 0)
    .attr('x2', width)
    .attr('y1', y(0))
    .attr('y2', y(0))
    .attr('stroke', '#888')
    .attr('stroke-dasharray', '4,4')
    .attr('stroke-width', 1)

  // Gradient definition for the line
  const defs = svg.append('defs')
  const gradient = defs
    .append('linearGradient')
    .attr('id', 'sentiment-gradient')
    .attr('gradientUnits', 'userSpaceOnUse')
    .attr('x1', 0)
    .attr('y1', y(1))
    .attr('x2', 0)
    .attr('y2', y(-1))

  gradient.append('stop').attr('offset', '0%').attr('stop-color', '#22c55e')
  gradient.append('stop').attr('offset', '50%').attr('stop-color', '#eab308')
  gradient.append('stop').attr('offset', '100%').attr('stop-color', '#ef4444')

  // Area fill
  const area = d3
    .area()
    .x((d) => x(d.date))
    .y0(y(0))
    .y1((d) => y(d.avg_sentiment))
    .curve(d3.curveMonotoneX)

  const areaGradient = defs
    .append('linearGradient')
    .attr('id', 'area-gradient')
    .attr('gradientUnits', 'userSpaceOnUse')
    .attr('x1', 0)
    .attr('y1', y(1))
    .attr('x2', 0)
    .attr('y2', y(-1))

  areaGradient.append('stop').attr('offset', '0%').attr('stop-color', '#22c55e').attr('stop-opacity', 0.15)
  areaGradient.append('stop').attr('offset', '50%').attr('stop-color', '#eab308').attr('stop-opacity', 0.05)
  areaGradient.append('stop').attr('offset', '100%').attr('stop-color', '#ef4444').attr('stop-opacity', 0.15)

  g.append('path').datum(parsed).attr('fill', 'url(#area-gradient)').attr('d', area)

  // Line
  const line = d3
    .line()
    .x((d) => x(d.date))
    .y((d) => y(d.avg_sentiment))
    .curve(d3.curveMonotoneX)

  g.append('path')
    .datum(parsed)
    .attr('fill', 'none')
    .attr('stroke', 'url(#sentiment-gradient)')
    .attr('stroke-width', 2.5)
    .attr('d', line)

  // Dots
  g.selectAll('.dot')
    .data(parsed)
    .join('circle')
    .attr('class', 'dot')
    .attr('cx', (d) => x(d.date))
    .attr('cy', (d) => y(d.avg_sentiment))
    .attr('r', 4)
    .attr('fill', (d) => {
      if (d.avg_sentiment > 0.2) return '#22c55e'
      if (d.avg_sentiment < -0.2) return '#ef4444'
      return '#eab308'
    })
    .attr('stroke', '#fff')
    .attr('stroke-width', 1.5)
    .style('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      tooltipVisible.value = true
      const rect = containerRef.value.getBoundingClientRect()
      tooltipX.value = event.clientX - rect.left + 12
      tooltipY.value = event.clientY - rect.top - 10
      tooltipData.date = d3.timeFormat('%b %d, %Y')(d.date)
      tooltipData.sentiment = d.avg_sentiment.toFixed(3)
      tooltipData.count = d.count
      d3.select(event.currentTarget).attr('r', 6)
    })
    .on('mouseleave', (event) => {
      tooltipVisible.value = false
      d3.select(event.currentTarget).attr('r', 4)
    })

  // Axes
  g.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(
      d3
        .axisBottom(x)
        .ticks(Math.min(parsed.length, 8))
        .tickFormat(d3.timeFormat('%b %d'))
    )
    .selectAll('text')
    .attr('transform', 'rotate(-30)')
    .style('text-anchor', 'end')
    .style('font-size', '11px')

  g.append('g')
    .call(d3.axisLeft(y).ticks(5))
    .selectAll('text')
    .style('font-size', '11px')

  // Y-axis label
  g.append('text')
    .attr('transform', 'rotate(-90)')
    .attr('y', -margin.left + 14)
    .attr('x', -height / 2)
    .attr('text-anchor', 'middle')
    .attr('fill', '#888')
    .style('font-size', '12px')
    .text('Sentiment')
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

.tooltip-date {
  font-weight: 600;
  margin-bottom: 2px;
}

.tooltip-sentiment,
.tooltip-count {
  color: #d1d5db;
}
</style>
