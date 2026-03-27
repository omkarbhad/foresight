<template>
  <AppLayout>
    <div class="dashboard">
      <div class="page-header">
        <h1>Dashboard</h1>
        <select v-model="selectedMonitor" class="monitor-select" @change="loadDashboard">
          <option value="">Select a monitor...</option>
          <option v-for="m in monitors" :key="m.monitor_id" :value="m.monitor_id">
            {{ m.name }}
          </option>
        </select>
      </div>

      <div v-if="!selectedMonitor" class="empty-state">
        <p>Select a monitor to view its dashboard</p>
        <router-link to="/monitors" class="btn-primary">Manage Monitors</router-link>
      </div>

      <template v-else>
        <div class="metrics-grid">
          <MetricCard label="Total Mentions (7d)" :value="stats.total_mentions || 0" color="#2563eb" />
          <MetricCard label="Positive" :value="stats.positive_count || 0" color="#10b981" />
          <MetricCard label="Negative" :value="stats.negative_count || 0" color="#ef4444" />
          <MetricCard label="Crisis Alerts" :value="stats.crisis_count || 0" color="#f59e0b" />
        </div>

        <div class="dashboard-row">
          <div class="card gauge-card">
            <h3>Average Sentiment</h3>
            <SentimentGauge :value="stats.avg_sentiment || 0" label="7-day average" />
          </div>
          <div class="card crisis-card">
            <h3>Max Crisis Score</h3>
            <div class="crisis-simple">{{ ((stats.max_crisis_score || 0) * 100).toFixed(0) }}%</div>
          </div>
        </div>

        <div class="card">
          <h3>Recent Mentions</h3>
          <RecentMentions :mentions="recentMentions" />
        </div>
      </template>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import MetricCard from '../components/dashboard/MetricCard.vue'
import SentimentGauge from '../components/dashboard/SentimentGauge.vue'
import RecentMentions from '../components/dashboard/RecentMentions.vue'
import { listMonitors } from '../api/monitors'
import { getDashboard } from '../api/analysis'
import { listMentions } from '../api/mentions'

const monitors = ref([])
const selectedMonitor = ref('')
const stats = ref({})
const recentMentions = ref([])

onMounted(async () => {
  try {
    const res = await listMonitors()
    monitors.value = res.data
    if (monitors.value.length > 0) {
      selectedMonitor.value = monitors.value[0].monitor_id
      loadDashboard()
    }
  } catch (e) { console.error(e) }
})

async function loadDashboard() {
  if (!selectedMonitor.value) return
  try {
    const [dashRes, mentionsRes] = await Promise.all([
      getDashboard(selectedMonitor.value),
      listMentions(selectedMonitor.value, { limit: 10 }),
    ])
    stats.value = dashRes.data
    recentMentions.value = mentionsRes.data
  } catch (e) { console.error(e) }
}
</script>

<style scoped>
.dashboard { max-width: 1200px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.monitor-select {
  padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px;
  font-size: 14px; background: var(--surface);
}
.metrics-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.dashboard-row { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
.card h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
.empty-state { text-align: center; padding: 60px 20px; color: var(--text-secondary); }
.btn-primary {
  display: inline-block; margin-top: 16px; padding: 10px 20px;
  background: var(--primary); color: white; border-radius: 8px;
  text-decoration: none; font-weight: 500;
}
</style>
