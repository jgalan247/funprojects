<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useSystemLogs } from '../composables/useSystemLogs'
import { useAiUsage } from '../composables/useAiUsage'
import { useAiInfo } from '../composables/useAiInfo'
import { useSnapshots } from '../composables/useSnapshots'

const { logs, loading, error, refresh } = useSystemLogs()
const { usage, refresh: refreshUsage } = useAiUsage()
const { info: aiInfo } = useAiInfo()
const { snapshots, refresh: refreshSnapshots } = useSnapshots()

onMounted(() => {
  refresh(50)
  refreshUsage(7)
  refreshSnapshots(20)
})

function levelClass(level: string): string {
  switch (level) {
    case 'error': return 'text-pi-red-soft bg-pi-red/10'
    case 'warn': return 'text-yellow-300 bg-yellow-500/10'
    default: return 'text-slate-300 bg-slate-700/40'
  }
}

function shortTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString([], {
    month: 'short',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function detailSummary(detail: Record<string, unknown>): string {
  const parts: string[] = []
  for (const [k, v] of Object.entries(detail)) {
    if (parts.length >= 3) break
    const text = typeof v === 'object' ? JSON.stringify(v) : String(v)
    parts.push(`${k}=${text.slice(0, 32)}`)
  }
  return parts.join(' · ')
}

const groupedByEvent = computed(() => {
  const counts = new Map<string, number>()
  for (const l of logs.value) counts.set(l.event, (counts.get(l.event) ?? 0) + 1)
  return [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5)
})
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto space-y-8">

    <!-- About this platform -->
    <section>
      <h2 class="text-sm font-extrabold uppercase tracking-widest text-slate-500 mb-3">
        Platform
      </h2>
      <dl class="rounded-xl border border-slate-800 bg-slate-900/40 divide-y divide-slate-800">
        <div class="flex justify-between p-4">
          <dt class="text-slate-400">Frontend version</dt>
          <dd class="font-mono text-sm">0.5.0</dd>
        </div>
        <div class="flex justify-between p-4">
          <dt class="text-slate-400">API endpoint</dt>
          <dd class="font-mono text-sm">/api</dd>
        </div>
        <div class="flex justify-between p-4">
          <dt class="text-slate-400">WebSocket endpoint</dt>
          <dd class="font-mono text-sm">/ws/sensors</dd>
        </div>
        <div class="flex justify-between p-4">
          <dt class="text-slate-400">Reading retention</dt>
          <dd class="font-mono text-sm">30 days, 03:00 UTC daily</dd>
        </div>
      </dl>
    </section>

    <!-- AI usage -->
    <section>
      <header class="flex items-baseline justify-between mb-3">
        <h2 class="text-sm font-extrabold uppercase tracking-widest text-slate-500">
          AI usage (last 7 days)
        </h2>
        <span
          v-if="aiInfo?.fallback"
          class="text-[0.7rem] px-2 py-0.5 rounded-full bg-yellow-500/15 text-yellow-300 font-bold uppercase tracking-wider"
        >
          offline stub
        </span>
        <span
          v-else-if="aiInfo"
          class="text-[0.7rem] font-mono text-slate-500"
        >
          {{ aiInfo.model }}
        </span>
      </header>

      <div
        v-if="usage"
        class="grid grid-cols-2 sm:grid-cols-4 gap-3"
      >
        <div class="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div class="text-[0.7rem] uppercase tracking-widest text-slate-500 font-bold">Calls</div>
          <div class="text-2xl font-extrabold tabular-nums mt-1">{{ usage.calls }}</div>
        </div>
        <div class="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div class="text-[0.7rem] uppercase tracking-widest text-slate-500 font-bold">Successes</div>
          <div class="text-2xl font-extrabold tabular-nums mt-1 text-pi-green-soft">{{ usage.successes }}</div>
        </div>
        <div class="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div class="text-[0.7rem] uppercase tracking-widest text-slate-500 font-bold">Input tokens</div>
          <div class="text-2xl font-extrabold tabular-nums mt-1">{{ usage.input_tokens.toLocaleString() }}</div>
        </div>
        <div class="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
          <div class="text-[0.7rem] uppercase tracking-widest text-slate-500 font-bold">Output tokens</div>
          <div class="text-2xl font-extrabold tabular-nums mt-1">{{ usage.output_tokens.toLocaleString() }}</div>
        </div>
      </div>
      <p v-else class="text-slate-500 text-sm">Loading usage…</p>
    </section>

    <!-- Snapshots -->
    <section>
      <header class="flex items-baseline justify-between mb-3">
        <h2 class="text-sm font-extrabold uppercase tracking-widest text-slate-500">
          Recent snapshots
        </h2>
        <button
          type="button"
          class="text-xs font-bold px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 active:scale-95 transition-all min-h-[2.25rem] focus:outline-none focus-visible:ring-2 focus-visible:ring-pi-green"
          @click="refreshSnapshots(20)"
        >
          Refresh
        </button>
      </header>

      <ol
        v-if="snapshots.length"
        class="rounded-xl border border-slate-800 bg-slate-900/40 divide-y divide-slate-800 overflow-hidden"
      >
        <li
          v-for="snap in snapshots"
          :key="snap.id"
          class="p-4 flex justify-between items-center text-sm gap-3"
        >
          <div>
            <span class="font-mono text-xs text-slate-500">#{{ snap.id }}</span>
            <span class="ml-2 font-bold text-slate-200">
              {{ snap.label || '(no label)' }}
            </span>
          </div>
          <div class="text-right shrink-0">
            <div class="font-mono text-[0.7rem] text-slate-500">
              {{ new Date(snap.taken_at).toLocaleString() }}
            </div>
            <div class="text-xs text-slate-400">
              {{ snap.count }} sensor{{ snap.count === 1 ? '' : 's' }}
            </div>
          </div>
        </li>
      </ol>
      <p v-else class="text-slate-500 text-sm">
        No snapshots yet. Take one from the Sensors page.
      </p>
    </section>

    <!-- System logs -->
    <section>
      <header class="flex items-baseline justify-between mb-3">
        <h2 class="text-sm font-extrabold uppercase tracking-widest text-slate-500">
          Recent events
        </h2>
        <button
          type="button"
          class="text-xs font-bold px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 active:scale-95 transition-all min-h-[2.25rem] focus:outline-none focus-visible:ring-2 focus-visible:ring-pi-green"
          :disabled="loading"
          @click="refresh(50)"
        >
          {{ loading ? 'Refreshing…' : 'Refresh' }}
        </button>
      </header>

      <p v-if="error" class="text-pi-red-soft text-sm mb-3">
        Couldn’t load logs: {{ error }}
      </p>

      <div v-if="groupedByEvent.length" class="flex flex-wrap gap-2 mb-4">
        <span
          v-for="[event, count] in groupedByEvent"
          :key="event"
          class="font-mono text-xs px-2 py-1 rounded-md bg-slate-800/60 text-slate-300"
        >
          {{ event }} <span class="text-slate-500">×{{ count }}</span>
        </span>
      </div>

      <ol
        v-if="logs.length"
        class="rounded-xl border border-slate-800 bg-slate-900/40 divide-y divide-slate-800 overflow-hidden"
      >
        <li
          v-for="log in logs"
          :key="log.id"
          class="p-4 flex gap-3 items-start text-sm"
        >
          <span
            class="font-mono text-[0.7rem] font-bold uppercase px-2 py-0.5 rounded shrink-0"
            :class="levelClass(log.level)"
          >
            {{ log.level }}
          </span>
          <div class="min-w-0 flex-1">
            <div class="flex justify-between gap-3">
              <span class="font-bold text-slate-200">{{ log.event }}</span>
              <span class="font-mono text-[0.7rem] text-slate-500 shrink-0">
                {{ shortTime(log.ts) }}
              </span>
            </div>
            <div class="font-mono text-[0.7rem] text-slate-500 mt-1 truncate">
              {{ log.source }}<span v-if="Object.keys(log.detail).length"> · {{ detailSummary(log.detail) }}</span>
            </div>
          </div>
        </li>
      </ol>

      <p v-else-if="!loading" class="text-slate-500 text-sm">No events yet.</p>
    </section>
  </div>
</template>
