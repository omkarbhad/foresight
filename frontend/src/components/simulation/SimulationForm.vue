<template>
  <div class="sim-form">
    <h2>Configure Simulation</h2>

    <div class="field">
      <label>Scenarios</label>
      <p class="info-text">Enter one or more scenarios separated by commas. Each scenario generates its own agents, then all agents interact in a shared simulation to reveal cross-scenario dynamics.</p>
      <div class="scenario-input-area">
        <div class="tags-row" v-if="parsedScenarios.length > 0">
          <span class="tag" v-for="(s, i) in parsedScenarios" :key="i">
            {{ s }}
            <button class="tag-remove" @click="removeScenario(i)">&times;</button>
          </span>
        </div>
        <textarea
          v-model="form.scenarioInput"
          class="input textarea"
          rows="3"
          placeholder='e.g. USA attacks Iran, Russia attacked Ukraine, Oil prices spike 40%'
          maxlength="3000"
          @keydown.enter.prevent="addFromInput"
        ></textarea>
      </div>
      <div class="input-footer">
        <span class="hint">Press Enter or use commas to separate multiple scenarios</span>
        <span class="char-count">{{ allScenariosText.length }}/3000</span>
      </div>
    </div>

    <div class="presets">
      <span class="presets-label">Quick scenarios:</span>
      <button v-for="p in presets" :key="p.label" class="preset-btn" @click="addPreset(p.text)">
        {{ p.label }}
      </button>
    </div>

    <div class="field">
      <label>Rounds ({{ form.totalRounds }})</label>
      <input type="range" v-model.number="form.totalRounds" min="3" max="8" step="1" class="range" />
      <div class="range-labels">
        <span>3 (Quick)</span><span>6 (Standard)</span><span>8 (Deep)</span>
      </div>
    </div>

    <div class="field">
      <label>Agents</label>
      <p class="info-text">AI will automatically select 5-20 agents tailored to your scenarios -- covering media, markets, government, geopolitics, and any other relevant stakeholders.</p>
    </div>

    <button class="btn-primary" :disabled="!canSubmit" @click="handleSubmit">
      Run Simulation
    </button>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'

const emit = defineEmits(['submit'])

const presets = [
  { label: 'US-Iran Conflict', text: 'USA launches military strikes against Iran' },
  { label: 'Russia-Ukraine Escalation', text: 'Russia escalates military operations in Ukraine' },
  { label: 'Oil Price Shock', text: 'Global oil prices spike 40% due to Middle East supply disruption' },
  { label: 'Taiwan Strait Crisis', text: 'China begins naval blockade of Taiwan' },
  { label: 'Market Crash', text: 'Major stock market crash triggered by banking sector collapse' },
  { label: 'Climate Summit Failure', text: 'Global climate summit collapses with no agreement, triggering protests worldwide' },
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
  const items = form.scenarioInput
    .split(',')
    .map(s => s.trim())
    .filter(s => s.length > 0)
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

  emit('submit', {
    scenarios,
    config: {
      total_rounds: form.totalRounds,
    },
  })
}
</script>

<style scoped>
.sim-form {
  background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 24px;
}
h2 { font-size: 18px; font-weight: 700; margin-bottom: 20px; }
.field { margin-bottom: 16px; }
.field label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 6px; color: var(--text); }
.input {
  width: 100%; padding: 10px 12px; border: 1px solid var(--border); border-radius: 8px;
  font-size: 14px; font-family: inherit; background: var(--surface);
}
.textarea { resize: vertical; line-height: 1.5; }
.scenario-input-area {
  border: 1px solid var(--border); border-radius: 8px; overflow: hidden;
}
.scenario-input-area .textarea {
  border: none; border-radius: 0; border-top: 1px solid var(--border);
}
.scenario-input-area .textarea:first-child {
  border-top: none;
}
.tags-row {
  display: flex; flex-wrap: wrap; gap: 6px; padding: 10px 12px;
}
.tag {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 4px 10px; background: #eff6ff; border: 1px solid #bfdbfe;
  border-radius: 6px; font-size: 13px; color: #1e40af;
}
.tag-remove {
  background: none; border: none; color: #6b7280; font-size: 16px;
  cursor: pointer; padding: 0 2px; line-height: 1;
}
.tag-remove:hover { color: #ef4444; }
.input-footer {
  display: flex; justify-content: space-between; align-items: center; margin-top: 4px;
}
.hint { font-size: 12px; color: var(--text-secondary); }
.char-count { font-size: 12px; color: var(--text-secondary); }
.presets { margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.presets-label { font-size: 12px; color: var(--text-secondary); margin-right: 4px; }
.preset-btn {
  padding: 4px 10px; border: 1px solid var(--border); border-radius: 6px;
  background: var(--surface); font-size: 12px; color: var(--text-secondary);
  cursor: pointer; transition: all 0.15s;
}
.preset-btn:hover { border-color: var(--primary); color: var(--primary); }
.range { width: 100%; margin: 4px 0; }
.range-labels { display: flex; justify-content: space-between; font-size: 11px; color: var(--text-secondary); }
.info-text { font-size: 13px; color: var(--text-secondary); line-height: 1.5; margin: 0 0 8px 0; }
.btn-primary {
  width: 100%; padding: 12px; background: var(--primary); color: white;
  border: none; border-radius: 8px; font-size: 15px; font-weight: 600; margin-top: 8px;
}
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
