import { ref } from 'vue'

export interface AiInfo {
  provider: string
  model: string
  fallback: boolean
}

const info = ref<AiInfo | null>(null)
let started = false

async function load(): Promise<void> {
  try {
    const res = await fetch('/api/ai/info', { cache: 'no-store' })
    if (!res.ok) return
    info.value = (await res.json()) as AiInfo
  } catch {
    /* silent — UI can fall back to nothing */
  }
}

export function useAiInfo() {
  if (!started) {
    started = true
    load()
  }
  return { info, refresh: load }
}
