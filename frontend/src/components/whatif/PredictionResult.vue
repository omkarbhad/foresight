<template>
  <div class="prediction-result">
    <!-- Loading state -->
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p class="loading-text">Analyzing scenario and generating predictions...</p>
    </div>

    <!-- Result content -->
    <template v-else-if="prediction">
      <h2 class="result-title">Prediction Results</h2>

      <!-- Key metrics row -->
      <div class="metrics-row">
        <!-- Sentiment shift gauge -->
        <div class="metric-box">
          <span class="metric-label">Sentiment Shift</span>
          <div class="gauge">
            <svg viewBox="0 0 120 70" class="gauge-svg">
              <path
                d="M10 60 A50 50 0 0 1 110 60"
                fill="none"
                stroke="var(--border)"
                stroke-width="8"
                stroke-linecap="round"
              />
              <path
                d="M10 60 A50 50 0 0 1 110 60"
                fill="none"
                :stroke="sentimentColor"
                stroke-width="8"
                stroke-linecap="round"
                :stroke-dasharray="gaugeDash"
              />
            </svg>
            <span class="gauge-value" :style="{ color: sentimentColor }">
              {{ sentimentLabel }}
            </span>
          </div>
        </div>

        <!-- Volume change -->
        <div class="metric-box">
          <span class="metric-label">Volume Change</span>
          <div class="metric-big" :class="volumeClass">
            {{ volumeSign }}{{ prediction.volume_change }}%
          </div>
        </div>

        <!-- Crisis probability -->
        <div class="metric-box">
          <span class="metric-label">Crisis Probability</span>
          <div class="crisis-bar-container">
            <div
              class="crisis-bar"
              :style="{ width: crisisPct + '%', background: crisisColor }"
            ></div>
          </div>
          <span class="crisis-value" :style="{ color: crisisColor }">
            {{ crisisPct }}%
          </span>
        </div>
      </div>

      <!-- Timeline -->
      <div v-if="prediction.timeline" class="section">
        <h3 class="section-title">Expected Timeline</h3>
        <p class="section-text">{{ prediction.timeline }}</p>
      </div>

      <!-- Key risks -->
      <div v-if="prediction.key_risks && prediction.key_risks.length" class="section">
        <h3 class="section-title">Key Risks</h3>
        <ul class="item-list item-list--danger">
          <li v-for="(risk, i) in prediction.key_risks" :key="'risk-' + i" class="item">
            <span class="item-dot"></span>
            {{ risk }}
          </li>
        </ul>
      </div>

      <!-- Opportunities -->
      <div v-if="prediction.opportunities && prediction.opportunities.length" class="section">
        <h3 class="section-title">Opportunities</h3>
        <ul class="item-list item-list--success">
          <li v-for="(opp, i) in prediction.opportunities" :key="'opp-' + i" class="item">
            <span class="item-dot"></span>
            {{ opp }}
          </li>
        </ul>
      </div>

      <!-- Recommended actions -->
      <div v-if="prediction.recommended_actions && prediction.recommended_actions.length" class="section">
        <h3 class="section-title">Recommended Actions</h3>
        <ol class="action-list">
          <li v-for="(action, i) in prediction.recommended_actions" :key="'act-' + i" class="action-item">
            <span class="action-number">{{ i + 1 }}</span>
            <span class="action-text">{{ action }}</span>
          </li>
        </ol>
      </div>

      <!-- Narrative prediction -->
      <div v-if="prediction.narrative" class="section section--narrative">
        <h3 class="section-title">Narrative Prediction</h3>
        <p class="narrative-text">{{ prediction.narrative }}</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  prediction: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
})

// Sentiment: expected range roughly -1 to 1
const sentimentColor = computed(() => {
  const s = props.prediction?.sentiment_shift ?? 0
  if (s > 0.1) return 'var(--success)'
  if (s < -0.1) return 'var(--danger)'
  return 'var(--warning)'
})

const sentimentLabel = computed(() => {
  const s = props.prediction?.sentiment_shift ?? 0
  const sign = s > 0 ? '+' : ''
  return sign + s.toFixed(2)
})

// Gauge dash: arc length ~157; map sentiment_shift from [-1,1] to [0,157]
const gaugeDash = computed(() => {
  const total = 157
  const s = props.prediction?.sentiment_shift ?? 0
  const pct = Math.min(1, Math.max(0, (s + 1) / 2))
  const filled = pct * total
  return `${filled} ${total}`
})

// Volume
const volumeSign = computed(() => {
  const v = props.prediction?.volume_change ?? 0
  return v > 0 ? '+' : ''
})

const volumeClass = computed(() => {
  const v = props.prediction?.volume_change ?? 0
  if (v > 0) return 'metric-big--up'
  if (v < 0) return 'metric-big--down'
  return ''
})

// Crisis
const crisisPct = computed(() => {
  const c = props.prediction?.crisis_probability ?? 0
  return Math.round(c * 100)
})

const crisisColor = computed(() => {
  const p = crisisPct.value
  if (p >= 70) return 'var(--danger)'
  if (p >= 40) return 'var(--warning)'
  return 'var(--success)'
})
</script>

<style scoped>
.prediction-result {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 32px;
  font-family: 'Inter', sans-serif;
}

/* Loading */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 0;
  gap: 16px;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 3px solid var(--border);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* Title */
.result-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 24px;
}

/* Metrics row */
.metrics-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.metric-box {
  background: color-mix(in srgb, var(--neutral) 5%, transparent);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}

.metric-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

/* Gauge */
.gauge {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.gauge-svg {
  width: 100px;
  height: 58px;
}

.gauge-value {
  font-size: 22px;
  font-weight: 700;
  margin-top: -4px;
}

/* Volume */
.metric-big {
  font-size: 28px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.3;
}

.metric-big--up {
  color: var(--success);
}

.metric-big--down {
  color: var(--danger);
}

/* Crisis bar */
.crisis-bar-container {
  width: 100%;
  height: 8px;
  background: var(--border);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.crisis-bar {
  height: 100%;
  border-radius: 4px;
  transition: width 0.6s ease;
}

.crisis-value {
  font-size: 22px;
  font-weight: 700;
}

/* Sections */
.section {
  margin-bottom: 24px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 10px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.section-text {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
}

/* Item lists (risks / opportunities) */
.item-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  font-size: 14px;
  color: var(--text);
  line-height: 1.5;
}

.item-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 6px;
}

.item-list--danger .item-dot {
  background: var(--danger);
}

.item-list--success .item-dot {
  background: var(--success);
}

/* Action list */
.action-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.action-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-size: 14px;
  color: var(--text);
  line-height: 1.5;
}

.action-number {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary);
  color: white;
  font-size: 12px;
  font-weight: 700;
  border-radius: 50%;
  flex-shrink: 0;
}

.action-text {
  padding-top: 2px;
}

/* Narrative */
.section--narrative {
  background: color-mix(in srgb, var(--primary-light) 8%, transparent);
  border: 1px solid color-mix(in srgb, var(--primary) 20%, transparent);
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 0;
}

.narrative-text {
  font-size: 14px;
  color: var(--text);
  line-height: 1.7;
  margin: 0;
}

/* Responsive */
@media (max-width: 640px) {
  .metrics-row {
    grid-template-columns: 1fr;
  }
}
</style>
