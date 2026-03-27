<template>
  <div class="crisis-indicator" :class="`level-${level}`">
    <div class="indicator-header">
      <div class="status-light-wrapper">
        <span class="status-light"></span>
      </div>
      <span class="status-label">{{ statusLabel }}</span>
    </div>
    <div class="indicator-body">
      <div class="indicator-detail">
        <span class="detail-label">Active Alerts</span>
        <span class="detail-value">{{ crisisCount }}</span>
      </div>
      <div class="indicator-detail">
        <span class="detail-label">Max Severity</span>
        <span class="detail-value">{{ formattedMaxScore }}</span>
      </div>
    </div>
    <div class="indicator-bar">
      <div class="bar-track">
        <div class="bar-fill" :style="barStyle"></div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CrisisIndicator',
  props: {
    crisisCount: {
      type: Number,
      required: true,
      default: 0,
    },
    maxScore: {
      type: Number,
      required: true,
      default: 0,
    },
  },
  computed: {
    level() {
      if (this.crisisCount === 0 && this.maxScore < 0.3) return 'safe';
      if (this.crisisCount <= 2 && this.maxScore < 0.7) return 'watch';
      return 'crisis';
    },
    statusLabel() {
      if (this.level === 'safe') return 'All Clear';
      if (this.level === 'watch') return 'Monitoring';
      return 'Crisis Detected';
    },
    formattedMaxScore() {
      return this.maxScore.toFixed(2);
    },
    barStyle() {
      const pct = Math.min(this.maxScore * 100, 100);
      const colorVar =
        this.level === 'safe'
          ? 'var(--success)'
          : this.level === 'watch'
            ? 'var(--warning)'
            : 'var(--danger)';
      return {
        width: `${pct}%`,
        background: colorVar,
      };
    },
  },
};
</script>

<style scoped>
.crisis-indicator {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px 24px;
  font-family: 'Inter', sans-serif;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
  transition: border-color 0.3s ease;
}

.crisis-indicator.level-safe {
  border-left: 4px solid var(--success);
}

.crisis-indicator.level-watch {
  border-left: 4px solid var(--warning);
}

.crisis-indicator.level-crisis {
  border-left: 4px solid var(--danger);
}

.indicator-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.status-light-wrapper {
  position: relative;
  width: 14px;
  height: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-light {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: block;
}

.level-safe .status-light {
  background: var(--success);
  box-shadow: 0 0 6px color-mix(in srgb, var(--success) 50%, transparent);
}

.level-watch .status-light {
  background: var(--warning);
  box-shadow: 0 0 6px color-mix(in srgb, var(--warning) 50%, transparent);
  animation: pulse-watch 2s ease-in-out infinite;
}

.level-crisis .status-light {
  background: var(--danger);
  box-shadow: 0 0 8px color-mix(in srgb, var(--danger) 60%, transparent);
  animation: pulse-crisis 1s ease-in-out infinite;
}

@keyframes pulse-watch {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes pulse-crisis {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.15); }
}

.status-label {
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
}

.level-crisis .status-label {
  color: var(--danger);
}

.indicator-body {
  display: flex;
  gap: 24px;
  margin-bottom: 16px;
}

.indicator-detail {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.detail-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.detail-value {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
}

.indicator-bar {
  margin-top: 4px;
}

.bar-track {
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease, background 0.4s ease;
}
</style>
