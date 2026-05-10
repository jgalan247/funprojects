<script setup lang="ts">
import { ref, computed } from 'vue'
import { useReadings } from '../composables/useReadings'
import SensorCard from '../components/SensorCard.vue'
import SensorDetailModal from '../components/SensorDetailModal.vue'

const { readings } = useReadings()

const sortedReadings = computed(() =>
  Array.from(readings.value.values()).sort((a, b) =>
    a.sensor_id.localeCompare(b.sensor_id),
  ),
)

const openSensorId = ref<string | null>(null)
</script>

<template>
  <div class="p-6 max-w-6xl mx-auto">

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
