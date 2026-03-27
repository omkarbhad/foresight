<template>
  <div ref="containerRef" class="chart-container">
    <svg ref="svgRef"></svg>
    <div
      class="tooltip"
      :style="{ opacity: tooltipVisible ? 1 : 0, left: tooltipX + 'px', top: tooltipY + 'px' }"
    >
      <div class="tooltip-date">{{ tooltipData.date }}</div>
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
const tooltipVisible = ref(false)
const tooltipX = ref(0)
const tooltipY = ref(0)
const tooltipData = reactive({ date: '', count: '' })

const margin = { top: 20, right: 20, bottom: 50, left: 50 }
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
    count: +d.count,
  }))

  const x = d3
    .scaleBand()
    .domain(parsed.map((d) => d.date))
    .range([0, width])
    .padding(0.2)

  const y = d3
    .scaleLinear()
    .domain([0, d3.max(parsed, (d) => d.count) * 1.1])
    .nice()
    .range([height, 0])

  // Grid lines
  g.append('g')
    .attr('class', 'grid')
    .call(d3.axisLeft(y).ticks(5).tickSize(-width).tickFormat(''))

  // Compute CSS custom property value for --primary, fallback to a default
  const primaryColor =
    getComputedStyle(containerRef.value).getPropertyValue('--primary').trim() || '#6366f1'

  // Bars
  g.selectAll('.bar')
    .data(parsed)
    .join('rect')
    .attr('class', 'bar')
    .attr('x', (d) => x(d.date))
    .attr('y', (d) => y(d.count))
    .attr('width', x.bandwidth())
    .attr('height', (d) => height - y(d.count))
    .attr('fill', primaryColor)
    .attr('rx', 3)
    .attr('ry', 3)
    .style('cursor', 'pointer')
    .on('mouseenter', (event, d) => {
      tooltipVisible.value = true
      const rect = containerRef.value.getBoundingClientRect()
      tooltipX.value = event.clientX - rect.left + 12
      tooltipY.value = event.clientY - rect.top - 10
      tooltipData.date = d3.timeFormat('%b %d, %Y')(d.date)
      tooltipData.count = d.count
      d3.select(event.currentTarget).attr('opacity', 0.75)
    })
    .on('mousemove', (event) => {
      const rect = containerRef.value.getBoundingClientRect()
      tooltipX.value = event.clientX - rect.left + 12
      tooltipY.value = event.clientY - rect.top - 10
    })
    .on('mouseleave', (event) => {
      tooltipVisible.value = false
      d3.select(event.currentTarget).attr('opacity', 1)
    })

  // X-axis
  const tickInterval = Math.max(1, Math.floor(parsed.length / 10))
  g.append('g')
    .attr('transform', `translate(0,${height})`)
    .call(
      d3
        .axisBottom(x)
        .tickValues(x.domain().filter((_, i) => i % tickInterval === 0))
        .tickFormat(d3.timeFormat('%b %d'))
    )
    .selectAll('text')
    .attr('transform', 'rotate(-35)')
    .style('text-anchor', 'end')
    .style('font-size', '11px')

  // Y-axis
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
    .text('Mentions')
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

.tooltip-count {
  color: #d1d5db;
}
</style>
