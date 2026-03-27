<template>
  <article class="mention-card" @click="$emit('click', mention)">
    <div class="card-header">
      <span class="source-badge" :class="sourceClass">{{ mention.source }}</span>
      <span class="published-time">{{ formattedTime }}</span>
    </div>

    <h3 class="card-title">{{ mention.title }}</h3>

    <p class="card-excerpt">{{ excerpt }}</p>

    <div class="card-meta">
      <span class="sentiment-pill" :class="sentimentClass">{{ mention.sentiment }}</span>

      <div class="crisis-score">
        <span class="crisis-label">Crisis</span>
        <div class="crisis-bar">
          <div
            class="crisis-fill"
            :style="{ width: crisisPercent + '%', background: crisisColor }"
          />
        </div>
        <span class="crisis-value">{{ mention.crisis_score ?? 0 }}</span>
      </div>
    </div>

    <div class="card-footer" v-if="mention.author">
      <span class="author">by {{ mention.author }}</span>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  mention: {
    type: Object,
    required: true,
  },
})

defineEmits(['click'])

const excerpt = computed(() => {
  const content = props.mention.content || ''
  return content.length > 150 ? content.slice(0, 150) + '...' : content
})

const sourceClass = computed(() => {
  const s = (props.mention.source || '').toLowerCase()
  return {
    'source-news': s === 'news',
    'source-reddit': s === 'reddit',
    'source-twitter': s === 'twitter',
  }
})

const sentimentClass = computed(() => {
  const s = (props.mention.sentiment || '').toLowerCase()
  return {
    'sentiment-positive': s === 'positive',
    'sentiment-negative': s === 'negative',
    'sentiment-neutral': s === 'neutral',
    'sentiment-mixed': s === 'mixed',
  }
})

const crisisPercent = computed(() => {
  const score = Number(props.mention.crisis_score) || 0
  return Math.min(Math.max(score, 0), 100)
})

const crisisColor = computed(() => {
  const score = crisisPercent.value
  if (score >= 70) return 'var(--danger)'
  if (score >= 40) return 'var(--warning)'
  return 'var(--success)'
})

const formattedTime = computed(() => {
  if (!props.mention.published_at) return ''
  const date = new Date(props.mention.published_at)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins}m ago`
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return `${diffHours}h ago`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
})
</script>

<style scoped>
.mention-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  cursor: pointer;
  transition: box-shadow 0.2s, border-color 0.2s;
}

.mention-card:hover {
  border-color: var(--primary);
  box-shadow: 0 2px 12px rgba(37, 99, 235, 0.08);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.source-badge {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 3px 8px;
  border-radius: 6px;
}

.source-news {
  background: #dbeafe;
  color: #1d4ed8;
}

.source-reddit {
  background: #fde8e8;
  color: #c0392b;
}

.source-twitter {
  background: #e0f2fe;
  color: #0284c7;
}

.published-time {
  font-size: 12px;
  color: var(--text-secondary);
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  line-height: 1.4;
  margin-bottom: 8px;
  color: var(--text);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-excerpt {
  font-size: 13px;
  line-height: 1.55;
  color: var(--text-secondary);
  margin-bottom: 14px;
}

.card-meta {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 10px;
}

.sentiment-pill {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
  white-space: nowrap;
  text-transform: capitalize;
}

.sentiment-positive {
  background: #d1fae5;
  color: #065f46;
}

.sentiment-negative {
  background: #fee2e2;
  color: #991b1b;
}

.sentiment-neutral {
  background: #f1f5f9;
  color: var(--neutral);
}

.sentiment-mixed {
  background: #fef3c7;
  color: #92400e;
}

.crisis-score {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  min-width: 0;
}

.crisis-label {
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.crisis-bar {
  flex: 1;
  height: 6px;
  background: var(--border);
  border-radius: 3px;
  overflow: hidden;
}

.crisis-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.crisis-value {
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  min-width: 22px;
  text-align: right;
}

.card-footer {
  padding-top: 10px;
  border-top: 1px solid var(--border);
}

.author {
  font-size: 12px;
  color: var(--text-secondary);
}
</style>
