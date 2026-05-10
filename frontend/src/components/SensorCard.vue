<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { Reading } from '../composables/useReadings'

const props = defineProps<{ reading: Reading }>()
defineEmits<{ open: [sensorId: string] }>()

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
    case 'celsius': return '°C'
    case 'percent': return '%'
    case 'pascal': return 'Pa'
    case 'lux': return 'lx'
    case 'metres-per-second': return 'm/s'
    case 'ppm': return 'ppm'
    default: return props.reading.unit
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
  if (m < 60) return `${m} min ago`
  const h = Math.floor(m / 60)
  return `${h} h ago`
}
</script>

<template>
  <button
    type="button"
    class="w-full text-left rounded-2xl border bg-slate-800/60 backdrop-blur p-5 transition-all min-h-[10rem] active:scale-[0.98] focus:outline-none focus-visible:ring-2 focus-visible:ring-pi-green"
    :class="isStale ? 'border-yellow-500/40' : 'border-slate-700 hover:border-slate-500'"
    @click="$emit('open', reading.sensor_id)"
    :aria-label="`Open ${reading.metric} from ${reading.device_id}`"
  >
    <div class="flex justify-between items-start mb-3 gap-3">
      <div class="min-w-0">
        <div class="font-mono text-[0.7rem] text-slate-500 uppercase tracking-widest truncate">
          {{ reading.device_id }}
        </div>
        <div class="text-lg font-bold text-slate-200 capitalize">
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

    <div class="text-5xl font-extrabold tabular-nums leading-none">
      {{ formattedValue }}<span class="text-xl font-semibold text-slate-400 ml-2">{{ unitLabel }}</span>
    </div>

    <div class="flex justify-between items-center mt-4 font-mono text-[0.75rem]">
      <span class="text-slate-500">{{ ageLabel(ageMs) }}</span>
      <span class="text-slate-600">tap for chart →</span>
    </div>
  </button>
</template>
