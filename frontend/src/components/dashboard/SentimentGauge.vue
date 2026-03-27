<template>
  <div class="sentiment-gauge">
    <div class="gauge-label">{{ label }}</div>
    <div class="gauge-container">
      <div class="gauge-track">
        <div class="gauge-fill" :style="fillStyle"></div>
        <div class="gauge-needle" :style="needleStyle"></div>
      </div>
      <div class="gauge-scale">
        <span class="scale-label scale-neg">-1</span>
        <span class="scale-label scale-zero">0</span>
        <span class="scale-label scale-pos">+1</span>
      </div>
    </div>
    <div class="gauge-value" :style="{ color: valueColor }">
      {{ formattedValue }}
    </div>
    <div class="gauge-description">{{ sentimentLabel }}</div>
  </div>
</template>

<script>
export default {
  name: 'SentimentGauge',
  props: {
    value: {
      type: Number,
      required: true,
      validator: (v) => v >= -1 && v <= 1,
    },
    label: {
      type: String,
      required: true,
    },
  },
  computed: {
    clampedValue() {
      return Math.max(-1, Math.min(1, this.value));
    },
    percentage() {
      return ((this.clampedValue + 1) / 2) * 100;
    },
    fillStyle() {
      return {
        width: `${this.percentage}%`,
        background: this.fillGradient,
      };
    },
    fillGradient() {
      if (this.clampedValue < -0.3) return 'var(--danger)';
      if (this.clampedValue < 0.3) return 'var(--warning)';
      return 'var(--success)';
    },
    needleStyle() {
      return {
        left: `${this.percentage}%`,
      };
    },
    valueColor() {
      if (this.clampedValue < -0.3) return 'var(--danger)';
      if (this.clampedValue < 0.3) return 'var(--warning)';
      return 'var(--success)';
    },
    formattedValue() {
      const sign = this.clampedValue > 0 ? '+' : '';
      return `${sign}${this.clampedValue.toFixed(2)}`;
    },
    sentimentLabel() {
      if (this.clampedValue <= -0.6) return 'Very Negative';
      if (this.clampedValue <= -0.3) return 'Negative';
      if (this.clampedValue < 0.3) return 'Neutral';
      if (this.clampedValue < 0.6) return 'Positive';
      return 'Very Positive';
    },
  },
};
</script>

<style scoped>
.sentiment-gauge {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  text-align: center;
}

.gauge-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 16px;
}

.gauge-container {
  margin-bottom: 12px;
}

.gauge-track {
  position: relative;
  height: 10px;
  background: var(--border);
  border-radius: 5px;
  overflow: visible;
}

.gauge-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.6s ease, background 0.4s ease;
}

.gauge-needle {
  position: absolute;
  top: 50%;
  width: 4px;
  height: 22px;
  background: var(--text);
  border-radius: 2px;
  transform: translate(-50%, -50%);
  transition: left 0.6s ease;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.gauge-scale {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
}

.scale-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--text-secondary);
}

.gauge-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 4px;
  transition: color 0.4s ease;
}

.gauge-description {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}
</style>
