<template>
  <AppLayout>
    <div class="whatif-page">
      <div class="page-header">
        <h1>What-If Predictor</h1>
        <p class="subtitle">Explore hypothetical scenarios and predict their media impact</p>
      </div>

      <WhatIfForm :monitors="monitors" @submit="handleSubmit" />

      <PredictionResult v-if="prediction || loading" :prediction="prediction" :loading="loading" />
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import WhatIfForm from '../components/whatif/WhatIfForm.vue'
import PredictionResult from '../components/whatif/PredictionResult.vue'
import { listMonitors } from '../api/monitors'
import { submitWhatIf } from '../api/analysis'

const monitors = ref([])
const prediction = ref(null)
const loading = ref(false)

onMounted(async () => {
  try {
    const res = await listMonitors()
    monitors.value = res.data
  } catch (e) { console.error(e) }
})

async function handleSubmit({ monitor_id, scenario }) {
  loading.value = true
  prediction.value = null
  try {
    const res = await submitWhatIf(monitor_id, scenario)
    prediction.value = res.data
  } catch (e) {
    console.error(e)
    prediction.value = { error: 'Prediction failed. Please try again.' }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.whatif-page { max-width: 900px; }
.page-header { margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.subtitle { color: var(--text-secondary); font-size: 14px; margin-top: 4px; }
</style>
