<template>
  <AppLayout>
    <div class="crisis-page">
      <div class="page-header">
        <h1>Crisis Alerts</h1>
        <label class="filter-toggle">
          <input type="checkbox" v-model="unackOnly" @change="loadAlerts" />
          Unacknowledged only
        </label>
      </div>

      <div v-if="alerts.length === 0" class="empty-state">
        <p>No crisis alerts. All clear!</p>
      </div>

      <div class="alerts-list">
        <div v-for="alert in alerts" :key="alert.event_id"
             class="alert-card" :class="{ acknowledged: alert.acknowledged }">

          <!-- Header: crisis score + monitor name + time -->
          <div class="alert-header">
            <span class="crisis-badge" :style="{ background: crisisColor(alert.crisis_score) }">
              {{ (alert.crisis_score * 100).toFixed(0) }}% Crisis
            </span>
            <span class="alert-monitor">{{ alert.monitor_name }}</span>
            <span v-if="alert.mention?.source" class="source-badge" :class="alert.mention.source">
              {{ alert.mention.source }}
            </span>
            <span class="alert-time">{{ formatTime(alert.delivered_at) }}</span>
          </div>

          <!-- Mention details -->
          <div v-if="alert.mention" class="mention-details">
            <h3 class="mention-title">{{ alert.mention.title || 'Untitled' }}</h3>
            <p class="mention-content">{{ alert.mention.content }}</p>

            <div class="mention-meta">
              <span v-if="alert.mention.author" class="meta-item">
                By {{ alert.mention.author }}
              </span>
              <span v-if="alert.mention.sentiment_label" class="sentiment-pill" :class="alert.mention.sentiment_label">
                {{ alert.mention.sentiment_label }} ({{ alert.mention.sentiment_score?.toFixed(2) }})
              </span>
              <span v-if="alert.mention.published_at" class="meta-item">
                {{ formatTime(alert.mention.published_at) }}
              </span>
            </div>

            <p v-if="alert.mention.analysis_summary" class="analysis-summary">
              {{ alert.mention.analysis_summary }}
            </p>

            <div v-if="alert.mention.topics?.length" class="topics">
              <span v-for="t in alert.mention.topics" :key="t" class="topic-tag">{{ t }}</span>
            </div>

            <a v-if="alert.mention.source_url" :href="alert.mention.source_url"
               target="_blank" class="source-link">
              View Original Source &rarr;
            </a>
          </div>

          <!-- Footer: status + action -->
          <div class="alert-footer">
            <span v-if="alert.acknowledged" class="ack-badge">Acknowledged</span>
            <button v-if="!alert.acknowledged" class="btn-ack" @click="handleAck(alert.event_id)">
              Acknowledge
            </button>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import { listAlerts, acknowledgeAlert } from '../api/alerts'

const alerts = ref([])
const unackOnly = ref(true)

onMounted(loadAlerts)

async function loadAlerts() {
  try {
    const res = await listAlerts({ unacknowledged_only: unackOnly.value })
    alerts.value = res.data
  } catch (e) { console.error(e) }
}

async function handleAck(eventId) {
  try {
    await acknowledgeAlert(eventId)
    await loadAlerts()
  } catch (e) { console.error(e) }
}

function crisisColor(score) {
  if (score >= 0.8) return '#ef4444'
  if (score >= 0.5) return '#f59e0b'
  return '#6b7280'
}

function formatTime(ts) {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    const now = new Date()
    const diff = now - d
    if (diff < 60000) return 'Just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch {
    return ts?.slice(0, 16) || ''
  }
}
</script>

<style scoped>
.crisis-page { max-width: 900px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.filter-toggle { font-size: 14px; display: flex; align-items: center; gap: 8px; cursor: pointer; }

.alerts-list { display: flex; flex-direction: column; gap: 16px; }

.alert-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 20px; border-left: 4px solid var(--danger);
}
.alert-card.acknowledged { opacity: 0.6; border-left-color: var(--neutral); }

.alert-header { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.crisis-badge {
  color: white; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: 700;
}
.alert-monitor { font-weight: 600; font-size: 15px; }
.source-badge {
  padding: 2px 10px; border-radius: 8px; font-size: 11px; font-weight: 600; text-transform: uppercase;
}
.source-badge.news { background: #dbeafe; color: #2563eb; }
.source-badge.reddit { background: #fee2e2; color: #dc2626; }
.source-badge.twitter { background: #e0f2fe; color: #0284c7; }
.alert-time { margin-left: auto; font-size: 13px; color: var(--text-secondary); }

.mention-details { margin-bottom: 14px; }
.mention-title { font-size: 16px; font-weight: 600; margin-bottom: 6px; line-height: 1.3; }
.mention-content { font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 10px; }

.mention-meta { display: flex; align-items: center; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
.meta-item { font-size: 13px; color: var(--text-secondary); }
.sentiment-pill {
  font-size: 12px; font-weight: 600; padding: 2px 10px; border-radius: 8px;
}
.sentiment-pill.positive { background: #d1fae5; color: #059669; }
.sentiment-pill.negative { background: #fee2e2; color: #dc2626; }
.sentiment-pill.neutral { background: #f1f5f9; color: #64748b; }
.sentiment-pill.mixed { background: #fef3c7; color: #d97706; }

.analysis-summary {
  font-size: 14px; color: var(--text); background: #f8fafc; padding: 10px 14px;
  border-radius: 8px; border-left: 3px solid var(--primary); margin-bottom: 10px;
  line-height: 1.5; font-style: italic;
}

.topics { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.topic-tag {
  font-size: 12px; padding: 2px 10px; border-radius: 6px;
  background: #f1f5f9; color: var(--text-secondary);
}

.source-link {
  font-size: 13px; color: var(--primary); text-decoration: none; font-weight: 500;
}
.source-link:hover { text-decoration: underline; }

.alert-footer { display: flex; align-items: center; gap: 12px; padding-top: 12px; border-top: 1px solid var(--border); }
.ack-badge { background: #d1fae5; color: var(--success); padding: 4px 12px; border-radius: 8px; font-size: 13px; font-weight: 500; }
.btn-ack {
  padding: 8px 20px; background: var(--primary); color: white;
  border: none; border-radius: 8px; font-size: 13px; font-weight: 500;
}

.empty-state { text-align: center; padding: 60px; color: var(--text-secondary); }
</style>
