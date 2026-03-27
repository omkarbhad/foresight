<template>
  <AppLayout>
    <div class="digests-page">
      <div class="page-header">
        <h1>Digest History</h1>
        <button class="btn-primary" @click="handleGenerate" :disabled="generating">
          {{ generating ? 'Generating...' : 'Generate Now' }}
        </button>
      </div>

      <div v-if="digests.length === 0" class="empty-state">
        <p>No digests yet. Click "Generate Now" to create one.</p>
      </div>

      <div class="digests-list">
        <div v-for="d in digests" :key="d.digest_id" class="digest-card">
          <div class="digest-header">
            <span class="digest-period">
              {{ d.period_start?.slice(0, 10) }} - {{ d.period_end?.slice(0, 10) }}
            </span>
            <span class="digest-time">Generated: {{ d.generated_at?.slice(0, 16) }}</span>
          </div>
          <div class="digest-summary" v-html="formatSummary(d.summary)"></div>
          <div v-if="d.stats" class="digest-stats">
            <span>Mentions: {{ d.stats.total_mentions }}</span>
            <span>Avg Sentiment: {{ d.stats.avg_sentiment }}</span>
            <span>Crises: {{ d.stats.crisis_count }}</span>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import { listDigests, generateDigest } from '../api/digests'

const props = defineProps({ monitorId: String })
const digests = ref([])
const generating = ref(false)

onMounted(loadDigests)

async function loadDigests() {
  try {
    const res = await listDigests(props.monitorId)
    digests.value = res.data
  } catch (e) { console.error(e) }
}

async function handleGenerate() {
  generating.value = true
  try {
    await generateDigest(props.monitorId)
    await loadDigests()
  } catch (e) { console.error(e) }
  generating.value = false
}

function formatSummary(text) {
  if (!text) return ''
  return text.replace(/\n/g, '<br>')
}
</script>

<style scoped>
.digests-page { max-width: 900px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.btn-primary {
  padding: 10px 20px; background: var(--primary); color: white;
  border: none; border-radius: 8px; font-weight: 500; font-size: 14px;
}
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.digests-list { display: flex; flex-direction: column; gap: 16px; }
.digest-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 20px;
}
.digest-header { display: flex; justify-content: space-between; margin-bottom: 12px; }
.digest-period { font-weight: 600; font-size: 15px; }
.digest-time { font-size: 13px; color: var(--text-secondary); }
.digest-summary { font-size: 14px; line-height: 1.6; color: var(--text); margin-bottom: 12px; }
.digest-stats {
  display: flex; gap: 20px; font-size: 13px; color: var(--text-secondary);
  padding-top: 12px; border-top: 1px solid var(--border);
}
.empty-state { text-align: center; padding: 60px; color: var(--text-secondary); }
</style>
