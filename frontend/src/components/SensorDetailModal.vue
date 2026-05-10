<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useReadings, type Reading } from '../composables/useReadings'
import LineChart, { type ChartPoint } from './LineChart.vue'

const props = defineProps<{ sensorId: string | null }>()
const emit = defineEmits<{ close: [] }>()

const { readings } = useReadings()

const history = ref<ChartPoint[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const sensor = computed<Reading | null>(() =>
  props.sensorId ? readings.value.get(props.sensorId) ?? null : null,
)

watch(
  () => props.sensorId,
  async (id) => {
    if (!id) {
      history.value = []
      return
    }
    loading.value = true
    error.value = null
    try {
      const res = await fetch(`/api/sensors/${encodeURIComponent(id)}/readings?limit=100`, {
        cache: 'no-store',
      })
      if (!res.ok) throw new Error(`${res.status}`)
      const rows = (await res.json()) as ChartPoint[]
      // API returns newest-first; chart wants chronological.
      history.value = rows.reverse()
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'unknown'
    } finally {
      loading.value = false
    }
  },
  { immediate: true },
)

/* When a fresh reading arrives for the open sensor, append it. */
watch(
  () => sensor.value,
  (r, prev) => {
    if (!r) return
    if (prev && r.ts === prev.ts) return
    history.value = [...history.value, { ts: r.ts, value: r.value }].slice(-200)
  },
  { deep: true },
)

const unitLabel = computed(() => {
  if (!sensor.value) return ''
  switch (sensor.value.unit) {
    case 'celsius': return '°C'
    case 'percent': return '%'
    case 'pascal': return 'Pa'
    default: return sensor.value.unit
  }
})

const accent = computed(() => {
  if (!sensor.value) return '#9bd06a'
  return sensor.value.metric === 'humidity' ? '#4ea1ff' : '#9bd06a'
})

function onBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) emit('close')
}
</script>

<template>
  <Transition>
    <div
      v-if="props.sensorId"
      class="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4"
      @click="onBackdropClick"
      role="dialog"
      aria-modal="true"
    >
      <div
        class="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col"
      >
        <header class="flex items-center justify-between p-5 border-b border-slate-800 shrink-0">
          <div class="min-w-0">
            <div class="font-mono text-[0.7rem] text-slate-500 uppercase tracking-widest truncate">
              {{ sensor?.device_id ?? '—' }}
            </div>
            <h2 class="text-2xl font-extrabold capitalize truncate">
              {{ sensor?.metric ?? props.sensorId }}
            </h2>
          </div>
          <button
            type="button"
            class="w-12 h-12 rounded-full bg-slate-800 hover:bg-slate-700 active:scale-95 transition-all flex items-center justify-center text-xl font-bold focus:outline-none focus-visible:ring-2 focus-visible:ring-pi-green"
            @click="emit('close')"
            aria-label="Close"
          >
            ×
          </button>
        </header>

        <section class="p-5 flex-1 overflow-y-auto">
          <div v-if="sensor" class="flex items-baseline gap-3 mb-4">
            <div class="text-5xl font-extrabold tabular-nums">
              {{ sensor.value.toFixed(sensor.metric === 'humidity' ? 0 : 1) }}
            </div>
            <div class="text-2xl font-semibold text-slate-400">{{ unitLabel }}</div>
            <div class="ml-auto font-mono text-xs text-slate-500">
              quality: {{ sensor.quality }}
            </div>
          </div>

          <div class="h-72">
            <p v-if="loading" class="text-slate-500 text-center py-12">Loading history…</p>
            <p v-else-if="error" class="text-pi-red-soft text-center py-12">
              Couldn’t load history: {{ error }}
            </p>
            <p v-else-if="history.length === 0" class="text-slate-500 text-center py-12">
              No readings yet.
            </p>
            <LineChart
              v-else
              :points="history"
              :unit="unitLabel"
              :color="accent"
            />
          </div>

          <p class="font-mono text-[0.7rem] text-slate-500 mt-4">
            <strong>{{ history.length }}</strong> readings shown · auto-updating
          </p>
        </section>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.v-enter-active,
.v-leave-active {
  transition: opacity 0.15s ease;
}
.v-enter-from,
.v-leave-to {
  opacity: 0;
}
</style>
