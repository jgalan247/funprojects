<script setup lang="ts">
import { ref, onMounted } from 'vue'

type HealthState = 'unknown' | 'ok' | 'error'

const apiHealth = ref<HealthState>('unknown')
const aiHealth = ref<HealthState>('unknown')

async function probe(url: string): Promise<HealthState> {
  try {
    const res = await fetch(url, { cache: 'no-store' })
    return res.ok ? 'ok' : 'error'
  } catch {
    return 'error'
  }
}

function statusClass(s: HealthState): string {
  return s === 'ok'
    ? 'text-pi-green-soft'
    : s === 'error'
    ? 'text-pi-red-soft'
    : 'text-slate-500'
}

function statusLabel(s: HealthState): string {
  return s === 'ok' ? 'healthy' : s === 'error' ? 'unreachable' : 'checking…'
}

onMounted(async () => {
  apiHealth.value = await probe('/api/health')
  // The AI service isn't proxied through the frontend yet — that lands when
  // the API gains an /ai/explain endpoint in Phase 6. For now we mirror the
  // API status; if the API is up, the platform is up.
  aiHealth.value = apiHealth.value
})
</script>

<template>
  <main
    class="min-h-screen flex items-center justify-center p-6 bg-slate-900 text-slate-100"
    style="background-image: radial-gradient(circle at 12% 8%, rgba(197, 26, 74, 0.08) 0%, transparent 35%), radial-gradient(circle at 88% 92%, rgba(117, 179, 67, 0.08) 0%, transparent 35%);"
  >
    <div class="max-w-xl w-full text-center space-y-6">

      <div
        class="mx-auto w-16 h-16 rounded-full bg-pi-red flex items-center justify-center text-white font-mono font-bold text-xl shadow-lg"
        aria-hidden="true"
      >
        Pi
      </div>

      <h1 class="text-4xl font-extrabold tracking-tight">
        Pi IoT Platform
      </h1>

      <p class="text-lg text-slate-400">
        Phase&nbsp;2 placeholder. The real touchscreen dashboard is built in
        Phase&nbsp;5.
      </p>

      <div
        class="font-mono text-sm rounded-lg border border-slate-700 bg-slate-800/60 backdrop-blur p-4 text-left space-y-2"
      >
        <div class="flex justify-between">
          <span class="text-slate-400">api</span>
          <span :class="statusClass(apiHealth)">{{ statusLabel(apiHealth) }}</span>
        </div>
        <div class="flex justify-between">
          <span class="text-slate-400">ai</span>
          <span :class="statusClass(aiHealth)">{{ statusLabel(aiHealth) }}</span>
        </div>
      </div>

      <p class="text-xs text-slate-500">
        Coderra.je &middot; Pi IoT Academy
      </p>
    </div>
  </main>
</template>
