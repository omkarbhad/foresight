<template>
  <AppLayout>
    <div class="monitors-page">
      <div class="page-header">
        <h1>Monitors</h1>
        <button class="btn-primary" @click="showForm = true">+ New Monitor</button>
      </div>

      <div v-if="showForm" class="form-overlay">
        <div class="form-container">
          <MonitorForm :monitor="editingMonitor" @submit="handleSubmit" @cancel="closeForm" />
        </div>
      </div>

      <div v-if="monitors.length === 0" class="empty-state">
        <p>No monitors yet. Create one to start tracking mentions.</p>
      </div>

      <div class="monitors-grid">
        <MonitorCard
          v-for="m in monitors" :key="m.monitor_id"
          :monitor="m"
          @edit="startEdit(m)"
          @delete="handleDelete(m.monitor_id)"
          @toggle-active="handleToggleActive(m)"
        />
      </div>
    </div>
  </AppLayout>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import AppLayout from '../components/layout/AppLayout.vue'
import MonitorForm from '../components/monitors/MonitorForm.vue'
import MonitorCard from '../components/monitors/MonitorCard.vue'
import { listMonitors, createMonitor, updateMonitor, deleteMonitor } from '../api/monitors'

const monitors = ref([])
const showForm = ref(false)
const editingMonitor = ref(null)

onMounted(loadMonitors)

async function loadMonitors() {
  try {
    const res = await listMonitors()
    monitors.value = res.data
  } catch (e) { console.error(e) }
}

function startEdit(monitor) {
  editingMonitor.value = monitor
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  editingMonitor.value = null
}

async function handleSubmit(data) {
  try {
    if (editingMonitor.value) {
      await updateMonitor(editingMonitor.value.monitor_id, data)
    } else {
      await createMonitor(data)
    }
    closeForm()
    await loadMonitors()
  } catch (e) { console.error(e) }
}

async function handleDelete(id) {
  if (!confirm('Delete this monitor and all its data?')) return
  try {
    await deleteMonitor(id)
    await loadMonitors()
  } catch (e) { console.error(e) }
}

async function handleToggleActive(monitor) {
  try {
    await updateMonitor(monitor.monitor_id, { is_active: !monitor.is_active })
    await loadMonitors()
  } catch (e) { console.error(e) }
}
</script>

<style scoped>
.monitors-page { max-width: 1200px; }
.page-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px; }
.page-header h1 { font-size: 24px; font-weight: 700; }
.btn-primary {
  padding: 10px 20px; background: var(--primary); color: white;
  border: none; border-radius: 8px; font-weight: 500; font-size: 14px;
}
.monitors-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 16px; }
.empty-state { text-align: center; padding: 60px; color: var(--text-secondary); }
.form-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.3); z-index: 200;
  display: flex; align-items: center; justify-content: center;
}
.form-container {
  background: var(--surface); border-radius: 12px; padding: 24px;
  width: 560px; max-height: 90vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.15);
}
</style>
