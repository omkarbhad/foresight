<template>
  <AppLayout>
    <div class="trends-page">
      <div class="page-header">
        <h1>Trends <span v-if="monitorName" class="monitor-name">{{ monitorName }}</span></h1>
        <select v-model="days" @change="loadTrends" class="days-select">
          <option :value="7">7 days</option>
          <option :value="14">14 days</option>
          <option :value="30">30 days</option>
          <option :value="90">90 days</option>
        </select>
      </div>

      <div class="charts-grid">
        <div class="card">
          <h3>Sentiment Over Time</h3>
          <SentimentLineChart :data="trends.sentiment_trend || []" />
        </div>
        <div class="card">
          <h3>Volume by Source</h3>
          <SourcePieChart :data="trends.volume_by_source || []" />
        </div>
      </div>

      <div class="card">
        <h3>Top Topics</h3>
        <div class="topics-list">
          <div v-for="t in trends.top_topics || []" :key="t.topic" class="topic-row">
            <span class="topic-name">{{ t.topic }}</span>
            <div class="topic-bar">
              <div class="topic-fill" :style="{ width: topicWidth(t.count) + '%' }"></div>
            </div>
            <span class="topic-count">{{ t.count }}</span>
          </div>
          <div v-if="!trends.top_topics?.length" class="empty">No topics yet</div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import SentimentLineChart from '../components/charts/SentimentLineChart.vue'
import SourcePieChart from '../components/charts/SourcePieChart.vue'
import { getTrends } from '../api/analysis'
import { getMonitor } from '../api/monitors'

const props = defineProps({ monitorId: String })
const trends = ref({})
const monitorName = ref('')
const days = ref(30)

const maxTopicCount = computed(() => {
  const topics = trends.value.top_topics || []
  return topics.length ? Math.max(...topics.map(t => t.count)) : 1
})

function topicWidth(count) {
  return (count / maxTopicCount.value) * 100
}

onMounted(async () => {
  try {
    const res = await getMonitor(props.monitorId)
    monitorName.value = res.data.name
  } catch (e) {}
  loadTrends()
})

async function loadTrends() {
  try {
    const res = await getTrends(props.monitorId, days.value)
    trends.value = res.data
  } catch (e) { console.error(e) }
}
</script>

<style scoped>
.trends-page { max-width: 1200px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.monitor-name { color: var(--primary); font-weight: 500; }
.days-select { padding: 8px 12px; border: 1px solid var(--border); border-radius: 8px; font-size: 14px; }
.charts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px; }
.card h3 { font-size: 16px; font-weight: 600; margin-bottom: 16px; }
.topics-list { display: flex; flex-direction: column; gap: 8px; }
.topic-row { display: flex; align-items: center; gap: 12px; }
.topic-name { min-width: 120px; font-size: 14px; font-weight: 500; }
.topic-bar { flex: 1; height: 24px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
.topic-fill { height: 100%; background: var(--primary); border-radius: 4px; transition: width 0.3s; }
.topic-count { font-size: 13px; color: var(--text-secondary); min-width: 40px; text-align: right; }
.empty { color: var(--text-secondary); padding: 20px; text-align: center; }
</style>
