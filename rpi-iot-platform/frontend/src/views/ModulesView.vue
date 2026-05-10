<script setup lang="ts">
import { useRouter } from 'vue-router'
import ModuleTile from '../components/ModuleTile.vue'

const router = useRouter()

const modules = [
  {
    id: 'classroom-sensor-hub',
    title: 'Classroom Sensor Hub',
    description: 'Live readings from Micro:bit and ESP32 boards in your classroom, with AI explanations and snapshots.',
    badge: 'Live',
    disabled: false,
  },
  {
    id: 'weather-station',
    title: 'Weather Station',
    description: 'Outdoor temperature, humidity, and pressure tracked over weeks.',
    badge: 'Future',
    disabled: true,
  },
  {
    id: 'greenhouse-monitor',
    title: 'Greenhouse Monitor',
    description: 'Soil moisture, light levels, and watering alerts.',
    badge: 'Future',
    disabled: true,
  },
]

function open(moduleId: string): void {
  if (moduleId === 'classroom-sensor-hub') {
    /* The module's view is the home sensor grid — that's where its data
       lands. Future modules can route to dedicated views. */
    router.push('/')
  }
}
</script>

<template>
  <div class="p-6 max-w-6xl mx-auto">

    <p class="text-slate-400 text-sm mb-6 max-w-prose">
      Modules are self-contained classroom projects that plug into the
      platform. Each one brings its own sensors, dashboard tiles, and
      lesson plan.
    </p>

    <section class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <ModuleTile
        v-for="m in modules"
        :key="m.id"
        :title="m.title"
        :description="m.description"
        :badge="m.badge"
        :disabled="m.disabled"
        @open="open(m.id)"
      />
    </section>
  </div>
</template>
