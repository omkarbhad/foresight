<template>
  <AppLayout>
    <div class="mentions-page">
      <div class="page-header">
        <h1>Mentions <span v-if="monitorName" class="monitor-name">{{ monitorName }}</span></h1>
      </div>

      <MentionFilters @filter-change="handleFilterChange" />

      <div class="mentions-list">
        <MentionCard
          v-for="m in mentions" :key="m.mention_id"
          :mention="m"
          @click="selectedMention = m"
        />
        <div v-if="mentions.length === 0" class="empty-state">No mentions found.</div>
      </div>

      <MentionDetail
        :mention="selectedMention"
        :show="!!selectedMention"
        @close="selectedMention = null"
      />
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import MentionCard from '../components/mentions/MentionCard.vue'
import MentionFilters from '../components/mentions/MentionFilters.vue'
import MentionDetail from '../components/mentions/MentionDetail.vue'
import { listMentions } from '../api/mentions'
import { getMonitor } from '../api/monitors'

const props = defineProps({ monitorId: String })
const mentions = ref([])
const selectedMention = ref(null)
const monitorName = ref('')
const filters = ref({ source: null, sentiment: null, sort_by: 'ingested_at' })

onMounted(async () => {
  try {
    const res = await getMonitor(props.monitorId)
    monitorName.value = res.data.name
  } catch (e) {}
  loadMentions()
})

async function loadMentions() {
  try {
    const params = { limit: 50, ...filters.value }
    Object.keys(params).forEach(k => { if (!params[k]) delete params[k] })
    const res = await listMentions(props.monitorId, params)
    mentions.value = res.data
  } catch (e) { console.error(e) }
}

function handleFilterChange(f) {
  filters.value = f
  loadMentions()
}
</script>

<style scoped>
.mentions-page { max-width: 900px; }
.page-header { margin-bottom: 20px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.monitor-name { color: var(--primary); font-weight: 500; }
.mentions-list { display: flex; flex-direction: column; gap: 12px; margin-top: 16px; }
.empty-state { text-align: center; padding: 40px; color: var(--text-secondary); }
</style>
