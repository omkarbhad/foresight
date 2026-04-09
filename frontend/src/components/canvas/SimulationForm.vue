<template>
  <div v-if="visible" class="form-wrapper">
    <div class="form-center">
      <h1 class="heading">What scenario do you<br>want to simulate?</h1>
      <p class="subtext">Describe an event and watch AI agents react in real-time</p>

      <div class="input-card">
        <div v-if="parsedScenarios.length" class="tags-row">
          <span class="tag" v-for="(s, i) in parsedScenarios" :key="i">
            {{ s }}
            <button class="tag-remove" @click="removeScenario(i)">
              <component :is="XIcon" :size="12" />
            </button>
          </span>
        </div>

        <div class="input-area">
          <textarea
            v-model="form.scenarioInput"
            rows="3"
            placeholder="Describe a scenario... e.g. USA attacks Iran, Oil prices spike 40%"
            maxlength="3000"
            @keydown.enter.prevent="addFromInput"
          ></textarea>
        </div>

        <div class="input-footer">
          <div class="footer-left">
            <div class="rounds-control">
              <span class="rounds-label">Rounds</span>
              <button class="rounds-btn" @click="form.totalRounds = Math.max(3, form.totalRounds - 1)">-</button>
              <span class="rounds-value">{{ form.totalRounds }}</span>
              <button class="rounds-btn" @click="form.totalRounds = Math.min(8, form.totalRounds + 1)">+</button>
            </div>
          </div>
          <div class="footer-right">
            <span class="char-count">{{ allScenariosText.length }}/3000</span>
            <button class="btn-run" :disabled="!canSubmit" @click="handleSubmit">
              Run
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></svg>
            </button>
          </div>
        </div>
      </div>

      <div class="presets">
        <button v-for="p in presets" :key="p.label" class="preset-chip" @click="addPreset(p.text)">
          {{ p.label }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'
import { X as XIcon } from 'lucide-vue-next'

const emit = defineEmits(['submit'])
defineProps({ visible: { type: Boolean, default: true } })

const presets = [
  { label: 'US-Iran Conflict', text: 'USA launches military strikes against Iran' },
  { label: 'Russia-Ukraine', text: 'Russia escalates military operations in Ukraine' },
  { label: 'Oil Shock', text: 'Global oil prices spike 40% due to Middle East supply disruption' },
  { label: 'Taiwan Crisis', text: 'China begins naval blockade of Taiwan' },
  { label: 'Market Crash', text: 'Major stock market crash triggered by banking sector collapse' },
  { label: 'Climate Failure', text: 'Global climate summit collapses with no agreement' },
]

const form = reactive({
  scenarioInput: '',
  addedScenarios: [],
  totalRounds: 6,
})

const parsedScenarios = computed(() => form.addedScenarios)

const allScenarios = computed(() => {
  const fromInput = form.scenarioInput
    .split(',')
    .map(s => s.trim())
    .filter(s => s.length > 0)
  return [...form.addedScenarios, ...fromInput]
})

const allScenariosText = computed(() => allScenarios.value.join(', '))
const canSubmit = computed(() => allScenarios.value.length > 0)

function addFromInput() {
  const items = form.scenarioInput.split(',').map(s => s.trim()).filter(s => s.length > 0)
  if (items.length > 0) {
    form.addedScenarios.push(...items)
    form.scenarioInput = ''
  }
}

function addPreset(text) {
  if (!form.addedScenarios.includes(text)) {
    form.addedScenarios.push(text)
  }
}

function removeScenario(index) {
  form.addedScenarios.splice(index, 1)
}

function handleSubmit() {
  addFromInput()
  const scenarios = allScenarios.value
  if (scenarios.length === 0) return
  emit('submit', { scenarios, config: { total_rounds: form.totalRounds } })
}
</script>

<style scoped>
.form-wrapper {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding-top: 44px;
  z-index: 10;
  overflow: hidden;
}

.form-center {
  max-width: 640px;
  width: 100%;
  padding: 0 24px;
  position: relative;
  z-index: 1;
}
.heading {
  font-size: 28px;
  font-weight: 500;
  color: var(--text-primary);
  text-align: center;
  line-height: 1.25;
  letter-spacing: -0.025em;
}
.subtext {
  font-size: 13px;
  color: var(--text-muted);
  text-align: center;
  margin-top: 6px;
  margin-bottom: 24px;
}
.input-card {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 10px;
  overflow: hidden;
}
.tags-row {
  padding: 12px 16px;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px 10px;
  font-size: 12px;
  color: var(--text-secondary);
}
.tag-remove {
  background: none;
  border: none;
  color: var(--text-muted);
  padding: 0;
  display: flex;
  cursor: pointer;
  transition: color 150ms;
}
.tag-remove:hover { color: var(--danger); }

.input-area textarea {
  width: 100%;
  padding: 16px;
  background: transparent;
  border: none;
  color: var(--text-primary);
  font-size: 14px;
  resize: none;
  min-height: 80px;
  outline: none;
  font-family: inherit;
  line-height: 1.5;
}
.input-area textarea::placeholder {
  color: var(--text-placeholder);
}

.input-footer {
  padding: 10px 12px;
  border-top: 1px solid rgba(255,255,255,0.06);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.footer-left { display: flex; align-items: center; }
.footer-right { display: flex; align-items: center; gap: 10px; }

/* Rounds stepper inside footer */
.rounds-control {
  display: flex;
  align-items: center;
  gap: 4px;
}
.rounds-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-right: 4px;
}
.rounds-btn {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-hover);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: border-color 150ms;
}
.rounds-btn:hover { border-color: var(--border-strong); color: var(--text-primary); }
.rounds-value {
  font-size: 12px;
  color: var(--text-primary);
  min-width: 14px;
  text-align: center;
}

.char-count {
  font-size: 11px;
  color: var(--text-muted);
}
.btn-run {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  background: var(--btn-active-bg);
  color: var(--btn-active-text);
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 150ms;
}
.btn-run:hover:not(:disabled) {
  opacity: 0.85;
}
.btn-run:disabled {
  background: var(--btn-inactive-bg);
  color: var(--btn-inactive-text);
  box-shadow: none;
  cursor: not-allowed;
}

.presets {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
  margin-top: 16px;
}
.preset-chip {
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.07);
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 12px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: border-color 150ms, color 150ms;
}
.preset-chip:hover {
  border-color: var(--border-strong);
  color: var(--text-primary);
}
</style>
