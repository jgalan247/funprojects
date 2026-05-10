import { ref } from 'vue'

export interface AiUsage {
  window_days: number
  calls: number
  successes: number
  input_tokens: number
  output_tokens: number
}

const usage = ref<AiUsage | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

export async function loadAiUsage(days = 7): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/ai/usage?days=${days}`, { cache: 'no-store' })
    if (!res.ok) throw new Error(`${res.status}`)
    usage.value = (await res.json()) as AiUsage
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'unknown'
  } finally {
    loading.value = false
  }
}

export function useAiUsage() {
  return { usage, loading, error, refresh: loadAiUsage }
}
