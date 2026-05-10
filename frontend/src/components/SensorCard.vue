<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Reading } from '../composables/useReadings'

const props = defineProps<{ reading: Reading }>()

const STALE_MS = 30_000

const now = ref(Date.now())
let timer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  timer = setInterval(() => { now.value = Date.now() }, 1000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})

const ageMs = computed(() => now.value - new Date(props.reading.received_at).getTime())
const isStale = computed(() => ageMs.value > STALE_MS)

const unitLabel = computed(() => {
  switch (props.reading.unit) {
    case 'celsius':
      return '°C'
    case 'percent':
      return '%'
    case 'pascal':
      return 'Pa'
    case 'lux':
      return 'lx'
    default:
      return props.reading.unit
  }
})

const formattedValue = computed(() => {
  const v = props.reading.value
  if (Number.isInteger(v)) return v.toString()
  return Math.abs(v) < 100 ? v.toFixed(1) : v.toFixed(0)
})

function ageLabel(ms: number): string {
  if (ms < 2000) return 'just now'
  const s = Math.floor(ms / 1000)
  if (s < 60) return `${s} s ago`
  const m = Math.floor(s / 60)
  return `${m} min ago`
}
</script>

<template>
  <article
    class="rounded-xl border bg-slate-800/60 backdrop-blur p-5 transition-colors"
    :class="isStale ? 'border-yellow-500/40' : 'border-slate-700'"
  >
    <div class="flex justify-between items-start mb-3">
      <div class="min-w-0">
        <div class="font-mono text-[0.7rem] text-slate-500 uppercase tracking-widest truncate">
          {{ reading.device_id }}
        </div>
        <div class="text-base font-bold text-slate-200 capitalize">
          {{ reading.metric }}
        </div>
      </div>
      <span
        v-if="isStale"
        class="shrink-0 text-[0.7rem] px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-300 font-bold uppercase tracking-wider"
      >
        stale
      </span>
    </div>

    <div class="text-4xl font-extrabold tabular-nums leading-none">
      {{ formattedValue }}
      <span class="text-base font-semibold text-slate-400 ml-1">{{ unitLabel }}</span>
    </div>

    <div class="font-mono text-[0.7rem] text-slate-500 mt-3">
      {{ ageLabel(ageMs) }}
    </div>
  </article>
</template>
