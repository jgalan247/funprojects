import { ref } from 'vue'

export interface SnapshotSummary {
  id: number
  taken_at: string
  label: string | null
  count: number
}

const snapshots = ref<SnapshotSummary[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

export async function listSnapshots(limit = 20): Promise<void> {
  loading.value = true
  error.value = null
  try {
    const res = await fetch(`/api/snapshots?limit=${limit}`, { cache: 'no-store' })
    if (!res.ok) throw new Error(`${res.status}`)
    snapshots.value = (await res.json()) as SnapshotSummary[]
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'unknown'
  } finally {
    loading.value = false
  }
}

export async function takeSnapshot(label: string | null = null): Promise<SnapshotSummary> {
  const res = await fetch('/api/snapshots', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ label }),
  })
  if (!res.ok) throw new Error(`${res.status}`)
  const result = (await res.json()) as SnapshotSummary
  // Prepend so the latest shows first.
  snapshots.value = [result, ...snapshots.value]
  return result
}

export function useSnapshots() {
  return { snapshots, loading, error, refresh: listSnapshots, take: takeSnapshot }
}
