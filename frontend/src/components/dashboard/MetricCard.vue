<template>
  <div class="metric-card" :style="cardStyle">
    <div class="metric-label">{{ label }}</div>
    <div class="metric-value">{{ formattedValue }}</div>
    <div v-if="trend !== undefined && trend !== null" class="metric-trend" :class="trendClass">
      <span class="trend-arrow">{{ trendArrow }}</span>
      <span class="trend-value">{{ Math.abs(trend) }}%</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'MetricCard',
  props: {
    label: {
      type: String,
      required: true,
    },
    value: {
      type: [String, Number],
      required: true,
    },
    trend: {
      type: Number,
      default: undefined,
    },
    color: {
      type: String,
      default: undefined,
    },
  },
  computed: {
    formattedValue() {
      if (typeof this.value === 'number') {
        return this.value.toLocaleString();
      }
      return this.value;
    },
    trendClass() {
      if (this.trend > 0) return 'trend-up';
      if (this.trend < 0) return 'trend-down';
      return 'trend-neutral';
    },
    trendArrow() {
      if (this.trend > 0) return '\u2191';
      if (this.trend < 0) return '\u2193';
      return '\u2192';
    },
    cardStyle() {
      if (!this.color) return {};
      return {
        '--card-accent': this.color,
      };
    },
  },
};
</script>

<style scoped>
.metric-card {
  --card-accent: var(--primary);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
  border-top: 3px solid var(--card-accent);
}

.metric-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
  transform: translateY(-1px);
}

.metric-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--text);
  line-height: 1.2;
  margin-bottom: 8px;
}

.metric-trend {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 6px;
}

.trend-up {
  color: var(--success);
  background: color-mix(in srgb, var(--success) 12%, transparent);
}

.trend-down {
  color: var(--danger);
  background: color-mix(in srgb, var(--danger) 12%, transparent);
}

.trend-neutral {
  color: var(--text-secondary);
  background: color-mix(in srgb, var(--neutral) 12%, transparent);
}

.trend-arrow {
  font-size: 14px;
}
</style>
