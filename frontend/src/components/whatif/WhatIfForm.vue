<template>
  <form class="whatif-form" @submit.prevent="handleSubmit">
    <h2 class="form-title">What-If Scenario Analysis</h2>
    <p class="form-description">
      Describe a hypothetical scenario to predict its impact on your brand's public perception.
    </p>

    <div class="form-group">
      <label class="form-label" for="whatif-monitor">Monitor</label>
      <div class="select-wrapper">
        <select
          id="whatif-monitor"
          v-model="selectedMonitorId"
          class="form-select"
          required
        >
          <option value="" disabled>Select a monitor...</option>
          <option
            v-for="m in monitors"
            :key="m.id"
            :value="m.id"
          >
            {{ m.name }}
          </option>
        </select>
        <svg class="select-chevron" width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </div>
    </div>

    <div class="form-group">
      <label class="form-label" for="whatif-scenario">Scenario</label>
      <textarea
        id="whatif-scenario"
        v-model="scenario"
        class="form-textarea"
        rows="8"
        placeholder="Describe the hypothetical scenario in detail. For example: 'Our CEO makes a controversial public statement about climate policy that contradicts our published sustainability commitments...'"
        required
      ></textarea>
      <span class="char-count" :class="{ 'char-count--warn': scenario.length > 1800 }">
        {{ scenario.length }} / 2000
      </span>
    </div>

    <div class="form-actions">
      <button
        type="submit"
        class="btn btn--primary"
        :disabled="!selectedMonitorId || !scenario.trim()"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 2v12M2 8l6 6 6-6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Run Prediction
      </button>
    </div>
  </form>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  monitors: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['submit'])

const selectedMonitorId = ref('')
const scenario = ref('')

function handleSubmit() {
  emit('submit', {
    monitor_id: selectedMonitorId.value,
    scenario: scenario.value.trim(),
  })
}
</script>

<style scoped>
.whatif-form {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 32px;
  max-width: 640px;
  font-family: 'Inter', sans-serif;
}

.form-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 8px;
}

.form-description {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0 0 28px;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Select */
.select-wrapper {
  position: relative;
}

.form-select {
  width: 100%;
  padding: 10px 40px 10px 14px;
  font-size: 14px;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  appearance: none;
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.form-select:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 15%, transparent);
}

.select-chevron {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-secondary);
  pointer-events: none;
}

/* Textarea */
.form-textarea {
  width: 100%;
  padding: 12px 14px;
  font-size: 14px;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  resize: vertical;
  line-height: 1.6;
  font-family: inherit;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  box-sizing: border-box;
}

.form-textarea:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 15%, transparent);
}

.form-textarea::placeholder {
  color: var(--text-secondary);
}

.char-count {
  display: block;
  text-align: right;
  font-size: 11px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.char-count--warn {
  color: var(--warning);
  font-weight: 600;
}

/* Actions */
.form-actions {
  margin-top: 8px;
}

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn--primary {
  background: var(--primary);
  color: white;
}

.btn--primary:hover:not(:disabled) {
  filter: brightness(1.08);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--primary) 40%, transparent);
}

.btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
