<template>
  <div v-if="visible" class="feed-panel">
    <div class="feed-header">
      <span class="feed-title">Feed</span>
      <span class="feed-count">{{ filteredActions.length }}</span>
    </div>
    <div class="feed-filter" v-if="availableRounds.length > 1">
      <select v-model="selectedRound" class="round-select">
        <option value="all">All rounds</option>
        <option v-for="r in availableRounds" :key="r" :value="r">Round {{ r }}</option>
      </select>
    </div>
    <div class="feed-scroll" ref="scrollEl">
      <template v-for="(action, i) in filteredActions" :key="i">
        <div v-if="showRoundHeader(action, i)" class="round-divider">
          <span class="round-label">Round {{ action._round }}</span>
        </div>
        <AgentActionCard
          :action="action"
          :agentDefs="agentDefs"
        />
      </template>
      <div v-if="actions.length === 0" class="feed-empty">
        Waiting for agents...
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import AgentActionCard from './AgentActionCard.vue'

const props = defineProps({
  actions: { type: Array, default: () => [] },
  agentDefs: { type: Object, default: () => ({}) },
  visible: { type: Boolean, default: false },
})

const scrollEl = ref(null)
const selectedRound = ref('all')

const reversedActions = computed(() => [...props.actions].reverse())

const availableRounds = computed(() => {
  const rounds = new Set(props.actions.map(a => a._round).filter(r => r != null))
  return [...rounds].sort((a, b) => a - b)
})

const filteredActions = computed(() => {
  if (selectedRound.value === 'all') return reversedActions.value
  return reversedActions.value.filter(a => a._round === selectedRound.value)
})

function showRoundHeader(action, index) {
  if (index === 0) return true
  const prev = filteredActions.value[index - 1]
  return action._round !== prev?._round
}

watch(() => props.actions.length, () => {
  nextTick(() => {
    if (scrollEl.value) scrollEl.value.scrollTop = 0
  })
})
</script>

<style scoped>
.feed-panel {
  position: fixed;
  top: 44px;
  right: 0;
  width: 340px;
  bottom: 0;
  background: #0c0c0d;
  border-left: 1px solid rgba(255,255,255,0.06);
  z-index: 50;
  display: flex;
  flex-direction: column;
}
.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.feed-title {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255,255,255,0.7);
}
.feed-count {
  font-size: 11px;
  color: rgba(255,255,255,0.25);
  padding: 2px 8px;
  background: rgba(255,255,255,0.04);
  border-radius: 8px;
}
.feed-filter {
  padding: 8px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.round-select {
  width: 100%;
  padding: 5px 10px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 8px;
  color: rgba(255,255,255,0.6);
  font-size: 12px;
  font-family: inherit;
}
.round-select:focus {
  outline: none;
  border-color: var(--accent);
}
.feed-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.round-divider {
  padding: 8px 4px 2px;
}
.round-divider:first-child { padding-top: 0; }
.round-label {
  font-size: 10px;
  font-weight: 500;
  color: rgba(255,255,255,0.2);
  letter-spacing: 0.05em;
}
.feed-empty {
  text-align: center;
  padding: 48px 16px;
  color: rgba(255,255,255,0.2);
  font-size: 13px;
}
</style>
