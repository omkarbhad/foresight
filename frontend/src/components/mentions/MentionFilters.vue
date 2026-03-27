<template>
  <div class="mention-filters">
    <div class="filter-group">
      <label class="filter-label" for="filter-source">Source</label>
      <select id="filter-source" v-model="filters.source" @change="emitChange" class="filter-select">
        <option value="all">All Sources</option>
        <option value="news">News</option>
        <option value="reddit">Reddit</option>
        <option value="twitter">Twitter</option>
      </select>
    </div>

    <div class="filter-group">
      <label class="filter-label" for="filter-sentiment">Sentiment</label>
      <select id="filter-sentiment" v-model="filters.sentiment" @change="emitChange" class="filter-select">
        <option value="all">All Sentiments</option>
        <option value="positive">Positive</option>
        <option value="negative">Negative</option>
        <option value="neutral">Neutral</option>
        <option value="mixed">Mixed</option>
      </select>
    </div>

    <div class="filter-group">
      <label class="filter-label" for="filter-sort">Sort By</label>
      <select id="filter-sort" v-model="filters.sort_by" @change="emitChange" class="filter-select">
        <option value="newest">Newest First</option>
        <option value="crisis_score">Crisis Score</option>
        <option value="sentiment">Sentiment</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { reactive } from 'vue'

const emit = defineEmits(['filter-change'])

const filters = reactive({
  source: 'all',
  sentiment: 'all',
  sort_by: 'newest',
})

function emitChange() {
  emit('filter-change', { ...filters })
}
</script>

<style scoped>
.mention-filters {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  padding: 14px 18px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 150px;
}

.filter-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-secondary);
}

.filter-select {
  height: 36px;
  padding: 0 32px 0 10px;
  font-size: 13px;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2364748b' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 10px center;
  cursor: pointer;
  transition: border-color 0.15s;
}

.filter-select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.12);
}

.filter-select:hover {
  border-color: var(--primary);
}
</style>
