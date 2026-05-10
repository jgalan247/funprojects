<script setup lang="ts">
import { computed } from 'vue'
import { useReadings } from './composables/useReadings'
import SensorCard from './components/SensorCard.vue'

const { readings, connected } = useReadings()

const sortedReadings = computed(() =>
  Array.from(readings.value.values()).sort((a, b) =>
    a.sensor_id.localeCompare(b.sensor_id),
  ),
)
</script>

<template>
  <main
    class="min-h-screen bg-slate-900 text-slate-100 px-6 py-8"
    style="background-image: radial-gradient(circle at 12% 8%, rgba(197, 26, 74, 0.07) 0%, transparent 35%), radial-gradient(circle at 88% 92%, rgba(117, 179, 67, 0.07) 0%, transparent 35%);"
  >
    <header class="flex items-center justify-between mb-8 max-w-6xl mx-auto">
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded-full bg-pi-red flex items-center justify-center text-white font-mono font-bold shadow-lg"
          aria-hidden="true"
        >
          Pi
        </div>
        <div>
          <h1 class="text-xl font-extrabold tracking-tight">Pi IoT Platform</h1>
          <p class="text-xs text-slate-400">Live sensor readings &middot; Phase&nbsp;3</p>
        </div>
      </div>
      <div
        class="font-mono text-[0.7rem] px-3 py-1 rounded-full font-bold uppercase tracking-wider"
        :class="
          connected
            ? 'bg-pi-green/20 text-pi-green-soft'
            : 'bg-pi-red/20 text-pi-red-soft'
        "
      >
        {{ connected ? 'connected' : 'disconnected' }}
      </div>
    </header>

    <section
      v-if="sortedReadings.length === 0"
      class="max-w-xl mx-auto text-center py-20 text-slate-400"
    >
      <p class="text-lg font-semibold mb-2">No sensor data yet.</p>
      <p class="text-sm">
        Run the test publisher from a laptop on the same Wi-Fi:
      </p>
      <pre
        class="font-mono text-xs bg-slate-800/80 border border-slate-700 rounded-lg px-4 py-3 inline-block mt-3 text-left text-slate-300"
      ><code>python3 scripts/publish-test-sensor.py \
  --host pi-iot-XX.local \
  --password &lt;your MQTT password&gt;</code></pre>
    </section>

    <section
      v-else
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 max-w-6xl mx-auto"
    >
      <SensorCard
        v-for="r in sortedReadings"
        :key="r.sensor_id"
        :reading="r"
      />
    </section>

    <footer class="text-center text-xs text-slate-600 mt-12">
      Coderra.je &middot; Pi IoT Academy
    </footer>
  </main>
</template>
