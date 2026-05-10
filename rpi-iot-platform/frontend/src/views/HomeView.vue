<script setup lang="ts">
import { ref, computed } from 'vue'
import { useReadings } from '../composables/useReadings'
import { useSnapshots } from '../composables/useSnapshots'
import SensorCard from '../components/SensorCard.vue'
import SensorDetailModal from '../components/SensorDetailModal.vue'

const { readings } = useReadings()
const { take } = useSnapshots()

const sortedReadings = computed(() =>
  Array.from(readings.value.values()).sort((a, b) =>
    a.sensor_id.localeCompare(b.sensor_id),
  ),
)

const openSensorId = ref<string | null>(null)

const snapshotting = ref(false)
const lastSnapshotMsg = ref<string | null>(null)
let snapshotMsgTimer: ReturnType<typeof setTimeout> | null = null

async function takeSnapshot() {
  if (snapshotting.value || sortedReadings.value.length === 0) return
  snapshotting.value = true
  lastSnapshotMsg.value = null
  try {
    const result = await take(null)
    lastSnapshotMsg.value = `Saved snapshot #${result.id} (${result.count} sensor${result.count === 1 ? '' : 's'})`
  } catch (e) {
    lastSnapshotMsg.value = `Couldn’t save: ${e instanceof Error ? e.message : 'unknown'}`
  } finally {
    snapshotting.value = false
    if (snapshotMsgTimer) clearTimeout(snapshotMsgTimer)
    snapshotMsgTimer = setTimeout(() => { lastSnapshotMsg.value = null }, 5000)
  }
}
</script>

<template>
  <div class="p-6 max-w-6xl mx-auto">

    <header
      v-if="sortedReadings.length"
      class="flex items-center justify-between gap-4 mb-5"
    >
      <p class="text-sm text-slate-400">
        {{ sortedReadings.length }} sensor{{ sortedReadings.length === 1 ? '' : 's' }} · live
      </p>
      <div class="flex items-center gap-3">
        <span
          v-if="lastSnapshotMsg"
          class="text-xs font-mono text-pi-green-soft"
          aria-live="polite"
        >
          {{ lastSnapshotMsg }}
        </span>
        <button
          type="button"
          class="min-h-[2.75rem] px-4 rounded-xl bg-pi-red text-white font-bold tracking-tight transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus-visible:ring-2 focus-visible:ring-pi-red"
          :disabled="snapshotting"
          @click="takeSnapshot"
        >
          {{ snapshotting ? 'Saving…' : 'Take snapshot' }}
        </button>
      </div>
    </header>

    <section
      v-if="sortedReadings.length === 0"
      class="text-center py-24 text-slate-400"
    >
      <p class="text-xl font-semibold mb-3">No sensor data yet.</p>
      <p class="text-sm mb-4">
        Run the test publisher from a laptop on the same Wi-Fi:
      </p>
      <pre
        class="font-mono text-xs bg-slate-800/80 border border-slate-700 rounded-lg px-4 py-3 inline-block text-left text-slate-300"
      ><code>python3 scripts/publish-test-sensor.py \
  --host pi-iot-XX.local \
  --password &lt;your MQTT password&gt;</code></pre>
    </section>

    <section
      v-else
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
    >
      <SensorCard
        v-for="r in sortedReadings"
        :key="r.sensor_id"
        :reading="r"
        @open="openSensorId = $event"
      />
    </section>

    <SensorDetailModal
      :sensor-id="openSensorId"
      @close="openSensorId = null"
    />
  </div>
</template>
