import { ref } from 'vue'

export interface SystemLogEntry {
  id: number
  ts: string
  level: 'info' | 'warn' | 'error' | string
  source: string
  event: string
  detail: Record<string, unknown>
}

const logs = ref<SystemLogEntry[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

export async function loadSystemLogs(limit = 100): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/system/logs?limit=${limit}`, { cache: 'no-store' })
    if (!res.ok) throw new Error(`${res.status}`)
    logs.value = (await res.json()) as SystemLogEntry[]
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'unknown'
  } finally {
    loading.value = false
  }
}

export function useSystemLogs() {
  return { logs, loading, error, refresh: loadSystemLogs }
}
