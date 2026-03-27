<template>
  <div class="persona-card" :class="{ 'no-action': action.action_type === 'no_action' }">
    <div class="card-header">
      <div class="persona-badge" :style="{ color: agentColor }">
        <span class="persona-icon">{{ personaIcon }}</span>
        <span class="persona-name">{{ personaLabel }}</span>
      </div>
      <span class="action-badge">{{ action.action_type.replace(/_/g, ' ') }}</span>
    </div>
    <div v-if="action.scenario && showScenario" class="scenario-tag">
      {{ action.scenario.length > 35 ? action.scenario.slice(0, 35) + '...' : action.scenario }}
    </div>
    <div v-if="action.influenced_by?.length" class="influence-row">
      <span class="influence-label">Influenced by:</span>
      <span v-for="src in action.influenced_by" :key="src" class="influence-tag"
            :style="{ color: getColor(src), background: getColor(src) + '20' }">
        {{ getLabel(src) }}
      </span>
    </div>
    <div v-if="action.action_type !== 'no_action'" class="card-body">
      <h4 class="action-title">{{ action.title }}</h4>
      <p class="action-content" :class="{ expanded }">{{ action.content }}</p>
      <button v-if="action.content && action.content.length > 120" class="expand-btn" @click="expanded = !expanded">
        {{ expanded ? 'Show less' : 'Show more' }}
      </button>
    </div>
    <div v-else class="card-body silent">
      <p>Stayed silent this round</p>
    </div>
    <div class="card-footer">
      <span class="sentiment-chip" :class="sentimentClass">
        {{ action.sentiment_score?.toFixed(2) }}
      </span>
      <span v-if="action.reach_estimate" class="reach">
        {{ formatReach(action.reach_estimate) }} reach
      </span>
      <span class="platform-badge">{{ action.platform }}</span>
    </div>
    <div v-if="expanded && action.reasoning" class="reasoning">
      {{ action.reasoning }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  action: Object,
  agentDefs: { type: Object, default: () => ({}) },
  showScenario: { type: Boolean, default: false },
})
const expanded = ref(false)

function getLabel(key) {
  return props.agentDefs?.[key]?.name || key?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()) || 'Unknown'
}
function getColor(key) {
  return props.agentDefs?.[key]?.color || '#6b7280'
}

const personaLabel = computed(() => getLabel(props.action.persona))
const personaIcon = computed(() => props.agentDefs?.[props.action.persona]?.icon || '\u{2753}')
const agentColor = computed(() => getColor(props.action.persona))

const sentimentClass = computed(() => {
  const s = props.action.sentiment_score || 0
  if (s > 0.2) return 'positive'
  if (s < -0.2) return 'negative'
  return 'neutral'
})

function formatReach(n) {
  if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return n.toString()
}
</script>

<style scoped>
.persona-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
  padding: 14px; min-width: 240px; max-width: 300px; flex-shrink: 0;
  transition: transform 0.15s;
}
.persona-card:hover { transform: translateY(-1px); }
.persona-card.no-action { opacity: 0.5; }
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.persona-badge {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; font-weight: 600;
}
.persona-icon { font-size: 16px; }
.action-badge {
  font-size: 11px; padding: 2px 8px; border-radius: 6px;
  background: #f1f5f9; color: var(--text-secondary); text-transform: capitalize;
}
.action-title { font-size: 14px; font-weight: 600; margin-bottom: 4px; line-height: 1.3; }
.action-content {
  font-size: 13px; color: var(--text-secondary); line-height: 1.5;
  overflow: hidden; max-height: 60px;
}
.action-content.expanded { max-height: none; }
.silent { color: var(--text-secondary); font-size: 13px; font-style: italic; }
.expand-btn {
  background: none; border: none; color: var(--primary); font-size: 12px;
  padding: 2px 0; margin-top: 4px;
}
.card-footer {
  display: flex; align-items: center; gap: 8px; margin-top: 10px;
  padding-top: 8px; border-top: 1px solid var(--border);
}
.sentiment-chip {
  font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 8px;
}
.sentiment-chip.positive { background: #d1fae5; color: #059669; }
.sentiment-chip.negative { background: #fee2e2; color: #dc2626; }
.sentiment-chip.neutral { background: #f1f5f9; color: #64748b; }
.reach { font-size: 12px; color: var(--text-secondary); }
.platform-badge { font-size: 11px; color: var(--text-secondary); margin-left: auto; }
.influence-row {
  display: flex; align-items: center; gap: 4px; flex-wrap: wrap;
  margin-bottom: 6px; padding: 4px 0;
}
.influence-label { font-size: 10px; color: var(--text-secondary); }
.influence-tag {
  font-size: 10px; padding: 1px 6px; border-radius: 4px;
  font-weight: 600;
}
.scenario-tag {
  font-size: 10px; padding: 2px 8px; border-radius: 4px;
  background: #eff6ff; color: #1e40af; margin-bottom: 6px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.reasoning {
  margin-top: 8px; padding: 8px; background: #f8fafc; border-radius: 6px;
  font-size: 12px; color: var(--text-secondary); line-height: 1.4; font-style: italic;
}
</style>
