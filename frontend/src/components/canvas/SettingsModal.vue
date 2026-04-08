<template>
  <Teleport to="body">
    <div v-if="visible" class="modal-overlay" @click.self="$emit('close')">
      <div class="modal-panel">
        <div class="modal-header">
          <h2>Settings</h2>
          <button class="btn-close" @click="$emit('close')">
            <component :is="XIcon" :size="18" />
          </button>
        </div>

        <div class="modal-body">
          <!-- LLM Provider -->
          <section class="settings-group">
            <h3>
              LLM Provider
              <span class="badge">Required</span>
            </h3>
            <div class="field">
              <label>Provider</label>
              <select v-model="form.llm_provider" class="input">
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="openrouter">OpenRouter</option>
                <option value="openai">OpenAI</option>
              </select>
            </div>
            <div class="field">
              <label>Model</label>
              <input v-model="form.llm_model" class="input" :placeholder="modelPlaceholder" />
              <span class="field-hint">{{ modelHint }}</span>
            </div>
            <div class="field">
              <label>API Key</label>
              <div class="input-with-toggle">
                <input
                  v-model="form.llm_api_key"
                  :type="showKeys.llm ? 'text' : 'password'"
                  class="input"
                  placeholder="sk-..."
                />
                <button class="toggle-vis" @click="showKeys.llm = !showKeys.llm">
                  <component :is="showKeys.llm ? EyeOffIcon : EyeIcon" :size="14" />
                </button>
              </div>
              <span class="status-indicator" :class="{ configured: status.llm_api_key }">
                {{ status.llm_api_key ? 'Configured' : 'Not set' }}
              </span>
            </div>
          </section>

          <!-- Data Sources -->
          <section class="settings-group">
            <h3>
              Data Sources
              <span class="badge">Optional</span>
            </h3>
            <div class="field">
              <label>NewsAPI Key</label>
              <div class="input-with-toggle">
                <input v-model="form.news_api_key" :type="showKeys.news ? 'text' : 'password'" class="input" placeholder="API key" />
                <button class="toggle-vis" @click="showKeys.news = !showKeys.news">
                  <component :is="showKeys.news ? EyeOffIcon : EyeIcon" :size="14" />
                </button>
              </div>
            </div>
            <div class="field">
              <label>Reddit Client ID</label>
              <input v-model="form.reddit_client_id" class="input" placeholder="Client ID" />
            </div>
            <div class="field">
              <label>Reddit Client Secret</label>
              <div class="input-with-toggle">
                <input v-model="form.reddit_client_secret" :type="showKeys.reddit ? 'text' : 'password'" class="input" placeholder="Client secret" />
                <button class="toggle-vis" @click="showKeys.reddit = !showKeys.reddit">
                  <component :is="showKeys.reddit ? EyeOffIcon : EyeIcon" :size="14" />
                </button>
              </div>
            </div>
            <div class="field">
              <label>Finnhub API Key</label>
              <div class="input-with-toggle">
                <input v-model="form.finnhub_api_key" :type="showKeys.finnhub ? 'text' : 'password'" class="input" placeholder="API key" />
                <button class="toggle-vis" @click="showKeys.finnhub = !showKeys.finnhub">
                  <component :is="showKeys.finnhub ? EyeOffIcon : EyeIcon" :size="14" />
                </button>
              </div>
            </div>
            <div class="field">
              <label>Twitter Bearer Token</label>
              <div class="input-with-toggle">
                <input v-model="form.twitter_bearer_token" :type="showKeys.twitter ? 'text' : 'password'" class="input" placeholder="Bearer token" />
                <button class="toggle-vis" @click="showKeys.twitter = !showKeys.twitter">
                  <component :is="showKeys.twitter ? EyeOffIcon : EyeIcon" :size="14" />
                </button>
              </div>
            </div>
          </section>
        </div>

        <div class="modal-footer">
          <span v-if="saveMsg" class="save-msg" :class="saveMsg.type">{{ saveMsg.text }}</span>
          <span v-if="testResult" class="save-msg" :class="testResult.type">{{ testResult.text }}</span>
          <button class="btn-test" :disabled="testing" @click="handleTest">
            {{ testing ? 'Testing...' : 'Test' }}
          </button>
          <button class="btn-save" :disabled="saving" @click="handleSave">
            {{ saving ? 'Saving...' : 'Save Settings' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { X as XIcon, Eye as EyeIcon, EyeOff as EyeOffIcon } from 'lucide-vue-next'
import { getSettings, updateSettings, testLlmConnection } from '../../api/simulation'

const props = defineProps({ visible: Boolean })
const emit = defineEmits(['close', 'saved'])

const form = reactive({
  llm_provider: 'openrouter',
  llm_model: '',
  llm_api_key: '',
  news_api_key: '',
  reddit_client_id: '',
  reddit_client_secret: '',
  finnhub_api_key: '',
  twitter_bearer_token: '',
})

const showKeys = reactive({ llm: false, news: false, reddit: false, finnhub: false, twitter: false })
const status = reactive({ llm_api_key: false })
const saving = ref(false)
const saveMsg = ref(null)
const testing = ref(false)
const testResult = ref(null)

const modelPlaceholder = computed(() => {
  const placeholders = {
    anthropic: 'claude-sonnet-4-20250514',
    openrouter: 'openrouter/auto',
    openai: 'gpt-4o',
  }
  return placeholders[form.llm_provider] || 'model-name'
})

const modelHint = computed(() => {
  const hints = {
    anthropic: 'Recommended: claude-sonnet-4-20250514',
    openrouter: 'Auto-select: openrouter/auto — Free: nvidia/nemotron-3-super-120b-a12b:free',
    openai: 'Recommended: gpt-4o',
  }
  return hints[form.llm_provider] || ''
})

async function loadSettings() {
  try {
    const res = await getSettings()
    const data = res.data || {}
    Object.keys(form).forEach(key => {
      if (data[key] !== undefined) form[key] = data[key]
    })
  } catch (e) {
    // Settings may not exist yet
  }
}

async function handleSave() {
  saving.value = true
  saveMsg.value = null
  try {
    await updateSettings({ ...form })
    saveMsg.value = { type: 'success', text: 'Settings saved' }
    emit('saved')
    setTimeout(() => { saveMsg.value = null }, 3000)
  } catch (e) {
    saveMsg.value = { type: 'error', text: 'Failed to save' }
  } finally {
    saving.value = false
  }
}

async function handleTest() {
  testing.value = true
  testResult.value = null
  try {
    const res = await testLlmConnection()
    testResult.value = { type: 'success', text: res.message || 'Connection successful' }
  } catch (e) {
    const msg = e?.response?.data?.error || e?.message || 'Connection failed'
    testResult.value = { type: 'error', text: msg }
  } finally {
    testing.value = false
    setTimeout(() => { testResult.value = null }, 5000)
  }
}

watch(() => props.visible, (v) => { if (v) loadSettings() })
onMounted(() => { if (props.visible) loadSettings() })
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-panel {
  width: 520px;
  max-height: 85vh;
  background: rgba(10,10,11,0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--border);
}
.modal-header h2 {
  font-size: 16px;
  font-weight: 600;
  color: var(--text-primary);
}
.btn-close {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text-secondary);
  cursor: pointer;
  transition: border-color 150ms ease, color 150ms ease;
}
.btn-close:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
}
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
}
.settings-group {
  margin-bottom: 24px;
}
.settings-group h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 14px;
}
.badge {
  font-size: 11px;
  color: var(--text-muted);
}
.field {
  margin-bottom: 12px;
}
.field label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: var(--text-muted);
  margin-bottom: 4px;
}
.input {
  width: 100%;
  padding: 8px 12px;
  background: rgba(255,255,255,0.03);
  border: 1px solid rgba(255,255,255,0.06);
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 13px;
  transition: border-color 150ms ease;
}
.input:focus {
  outline: none;
  border-color: rgba(139,92,246,0.5);
}
select.input {
  font-family: 'Inter', sans-serif;
}
.input-with-toggle {
  position: relative;
}
.input-with-toggle .input {
  padding-right: 36px;
}
.toggle-vis {
  position: absolute;
  right: 8px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-muted);
  padding: 4px;
  cursor: pointer;
  transition: color 150ms ease;
}
.toggle-vis:hover {
  color: var(--text-secondary);
}
.field-hint {
  display: block;
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}
.status-indicator {
  display: inline-block;
  font-size: 11px;
  margin-top: 4px;
  color: var(--danger);
}
.status-indicator.configured {
  color: var(--success);
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid var(--border);
}
.save-msg {
  font-size: 12px;
}
.save-msg.success {
  color: var(--success);
}
.save-msg.error {
  color: var(--danger);
}
.btn-save {
  padding: 8px 20px;
  background: white;
  color: #0a0a0b;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 150ms ease;
}
.btn-save:hover {
  opacity: 0.9;
}
.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn-test {
  padding: 8px 16px;
  background: rgba(255,255,255,0.05);
  color: rgba(255,255,255,0.6);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 150ms ease, color 150ms ease;
}
.btn-test:hover {
  border-color: var(--text-muted);
  color: var(--text-primary);
}
.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
