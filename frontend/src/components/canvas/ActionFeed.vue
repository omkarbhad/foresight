<template>
  <div v-if="visible" class="feed-panel">
    <div class="feed-header">
      <span class="feed-title">Feed</span>
      <div class="feed-header-right">
        <span class="feed-count">{{ filteredActions.length }}</span>
        <div v-if="availableRounds.length > 1" class="round-filter" ref="filterRef">
          <button class="filter-btn" :class="{ active: selectedRound !== 'all' }" @click="showDropdown = !showDropdown" title="Filter by round">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M22 3H2l8 9.46V19l4 2v-8.54L22 3z"/></svg>
            <span v-if="selectedRound !== 'all'" class="filter-badge">{{ selectedRound }}</span>
          </button>
          <div v-if="showDropdown" class="filter-dropdown">
            <button class="filter-option" :class="{ selected: selectedRound === 'all' }" @click="selectRound('all')">
              All rounds
            </button>
            <button v-for="r in availableRounds" :key="r" class="filter-option" :class="{ selected: selectedRound === r }" @click="selectRound(r)">
              Round {{ r }}
            </button>
          </div>
        </div>
      </div>
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
import { computed, ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import AgentActionCard from './AgentActionCard.vue'

const props = defineProps({
  actions: { type: Array, default: () => [] },
  agentDefs: { type: Object, default: () => ({}) },
  visible: { type: Boolean, default: false },
})

const scrollEl = ref(null)
const filterRef = ref(null)
const selectedRound = ref('all')
const showDropdown = ref(false)

const reversedActions = computed(() => [...props.actions].reverse())

const availableRounds = computed(() => {
  const rounds = new Set(props.actions.map(a => a._round).filter(r => r != null))
  return [...rounds].sort((a, b) => a - b)
})

const filteredActions = computed(() => {
  if (selectedRound.value === 'all') return reversedActions.value
  return reversedActions.value.filter(a => a._round === selectedRound.value)
})

function selectRound(r) {
  selectedRound.value = r
  showDropdown.value = false
}

function showRoundHeader(action, index) {
  if (index === 0) return true
  const prev = filteredActions.value[index - 1]
  return action._round !== prev?._round
}

function onClickOutside(e) {
  if (filterRef.value && !filterRef.value.contains(e.target)) {
    showDropdown.value = false
  }
}

onMounted(() => document.addEventListener('mousedown', onClickOutside))
onUnmounted(() => document.removeEventListener('mousedown', onClickOutside))

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
  border-left: 1px solid rgba(255,255,255,0.08);
  z-index: 50;
  display: flex;
  flex-direction: column;
}
.feed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.feed-title {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255,255,255,0.7);
  letter-spacing: -0.02em;
}
.feed-header-right {
  display: flex; align-items: center; gap: 6px;
}
.feed-count {
  font-size: 10px;
  color: rgba(255,255,255,0.25);
  padding: 2px 7px;
  background: rgba(255,255,255,0.04);
  border-radius: 6px;
}

/* Filter button */
.round-filter {
  position: relative;
}
.filter-btn {
  width: 28px; height: 28px;
  display: flex; align-items: center; justify-content: center;
  background: none;
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 6px;
  color: rgba(255,255,255,0.3);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
  position: relative;
}
.filter-btn:hover {
  color: rgba(255,255,255,0.6);
  border-color: rgba(255,255,255,0.12);
}
.filter-btn.active {
  color: var(--accent);
  border-color: rgba(99,102,241,0.3);
  background: rgba(99,102,241,0.06);
}
.filter-badge {
  position: absolute;
  top: -4px; right: -4px;
  font-size: 8px; font-weight: 700;
  color: #fff;
  background: var(--accent);
  width: 14px; height: 14px;
  border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  line-height: 1;
}

/* Dropdown */
.filter-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  min-width: 120px;
  background: #151517;
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  padding: 4px;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.filter-option {
  display: block; width: 100%;
  padding: 6px 10px;
  font-size: 11px;
  color: rgba(255,255,255,0.45);
  background: none; border: none;
  border-radius: 5px;
  cursor: pointer;
  text-align: left;
  transition: background 0.1s, color 0.1s;
}
.filter-option:hover {
  background: rgba(255,255,255,0.04);
  color: rgba(255,255,255,0.7);
}
.filter-option.selected {
  color: var(--accent);
  background: rgba(99,102,241,0.08);
}

.feed-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
  padding-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.round-divider {
  padding: 8px 4px 2px;
}
.round-divider:first-child { padding-top: 0; }
.round-label {
  font-size: 10px;
  font-weight: 500;
  color: rgba(255,255,255,0.2);
  letter-spacing: 0;
}
.feed-empty {
  text-align: center;
  padding: 48px 16px;
  color: rgba(255,255,255,0.2);
  font-size: 13px;
}
</style>
