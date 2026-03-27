<template>
  <form class="monitor-form" @submit.prevent="handleSubmit">
    <h2 class="form-title">{{ isEdit ? 'Edit Monitor' : 'Create Monitor' }}</h2>

    <div class="form-group">
      <label class="form-label" for="monitor-name">Name</label>
      <input
        id="monitor-name"
        v-model="form.name"
        type="text"
        class="form-input"
        placeholder="e.g. Brand Mentions Tracker"
        required
      />
    </div>

    <div class="form-group">
      <label class="form-label">Keywords</label>
      <div class="tag-input-wrapper">
        <div class="tag-pills">
          <span v-for="(tag, i) in form.keywords" :key="'kw-' + i" class="pill">
            {{ tag }}
            <button type="button" class="pill-remove" @click="removeTag('keywords', i)">&times;</button>
          </span>
        </div>
        <input
          v-model="tagInputs.keywords"
          type="text"
          class="tag-input"
          placeholder="Type and press Enter or comma"
          @keydown.enter.prevent="addTag('keywords')"
          @keydown.,="addTag('keywords')"
        />
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">Negative Keywords</label>
      <div class="tag-input-wrapper">
        <div class="tag-pills">
          <span v-for="(tag, i) in form.negative_keywords" :key="'nk-' + i" class="pill pill--negative">
            {{ tag }}
            <button type="button" class="pill-remove" @click="removeTag('negative_keywords', i)">&times;</button>
          </span>
        </div>
        <input
          v-model="tagInputs.negative_keywords"
          type="text"
          class="tag-input"
          placeholder="Type and press Enter or comma"
          @keydown.enter.prevent="addTag('negative_keywords')"
          @keydown.,="addTag('negative_keywords')"
        />
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">Sources</label>
      <div class="checkbox-group">
        <label v-for="source in availableSources" :key="source.value" class="checkbox-label">
          <input
            v-model="form.sources"
            type="checkbox"
            :value="source.value"
            class="checkbox-input"
          />
          <span class="checkbox-custom"></span>
          <span class="checkbox-text">{{ source.label }}</span>
        </label>
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">
        Alert Threshold
        <span class="label-hint">{{ (form.alert_threshold * 100).toFixed(0) }}%</span>
      </label>
      <input
        v-model.number="form.alert_threshold"
        type="range"
        class="range-input"
        min="0"
        max="1"
        step="0.01"
      />
      <div class="range-labels">
        <span>Low sensitivity</span>
        <span>High sensitivity</span>
      </div>
    </div>

    <div class="form-group">
      <label class="form-label">Competitors</label>
      <div class="tag-input-wrapper">
        <div class="tag-pills">
          <span v-for="(tag, i) in form.competitors" :key="'comp-' + i" class="pill pill--competitor">
            {{ tag }}
            <button type="button" class="pill-remove" @click="removeTag('competitors', i)">&times;</button>
          </span>
        </div>
        <input
          v-model="tagInputs.competitors"
          type="text"
          class="tag-input"
          placeholder="Type and press Enter or comma"
          @keydown.enter.prevent="addTag('competitors')"
          @keydown.,="addTag('competitors')"
        />
      </div>
    </div>

    <div class="form-actions">
      <button type="button" class="btn btn--secondary" @click="$emit('cancel')">Cancel</button>
      <button type="submit" class="btn btn--primary">
        {{ isEdit ? 'Update Monitor' : 'Create Monitor' }}
      </button>
    </div>
  </form>
</template>

<script setup>
import { reactive, computed } from 'vue'

