<template>
  <div class="round-metrics">
    <div class="metric">
      <span class="metric-label">Sentiment</span>
      <span class="metric-value" :class="sentimentClass">{{ metrics.avg_sentiment?.toFixed(2) }}</span>
      <div class="metric-bar">
        <div class="bar-fill sentiment-bar" :style="sentimentBarStyle"></div>
      </div>
    </div>
    <div class="metric">
      <span class="metric-label">Volume</span>
      <span class="metric-value">{{ metrics.total_volume }}</span>
    </div>
    <div class="metric" v-if="metrics.round_volume !== undefined">
      <span class="metric-label">This round</span>
      <span class="metric-value">+{{ metrics.round_volume }}</span>
    </div>
    <div v-if="metrics.cross_scenario_interactions > 0" class="metric">
      <span class="metric-label">Cross-scenario</span>
      <span class="metric-value cross">{{ metrics.cross_scenario_interactions }}</span>
    </div>
    <div v-if="metrics.per_scenario && Object.keys(metrics.per_scenario).length > 1" class="per-scenario-metrics">
      <div v-for="(sm, sc) in metrics.per_scenario" :key="sc" class="sc-row">
        <span class="sc-name">{{ sc.length > 25 ? sc.slice(0, 25) + '...' : sc }}</span>
        <span class="sc-sentiment" :class="scSentimentClass(sm.avg_sentiment)">{{ sm.avg_sentiment?.toFixed(2) }}</span>
        <span class="sc-volume">+{{ sm.round_volume }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ metrics: { type: Object, default: () => ({}) } })

const sentimentClass = computed(() => {
  const s = props.metrics.avg_sentiment || 0
  if (s > 0.2) return 'positive'
  if (s < -0.2) return 'negative'
  return 'neutral'
})

const sentimentBarStyle = computed(() => {
  const s = props.metrics.avg_sentiment || 0
  const pct = ((s + 1) / 2) * 100
  const color = s > 0.2 ? '#10b981' : s < -0.2 ? '#ef4444' : '#6b7280'
  return { width: pct + '%', background: color }
})

function scSentimentClass(v) {
  if (v > 0.2) return 'positive'
  if (v < -0.2) return 'negative'
  return 'neutral'
}
</script>

<style scoped>
.round-metrics {
  display: flex; flex-direction: column; gap: 10px; min-width: 140px;
  padding: 12px; background: #f8fafc; border-radius: 10px; border: 1px solid var(--border);
}
.metric { display: flex; flex-direction: column; gap: 2px; }
.metric-label { font-size: 11px; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.03em; }
.metric-value { font-size: 16px; font-weight: 700; }
.metric-value.positive { color: #10b981; }
.metric-value.negative { color: #ef4444; }
.metric-value.neutral { color: #6b7280; }
.metric-bar { height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden; }
.bar-fill { height: 100%; border-radius: 2px; transition: width 0.5s ease; }
.metric-value.cross { color: #f59e0b; }
.per-scenario-metrics {
  border-top: 1px solid var(--border); padding-top: 8px; margin-top: 4px;
}
.sc-row {
  display: flex; align-items: center; gap: 6px; font-size: 11px; margin-bottom: 3px;
}
.sc-name { flex: 1; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sc-sentiment { font-weight: 600; }
.sc-sentiment.positive { color: #10b981; }
.sc-sentiment.negative { color: #ef4444; }
.sc-sentiment.neutral { color: #6b7280; }
.sc-volume { color: var(--text-secondary); font-size: 10px; }
</style>
