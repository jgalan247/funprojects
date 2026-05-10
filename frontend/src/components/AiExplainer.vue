<script setup lang="ts">
import { ref, computed } from 'vue'
import { useAiInfo } from '../composables/useAiInfo'

const props = defineProps<{ sensorId: string; hasReading: boolean }>()

const { info } = useAiInfo()

interface ExplainResponse {
  text: string
  provider: string
  model: string
  input_tokens: number | null
  output_tokens: number | null
  latency_ms: number
  status: string
}

const result = ref<ExplainResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const buttonDisabled = computed(() => loading.value || !props.hasReading)

async function explain() {
  loading.value = true
  error.value = null
  result.value = null
  try {
    const res = await fetch('/api/ai/explain', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sensor_id: props.sensorId }),
    })
    if (!res.ok) {
      const detail = await res.text().catch(() => '')
      throw new Error(`${res.status}${detail ? ` — ${detail.slice(0, 120)}` : ''}`)
    }
    result.value = (await res.json()) as ExplainResponse
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'unknown error'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="border-t border-slate-800 pt-5 mt-5">
    <header class="flex items-baseline justify-between mb-3">
      <h3 class="text-sm font-extrabold uppercase tracking-widest text-slate-500">
        AI explanation
      </h3>
      <span
        v-if="info?.fallback"
        class="text-[0.7rem] px-2 py-0.5 rounded-full bg-yellow-500/15 text-yellow-300 font-bold uppercase tracking-wider"
        title="ANTHROPIC_API_KEY is not set — using offline stub"
      >
        offline
      </span>
    </header>

    <button
      type="button"
      class="w-full min-h-[3rem] rounded-xl bg-pi-red text-white font-bold tracking-tight transition-all active:scale-[0.98] disabled:opacity-40 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-pi-red"
      :disabled="buttonDisabled"
      @click="explain"
    >
      <span v-if="loading">Thinking…</span>
      <span v-else-if="!hasReading">No reading yet</span>
      <span v-else-if="result">Explain again</span>
      <span v-else>Explain this reading</span>
    </button>

    <p v-if="error" class="mt-3 text-pi-red-soft text-sm">
      {{ error }}
    </p>

    <div
      v-if="result"
      class="mt-4 rounded-xl bg-slate-800/60 border border-slate-700 p-4"
    >
      <p class="text-base text-slate-200 leading-relaxed">
        {{ result.text || '(no text returned)' }}
      </p>
      <div class="mt-3 flex flex-wrap gap-2 font-mono text-[0.7rem] text-slate-500">
        <span>{{ result.model }}</span>
        <span class="text-slate-700">·</span>
        <span>{{ result.input_tokens ?? '?' }} → {{ result.output_tokens ?? '?' }} tok</span>
        <span class="text-slate-700">·</span>
        <span>{{ result.latency_ms }} ms</span>
        <span
          v-if="result.status !== 'ok'"
          class="px-2 py-0.5 rounded bg-pi-red/20 text-pi-red-soft font-bold"
        >
          {{ result.status }}
        </span>
      </div>
    </div>
  </section>
</template>