const props = defineProps({
  monitor: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['submit', 'cancel'])

const isEdit = computed(() => !!props.monitor)

const availableSources = [
  { label: 'News', value: 'news' },
  { label: 'Reddit', value: 'reddit' },
  { label: 'Twitter', value: 'twitter' },
]

const form = reactive({
  name: props.monitor?.name ?? '',
  keywords: props.monitor?.keywords ? [...props.monitor.keywords] : [],
  negative_keywords: props.monitor?.negative_keywords ? [...props.monitor.negative_keywords] : [],
  sources: props.monitor?.sources ? [...props.monitor.sources] : [],
  alert_threshold: props.monitor?.alert_threshold ?? 0.5,
  competitors: props.monitor?.competitors ? [...props.monitor.competitors] : [],
})

const tagInputs = reactive({
  keywords: '',
  negative_keywords: '',
  competitors: '',
})

function addTag(field) {
  const raw = tagInputs[field].replace(/,/g, '').trim()
  if (raw && !form[field].includes(raw)) {
    form[field].push(raw)
  }
  tagInputs[field] = ''
}

function removeTag(field, index) {
  form[field].splice(index, 1)
}

function handleSubmit() {
  emit('submit', {
    name: form.name,
    keywords: [...form.keywords],
    negative_keywords: [...form.negative_keywords],
    sources: [...form.sources],
    alert_threshold: form.alert_threshold,
    competitors: [...form.competitors],
  })
}
</script>

<style scoped>
.monitor-form {
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
  margin: 0 0 28px;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.label-hint {
  font-size: 14px;
  font-weight: 700;
  color: var(--primary);
  text-transform: none;
  letter-spacing: 0;
}

.form-input {
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  color: var(--text);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  outline: none;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
  box-sizing: border-box;
}

.form-input:focus {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 15%, transparent);
}

/* Tag input */
.tag-input-wrapper {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  background: var(--surface);
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.tag-input-wrapper:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 15%, transparent);
}

.tag-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 500;
  color: var(--primary);
  background: color-mix(in srgb, var(--primary) 12%, transparent);
  border-radius: 16px;
  white-space: nowrap;
}

.pill--negative {
  color: var(--danger);
  background: color-mix(in srgb, var(--danger) 12%, transparent);
}

.pill--competitor {
  color: var(--warning);
  background: color-mix(in srgb, var(--warning) 12%, transparent);
}

.pill-remove {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  padding: 0;
  opacity: 0.7;
  transition: opacity 0.15s ease;
}

.pill-remove:hover {
  opacity: 1;
}

.tag-input {
  flex: 1;
  min-width: 120px;
  border: none;
  outline: none;
  font-size: 14px;
  color: var(--text);
  background: transparent;
  padding: 4px 0;
}

.tag-input::placeholder {
  color: var(--text-secondary);
}

/* Checkboxes */
.checkbox-group {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: var(--text);
  user-select: none;
}

.checkbox-input {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
}

.checkbox-custom {
  width: 18px;
  height: 18px;
  border: 2px solid var(--border);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
  flex-shrink: 0;
}

.checkbox-input:checked + .checkbox-custom {
  background: var(--primary);
  border-color: var(--primary);
}

.checkbox-input:checked + .checkbox-custom::after {
  content: '';
  width: 5px;
  height: 9px;
  border: solid white;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg) translate(-1px, -1px);
}

.checkbox-input:focus-visible + .checkbox-custom {
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 25%, transparent);
}

/* Range slider */
.range-input {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: var(--border);
  border-radius: 3px;
  outline: none;
}

.range-input::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
  border: 3px solid var(--surface);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
  transition: transform 0.15s ease;
}

.range-input::-webkit-slider-thumb:hover {
  transform: scale(1.15);
}

.range-input::-moz-range-thumb {
  width: 20px;
  height: 20px;
  background: var(--primary);
  border-radius: 50%;
  cursor: pointer;
  border: 3px solid var(--surface);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
}

.range-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 6px;
  font-size: 11px;
  color: var(--text-secondary);
}

/* Actions */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid var(--border);
}

.btn {
  padding: 10px 20px;
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

.btn--primary:hover {
  filter: brightness(1.08);
  box-shadow: 0 2px 8px color-mix(in srgb, var(--primary) 40%, transparent);
}

.btn--secondary {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.btn--secondary:hover {
  background: color-mix(in srgb, var(--neutral) 8%, transparent);
  color: var(--text);
}
</style>
