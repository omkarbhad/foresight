<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="detail-overlay" @click.self="$emit('close')">
        <div class="detail-panel">
          <div class="panel-header">
            <span class="source-badge" :class="sourceClass">{{ mention.source }}</span>
            <button class="close-btn" @click="$emit('close')" aria-label="Close">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>

          <h2 class="panel-title">{{ mention.title }}</h2>

          <div class="panel-byline">
            <span v-if="mention.author" class="author">{{ mention.author }}</span>
            <span v-if="mention.author && formattedDate" class="separator">&middot;</span>
            <span v-if="formattedDate" class="date">{{ formattedDate }}</span>
          </div>

          <div class="panel-content">{{ mention.content }}</div>

          <a
            v-if="mention.url"
            :href="mention.url"
            target="_blank"
            rel="noopener noreferrer"
            class="source-link"
          >
            View original source
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </a>

          <div class="analysis-section">
            <h3 class="section-heading">Analysis</h3>

            <div class="analysis-grid">
              <div class="analysis-item">
                <span class="analysis-label">Sentiment</span>
                <span class="sentiment-pill" :class="sentimentClass">{{ mention.sentiment || 'N/A' }}</span>
              </div>

              <div class="analysis-item">
                <span class="analysis-label">Crisis Score</span>
                <div class="crisis-inline">
                  <div class="crisis-bar">
                    <div
                      class="crisis-fill"
                      :style="{ width: crisisPercent + '%', background: crisisColor }"
                    />
                  </div>
                  <span class="crisis-value">{{ mention.crisis_score ?? 0 }}</span>
                </div>
              </div>

              <div class="analysis-item" v-if="mention.topics && mention.topics.length">
                <span class="analysis-label">Topics</span>
                <div class="topics-list">
                  <span v-for="topic in mention.topics" :key="topic" class="topic-tag">{{ topic }}</span>
                </div>
              </div>

              <div class="analysis-item" v-if="mention.summary">
                <span class="analysis-label">Summary</span>
                <p class="analysis-text">{{ mention.summary }}</p>
              </div>

              <div class="analysis-item" v-if="mention.amplify_status != null">
                <span class="analysis-label">Amplify Status</span>
                <span class="amplify-badge" :class="amplifyClass">{{ amplifyLabel }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  mention: {
    type: Object,
    required: true,
  },
  show: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['close'])

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

const formattedDate = computed(() => {
  if (!props.mention.published_at) return ''
  return new Date(props.mention.published_at).toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
})

const amplifyLabel = computed(() => {
  const status = props.mention.amplify_status
  if (status === true || status === 'amplified') return 'Amplified'
  if (status === false || status === 'suppressed') return 'Suppressed'
  if (status === 'pending') return 'Pending'
  return String(status)
})

const amplifyClass = computed(() => {
  const status = props.mention.amplify_status
  return {
    'amplify-active': status === true || status === 'amplified',
    'amplify-suppressed': status === false || status === 'suppressed',
    'amplify-pending': status === 'pending',
  }
})
</script>

<style scoped>
.detail-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  justify-content: flex-end;
}

.detail-panel {
  width: 540px;
  max-width: 100%;
  height: 100%;
  background: var(--surface);
  overflow-y: auto;
  padding: 28px;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.source-badge {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 3px 8px;
  border-radius: 6px;
}

.source-news { background: #dbeafe; color: #1d4ed8; }
.source-reddit { background: #fde8e8; color: #c0392b; }
.source-twitter { background: #e0f2fe; color: #0284c7; }

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  border-radius: 8px;
  color: var(--text-secondary);
  transition: background 0.15s, color 0.15s;
}

.close-btn:hover {
  background: var(--border);
  color: var(--text);
}

.panel-title {
  font-size: 20px;
  font-weight: 700;
  line-height: 1.35;
  color: var(--text);
  margin-bottom: 8px;
}

.panel-byline {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.separator { color: var(--border); }

.panel-content {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text);
  white-space: pre-wrap;
  margin-bottom: 18px;
}

.source-link {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 500;
  color: var(--primary);
  text-decoration: none;
  margin-bottom: 28px;
  transition: opacity 0.15s;
}

.source-link:hover { opacity: 0.8; }

.analysis-section {
  border-top: 1px solid var(--border);
  padding-top: 22px;
}

.section-heading {
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-secondary);
  margin-bottom: 16px;
}

.analysis-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.analysis-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.analysis-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
}

.sentiment-pill {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
  width: fit-content;
  text-transform: capitalize;
}

.sentiment-positive { background: #d1fae5; color: #065f46; }
.sentiment-negative { background: #fee2e2; color: #991b1b; }
.sentiment-neutral { background: #f1f5f9; color: var(--neutral); }
.sentiment-mixed { background: #fef3c7; color: #92400e; }

.crisis-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.crisis-bar {
  flex: 1;
  max-width: 200px;
  height: 8px;
  background: var(--border);
  border-radius: 4px;
  overflow: hidden;
}

.crisis-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
}

.crisis-value {
  font-size: 14px;
  font-weight: 700;
  color: var(--text);
}

.topics-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.topic-tag {
  font-size: 12px;
  padding: 3px 10px;
  background: #f1f5f9;
  color: var(--text-secondary);
  border-radius: 6px;
  font-weight: 500;
}

.analysis-text {
  font-size: 13px;
  line-height: 1.6;
  color: var(--text);
}

.amplify-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
  width: fit-content;
}

.amplify-active { background: #d1fae5; color: #065f46; }
.amplify-suppressed { background: #fee2e2; color: #991b1b; }
.amplify-pending { background: #fef3c7; color: #92400e; }

/* Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}

.modal-enter-active .detail-panel,
.modal-leave-active .detail-panel {
  transition: transform 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .detail-panel {
  transform: translateX(100%);
}

.modal-leave-to .detail-panel {
  transform: translateX(100%);
}
</style>
