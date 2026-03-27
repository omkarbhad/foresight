<template>
  <AppLayout>
    <div class="amplify-page">
      <div class="page-header">
        <h1>Amplify Queue</h1>
        <p class="subtitle">Positive mentions worth promoting</p>
      </div>

      <div v-if="mentions.length === 0" class="empty-state">
        <p>No amplify-worthy mentions yet.</p>
      </div>

      <div class="mentions-grid">
        <div v-for="m in mentions" :key="m.mention_id" class="amplify-card">
          <div class="card-header">
            <span class="source-badge" :class="m.source">{{ m.source }}</span>
            <span class="sentiment">{{ m.sentiment_label }} ({{ m.sentiment_score?.toFixed(2) }})</span>
          </div>
          <h3 class="card-title">{{ m.title || 'Untitled' }}</h3>
          <p class="card-content">{{ (m.content || '').slice(0, 200) }}</p>
          <div class="card-footer">
            <span class="author">{{ m.author || 'Unknown' }}</span>
            <a v-if="m.source_url" :href="m.source_url" target="_blank" class="link">View Source</a>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import { getAmplifyQueue } from '../api/mentions'

const mentions = ref([])

onMounted(async () => {
  try {
    const res = await getAmplifyQueue()
    mentions.value = res.data
  } catch (e) { console.error(e) }
})
</script>

<style scoped>
.amplify-page { max-width: 1200px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }
.mentions-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 16px; }
.amplify-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px;
  padding: 20px; border-left: 4px solid var(--success);
}
.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.source-badge {
  padding: 2px 10px; border-radius: 8px; font-size: 12px; font-weight: 600; text-transform: uppercase;
}
.source-badge.news { background: #dbeafe; color: #2563eb; }
.source-badge.reddit { background: #fee2e2; color: #dc2626; }
.source-badge.twitter { background: #e0f2fe; color: #0284c7; }
.sentiment { font-size: 13px; color: var(--success); font-weight: 500; }
.card-title { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
.card-content { font-size: 14px; color: var(--text-secondary); line-height: 1.5; margin-bottom: 12px; }
.card-footer { display: flex; align-items: center; justify-content: space-between; font-size: 13px; }
.author { color: var(--text-secondary); }
.link { color: var(--primary); text-decoration: none; font-weight: 500; }
.empty-state { text-align: center; padding: 60px; color: var(--text-secondary); }
</style>
