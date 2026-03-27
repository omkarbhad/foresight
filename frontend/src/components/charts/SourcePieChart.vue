<template>
  <div ref="containerRef" class="chart-container">
    <svg ref="svgRef"></svg>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import * as d3 from 'd3'

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
})

const containerRef = ref(null)
const svgRef = ref(null)

const sourceColors = {
  news: '#3b82f6',
  reddit: '#f97316',
  twitter: '#06b6d4',
  facebook: '#8b5cf6',
  youtube: '#ef4444',
  blog: '#10b981',
  forum: '#eab308',
}

const fallbackColors = d3.schemeTableau10
let resizeObserver = null

function getColor(source, i) {
  const key = source.toLowerCase()
  return sourceColors[key] || fallbackColors[i % fallbackColors.length]
}

function drawChart() {
  if (!svgRef.value || !containerRef.value || !props.data.length) return

  const containerWidth = containerRef.value.clientWidth
  const containerHeight = 300
  const radius = Math.min(containerWidth, containerHeight) / 2 - 30

  const svg = d3.select(svgRef.value)
  svg.selectAll('*').remove()
  svg.attr('width', containerWidth).attr('height', containerHeight)

  const g = svg.append('g').attr('transform', `translate(${containerWidth / 2},${containerHeight / 2})`)

  const total = d3.sum(props.data, (d) => +d.count)

  const pie = d3
    .pie()
    .value((d) => +d.count)
    .sort(null)
    .padAngle(0.02)

  const arc = d3
    .arc()
    .innerRadius(radius * 0.55)
    .outerRadius(radius)
    .cornerRadius(4)

  const arcHover = d3
    .arc()
    .innerRadius(radius * 0.55)
    .outerRadius(radius + 8)
    .cornerRadius(4)

  const labelArc = d3
    .arc()
    .innerRadius(radius * 0.8)
    .outerRadius(radius * 0.8)

  const arcs = pie(props.data)

  // Slices
  g.selectAll('.slice')
    .data(arcs)
    .join('path')
    .attr('class', 'slice')
    .attr('d', arc)
    .attr('fill', (d, i) => getColor(d.data.source, i))
    .attr('stroke', '#fff')
    .attr('stroke-width', 2)
    .style('cursor', 'pointer')
    .on('mouseenter', function (event, d) {
      d3.select(this).transition().duration(150).attr('d', arcHover)
    })
    .on('mouseleave', function () {
      d3.select(this).transition().duration(150).attr('d', arc)
    })

  // Labels
  g.selectAll('.label')
    .data(arcs)
    .join('text')
    .attr('class', 'label')
    .attr('transform', (d) => `translate(${labelArc.centroid(d)})`)
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.2em')
    .style('font-size', '12px')
    .style('font-weight', '600')
    .style('fill', '#fff')
    .style('pointer-events', 'none')
    .text((d) => {
      const pct = ((d.data.count / total) * 100).toFixed(0)
      return pct >= 5 ? d.data.source : ''
    })

  // Percentages
  g.selectAll('.pct')
    .data(arcs)
    .join('text')
    .attr('class', 'pct')
    .attr('transform', (d) => `translate(${labelArc.centroid(d)})`)
    .attr('text-anchor', 'middle')
    .attr('dy', '1em')
    .style('font-size', '11px')
    .style('fill', 'rgba(255,255,255,0.85)')
    .style('pointer-events', 'none')
    .text((d) => {
      const pct = ((d.data.count / total) * 100).toFixed(1)
      return pct >= 5 ? `${pct}%` : ''
    })

  // Legend
  const legend = svg
    .append('g')
    .attr('transform', `translate(${containerWidth - 120}, 20)`)

  const legendItems = legend
    .selectAll('.legend-item')
    .data(props.data)
    .join('g')
    .attr('class', 'legend-item')
    .attr('transform', (_, i) => `translate(0, ${i * 22})`)

  legendItems
    .append('rect')
    .attr('width', 12)
    .attr('height', 12)
    .attr('rx', 3)
    .attr('fill', (d, i) => getColor(d.source, i))

  legendItems
    .append('text')
    .attr('x', 18)
    .attr('y', 10)
    .style('font-size', '11px')
    .style('fill', '#6b7280')
    .text((d) => {
      const pct = ((d.count / total) * 100).toFixed(1)
      return `${d.source} (${pct}%)`
    })

  // Center total
  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '-0.2em')
    .style('font-size', '24px')
    .style('font-weight', '700')
    .style('fill', '#374151')
    .text(total.toLocaleString())

  g.append('text')
    .attr('text-anchor', 'middle')
    .attr('dy', '1.2em')
    .style('font-size', '11px')
    .style('fill', '#9ca3af')
    .text('Total Mentions')
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
</style>
